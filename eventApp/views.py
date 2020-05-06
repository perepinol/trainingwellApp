from datetime import date, datetime, timedelta
from urllib.parse import parse_qs

from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden
from django.urls import reverse

from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from django.views.generic import TemplateView

from eventApp import query, decorators
from eventApp.forms import ReservationNameForm, DateForm

from eventApp.models import Reservation, Timeblock, Space, Notification, Incidence, User

import json
from functools import reduce
import logging

from eventApp.query import AlreadyExistsException

from datetime import datetime

logger = logging.getLogger(__name__)


def notification_context_processor(request):
    return {
        'notifications': Notification.objects.filter(
            user=request.user,
            is_deleted=False
        )} if request.user.is_authenticated else {}


class TestView(TemplateView):
    template_name = 'eventApp/test.html'


class EventView(TemplateView):
    template_name = 'eventApp/reservation_list_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        chosen_date = date.today()
        query_string = parse_qs(self.request.GET.urlencode())
        if 'chosen_date' in query_string and len(query_string['chosen_date']) == 1:
            try:
                chosen_date = datetime.strptime(query_string['chosen_date'][0], "%d-%m-%Y").date()
                if chosen_date < date.today():
                    chosen_date = date.today()
            except ValueError:
                pass  # Stick with current date

        context['form'] = DateForm(chosen_date=chosen_date)
        context['event_list'] = Reservation.objects.filter(event_date__exact=chosen_date)
        return context


def generate_timeblocks(post_data):
    """
    Create partial Timeblock objects (missing reservation) and return them, or raise exception if not valid.

    :param post_data: A JSON object with timestamps as keys and lists of space ids as values.
    :return: A list of Timeblocks without reservation.
    :raises:
        ValueError: If JSON is not correctly formatted.
        Space.DoesNotExist: If a space id is not in the database.
        AlreadyExistsException: If an identical Timeblock (except for its Reservation) is in the database.
    """
    if not post_data:
        raise ValueError()  # As if JSON verification failed

    timeblocks = []
    for timestamp in sorted(post_data.keys()):
        for space_id in sorted(post_data[timestamp]):
            timestamp = int(timestamp)  # May throw ValueError
            tb = Timeblock(
                space_id=space_id,
                start_time=datetime.fromtimestamp(timestamp)
            )
            if not Space.objects.filter(id=space_id).count():
                raise Space.DoesNotExist()
            if Timeblock.objects.filter(space_id=tb.space_id, start_time=tb.start_time).count():
                raise AlreadyExistsException()
            timeblocks.append(tb)
    return timeblocks


@login_required()
@decorators.organizer_responsible_only
def reservation_view(request):
    """
    Render the user's reservation list.

    If method is POST, also create reservation from JSON body.
    """
    if request.method == 'POST':
        res_name_form = ReservationNameForm(request.POST)
        if 'timeblocks' not in request.session or not res_name_form.is_valid():
            return http.HttpResponseBadRequest()

        # Make timeblocks. No need to check format because it has been checked before
        try:
            timeblocks = generate_timeblocks(request.session['timeblocks'])
        except AlreadyExistsException:
            return render(request, 'concurrency_error.html', {'redirect': reverse('schedule_view')})

        # Create reservation object
        res = Reservation.objects.create(
            event_name=res_name_form.cleaned_data['event_name'],
            price=reduce(lambda agg, tb: agg + tb.space.price_per_hour, timeblocks, 0),
            user=request.user,
            modified_by=request.user
        )
        logger.info("Created new reservation (id: %d, user: %s)" % (res.id, res.user))

        # Save timeblocks
        for timeblock in timeblocks:
            timeblock.reservation = res
            timeblock.save()
            logger.info("Created new timeblock (id: %d)" % timeblock.id)
        return http.HttpResponseRedirect(reverse('reservations'))

    return render(request, 'eventApp/reservation_list_view.html', {
        'res_list': sorted(
            Reservation.objects.filter(user=request.user, is_deleted=False),
            key=lambda r: r.timeblock_set.first().start_time
        )
    })


def aggregate_timeblocks(timeblocks):
    """
    Aggregate Timeblocks into a list of objects summarizing the input.

    :param timeblocks: A list of Timeblocks.
    :return: A list of objects of the form:
        {
            'start_time',
            'end_time',
            'space'
        }
    Where consecutive Timeblocks with the same space are squashed into one object.
    """
    agg_list = []
    agg = {}
    timeblocks.sort(key=lambda tb: tb.space.id)
    for timeblock in timeblocks:
        if len(agg.keys()) != 0:
            # If timeblocks are consecutive, just extend end_time
            if str(timeblock.space) == agg['space'] and timeblock.start_time == agg['end_time']:
                agg['end_time'] = agg['end_time'] + settings.RESERVATION_GRANULARITY
                continue

            # Else, add previous agg to list and store current one
            agg_list.append(agg)

        # Store current agg
        agg = {
            'start_time': timeblock.start_time,
            'end_time': timeblock.start_time + settings.RESERVATION_GRANULARITY,
            'space': str(timeblock.space)
        }

    if len(agg.keys()) != 0:
        agg_list.append(agg)  # Store last agg
    return agg_list


@login_required()
@decorators.organizer_responsible_only
def show_reservation_schedule_view(request):
    """
    Show the different views in the reservation process.

    If GET, return the reservation timetable.
    If POST, check the input's correctness and show the reservation confirmation page.
    """
    if request.method == 'GET':
        # Remove session if available
        if 'timeblocks' in request.session:
            del request.session['timeblocks']
        context = {'schedule': _get_schedule(), 'scheduleJSON': json.dumps(_get_schedule()),
                   'back': 'reservations'}
        return render(request, 'eventApp/reservation_schedule_view.html', context)

    else:
        # Get JSON and process timeblocks
        tb_json = json.loads(request.POST['reservations'])
        try:
            requested_timeblocks = generate_timeblocks(tb_json)
        except ValueError:  # Means that timeblocks had faulty format
            return http.HttpResponseBadRequest("Bad body format")
        except Space.DoesNotExist:
            return http.HttpResponseBadRequest("Invalid space id")
        except AlreadyExistsException:
            return render(request, 'concurrency_error.html', {'redirect': request.get_full_path()})

        request.session['timeblocks'] = tb_json  # So that we have the data in next view
        context = {
            'form': ReservationNameForm(),
            'timeblocks': aggregate_timeblocks(requested_timeblocks),
            'price': reduce(lambda agg, tb: agg + tb.space.price_per_hour, requested_timeblocks, 0)
        }
        return render(request, 'eventApp/reservation_confirmation.html', context)


class IncidenceView(TemplateView):
    template_name = 'eventApp/incidence.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incidences = Incidence.objects.all()
        '''for inc in Incidence.objects.all():
            incidencesJSON[inc.id] = {'name': inc.name,
                                      'content': inc.content,
                                      'deadline': inc.limit.strftime('%d/%m/%Y-%H:%M'),
                                      'fields': [str(field) for field in inc.affected_fields.all()],
                                      'disabled': inc.disable_fields,
                                      'deleted': inc.is_deleted,
                                      'date_created': inc.created_at.strftime('%d/%m/%Y-%H:%M')}'''
        context['incidences'] = incidences
        return context


@decorators.ajax_required
def _ajax_change_view(request):
    start_day = date(year=int(request.GET.get('year', 2020)),
                     month=int(request.GET.get('month', 1)),
                     day=int(request.GET.get('day', 1)))
    return http.JsonResponse(_get_schedule(start_day=start_day))


def _get_schedule(start_day=date.today()+timedelta(days=1), num_days=6):
    """Gets the schedule for one week from the specified day as a parameter (inclusive).
    Should no parameter given, 'tomorrow' is used as default and schedule for a week time.

    :param start_day: first day of the schedule desired.
    :param num_days: day count from now to include in the schedule, exclusive.
    :return: dictionary in JSON format of 1-week schedule { "day1": {"9h": [free spaces], ... }, ... }
    """
    from copy import deepcopy

    def get_int_hour(_timedelta):
        return int(_timedelta.seconds/3600)

    def get_day_all_spaces_free_(start_h, end_h, _spaces):
        _today_sch = {}
        for _hour in range(get_int_hour(start_h), get_int_hour(end_h)):
            _today_sch[str(_hour)+':00'] = _spaces
        return _today_sch

    schedule = {}
    spaces = {}

    open_season_hour = None
    end_season_hour = None

    for space in query.get_all_spaces():
        if space.is_available_in_season():
            spaces[space.id] = str(space)
            if not (open_season_hour and end_season_hour):
                open_season_hour = timedelta(hours=space.get_season_open_hour())
                end_season_hour = timedelta(hours=space.get_season_close_hour())

    if not spaces:
        raise RuntimeError("No spaces in database")

    timeblocks_qs = query.get_all_timeblocks(start_day, num_days=num_days)

    for day in range(0, num_days):
        hour = 0
        today_timeblocks = []
        for timeblock in timeblocks_qs:
            _date = start_day + timedelta(days=day)
            if timeblock.start_time.day == _date.day and \
                    timeblock.start_time.month == _date.month and \
                    timeblock.start_time.year == _date.year:
                today_timeblocks.append(timeblock)
        if not today_timeblocks:
            schedule[str(start_day + timedelta(days=day))] = get_day_all_spaces_free_(open_season_hour, end_season_hour, spaces)
        else:
            schedule[str(start_day + timedelta(days=day))] = {}
            while open_season_hour + timedelta(hours=hour) < end_season_hour:
                current_hour = open_season_hour + timedelta(hours=hour)
                free_spaces_per_hour = deepcopy(spaces)
                for timeblock in today_timeblocks:
                    if timeblock.start_time.hour == get_int_hour(current_hour):
                        del free_spaces_per_hour[timeblock.space.id]
                schedule[str(start_day + timedelta(days=day))][str(get_int_hour(current_hour))+':00'] = free_spaces_per_hour
                hour += 1

    return schedule


@login_required()
@decorators.organizer_responsible_only
def reservation_detail(request, id):
    res = get_object_or_404(Reservation, pk=id)
    tbck = Timeblock.objects.filter(reservation=id)

    context = {'reservation': res, 'timeblocks': aggregate_timeblocks(tbck)}
    if res.organizer != request.user:
        return http.HttpResponseForbidden()
    return render(request, 'eventApp/reservation_detail.html', context)


@login_required()
@decorators.organizer_responsible_only
def delete_reservation(request, pk):
    group_id = Group.objects.get(name='manager')
    manager_user = User.objects.filter(groups=group_id).first()

    def create_manager_notification(content):
        Notification.objects.create(title='Cancel Reserve', content=content, user=manager_user)

    item = Reservation.objects.get(id=pk)
    if request.user == item.user:
        request_date = datetime.now()
        days = (item.timeblock_set.first().start_time - request_date).days
        if days >= 7:
            item.status = Reservation.CANCELTOREFUND if item.status == Reservation.PAID else Reservation.CANCEL
            logger.info("Reservation " + str(item.id) + " successfully canceled as " + item.status)
            create_manager_notification("Reserve " + str(item.id) + " was canceled. You should check if needs to be refunded")
        else:
            item.status = Reservation.CANCELOUTTIME
            logger.info("Reservation " + item.id + " changed status to " + Reservation.CANCELOUTTIME)
            create_manager_notification("Reserve " + str(item.id) + " canceled out of time.")
        item.save()
    else:
        return HttpResponseForbidden()
    return redirect('/events/reservation')

  
@login_required()
@decorators.ajax_required
@decorators.get_if_creator(Notification)
def _ajax_mark_as_read(request, instance):
    if instance.is_deleted:
        return http.HttpResponseNotModified()
    instance.soft_delete()
    return http.HttpResponse()

  
@login_required()
@decorators.facility_responsible_only
@decorators.ajax_required
def _ajax_mark_completed_incidence(request):
    ids_list = request.GET.getlist('ids[]')
    for id_ins in ids_list:
        Incidence.objects.get(id=id_ins).soft_delete()
    return http.JsonResponse({})

