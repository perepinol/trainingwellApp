from datetime import date, datetime, timedelta
from io import BytesIO

from xhtml2pdf import pisa
from datetime import date, timedelta

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import Group
from django.http import HttpResponseForbidden, HttpResponse
from django.template.loader import get_template
from django.urls import reverse

from django import http
from django.conf import settings

from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.


from eventApp import query, decorators
from eventApp.forms import ReservationNameForm, DateForm, SeasonForm, SpaceForm
from django.views.generic import TemplateView, ListView
from eventApp.forms import SpaceForm
from django.views.generic import TemplateView

from eventApp import query, decorators, report
from eventApp.forms import ReservationNameForm, DateForm, SeasonForm, IncidenceForm, ReportForm
from eventApp.models import Reservation, Timeblock, Space, Notification, Incidence, User, Season, Invoice

import json
from functools import reduce
import logging

from eventApp.query import AlreadyExistsException

from datetime import datetime

logger = logging.getLogger(__name__)


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.passw_changed = True
            user.save()
            update_session_auth_hash(request, user)  # Important!
            return redirect(reverse('home'))
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {
        'form': form
    })


def notification_context_processor(request):
    return {
        'notifications': Notification.objects.filter(
            user=request.user,
            is_deleted=False
        )} if request.user.is_authenticated else {}


class TestView(TemplateView):
    template_name = 'eventApp/test.html'


class EventListView(TemplateView):
    template_name = 'eventApp/event_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        t = datetime.now().replace(minute=0, second=0, microsecond=0)
        curr_events = {
            'title': 'Current events',
            'start_time': t,
            'end_time': t + settings.RESERVATION_GRANULARITY,
            'events': Timeblock.objects.filter(start_time=t)
        }
        t += settings.RESERVATION_GRANULARITY
        coming_events = {
            'title': 'Coming events',
            'start_time': t,
            'end_time': t + settings.RESERVATION_GRANULARITY,
            'events': Timeblock.objects.filter(start_time=t)
        }
        context['event_agg'] = [curr_events, coming_events]
        return context


class EventView(TemplateView):
    template_name = 'eventApp/event_schedule_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_week = datetime.now() - timedelta(days=datetime.now().weekday())
        chosen_week = current_week
        if self.request.GET.get('week'):
            try:
                chosen_week = datetime.fromtimestamp(int(self.request.GET.get('week')))
                if chosen_week < current_week:
                    chosen_week = current_week
            except ValueError:
                pass  # Stick with current date

        # Week information for forwards and backwards navigation
        context['chosen_week'] = chosen_week
        context['weeks'] = {
            'chosen': chosen_week,
            'previous': chosen_week - timedelta(days=7),
            'next': chosen_week + timedelta(days=7)
        }
        if context['weeks']['previous'].date() < current_week.date():
            del context['weeks']['previous']

        # Current moment to disable previous events
        context['now'] = datetime.now()

        # Timetable data
        context['days'] = [chosen_week + timedelta(days=i) for i in range(7)]
        timetable = []
        for hour in Season.ongoing_season().open_hours():
            hour_events = [hour] + [
                query.get_all_timeblocks(d).filter(start_time__hour=hour.hour) for d in context['days']
            ]
            timetable.append(hour_events)
        context['timetable'] = timetable

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


@decorators.custom_login_required
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
            price=reduce(lambda agg, tb: agg + tb.space.price_per_hour * (1 - tb.space.offer/100), timeblocks, 0),
            user=request.user,
            modified_by=request.user,
            status=Reservation.UNPAID
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


@decorators.custom_login_required
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
        space_desc = {}
        for space in query.get_all_spaces():
            space_desc[str(space)] = space.description
        context = {'schedule': _get_schedule(), 'scheduleJSON': json.dumps(_get_schedule()),
                   'back': 'reservations', 'spaceDescrJSON': json.dumps(space_desc)}
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
            'price': reduce(lambda agg, tb: agg + tb.space.price_per_hour * (1- tb.space.offer/100), requested_timeblocks, 0)
        }
        return render(request, 'eventApp/reservation_confirmation.html', context)


def replace_space(timeblock, non_saved_reallocations):
    available_spaces = list(filter(
        lambda s:
            Timeblock.objects.filter(space=s, start_time=timeblock.start_time).count() == 0 and  # Space not busy in db
            len([nstb for nstb in non_saved_reallocations
                 if nstb.space == s and nstb.start_time == timeblock.start_time  # Space not busy in tb not saved
                 ]) == 0,
        Space.objects.filter(field=timeblock.space.field)
    ))
    if available_spaces:
        timeblock.space = available_spaces[0]
        return timeblock
    return None


def reallocate(tb_list):
    realloc, no_realloc = [], []
    for tb in tb_list:
        new_tb = replace_space(tb, non_saved_reallocations=realloc)
        if new_tb:
            realloc.append(new_tb)
        else:
            no_realloc.append(tb)
    return realloc, no_realloc


class IncidenceView(TemplateView):
    template_name = 'eventApp/incidence.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request):
        form = IncidenceForm(data=request.POST)
        if form.is_valid():
            incidence = form.save(commit=False)
            if form.cleaned_data['disable_fields']:
                # Reallocate affected timeblocks in reservation order
                reallocated_tb, non_reallocated_tb = reallocate(
                    Timeblock.objects.filter(
                        space__in=form.cleaned_data['affected_fields'],
                        start_time__lt=form.cleaned_data['limit'],
                        end_time__gte=datetime.now()
                    ).order_by('reservation__reservation_date')
                )
                if non_reallocated_tb:
                    # Create notification with reservations that could not be cancelled. Do not save
                    Notification.objects.create(
                        title='%s: incidence not created' % form.cleaned_data['name'],
                        content='\n'.join(['Could not reallocate reservations'] + [
                            '%s %s (%s)' % (tb.reservation.event_name, tb.start_time, tb.reservation.user)
                            for tb in non_reallocated_tb
                        ]),
                        user=request.user
                    )
                else:
                    # If all can be reallocated, do it and notify the organizer
                    for tb in reallocated_tb:
                        tb.save()
                        Notification.objects.create(
                            title='Reservation modified by incidence in a space',
                            content='Your reservation %s at %s has been moved to %s'
                                    % (tb.reservation.event_name, tb.start_time, tb.space),
                            user=tb.reservation.user
                        )
                    incidence.save()
            else:
                incidence.save()
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incidences'] = Incidence.objects.all()
        context['form'] = IncidenceForm()
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

    def get_day_all_spaces_free_(start_h, end_h, _spaces, _day):
        _today_sch = {}
        for _hour in range(get_int_hour(start_h), get_int_hour(end_h)):
            _hour_spaces = deepcopy(_spaces)
            for _incidence in incidences:
                if _incidence.limit > (datetime.combine(start_day+timedelta(days=_day), datetime.min.time()) + timedelta(hours=_hour)):
                    for _sp in _incidence.affected_fields.all():
                        del _hour_spaces[_sp.id]
            _today_sch[str(_hour)+':00'] = _hour_spaces
        return _today_sch

    schedule = {}
    spaces = {}
    incidences = query.get_all_incidences(limit=start_day+timedelta(days=num_days+1))

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
            schedule[str(start_day + timedelta(days=day))] = get_day_all_spaces_free_(open_season_hour, end_season_hour, spaces, day)
        else:
            schedule[str(start_day + timedelta(days=day))] = {}
            while open_season_hour + timedelta(hours=hour) < end_season_hour:
                current_hour = open_season_hour + timedelta(hours=hour)
                free_spaces_per_hour = deepcopy(spaces)
                for timeblock in today_timeblocks:
                    if timeblock.start_time.hour == get_int_hour(current_hour):
                        del free_spaces_per_hour[timeblock.space.id]
                for incidence in incidences:
                    if incidence.limit > (datetime.combine(start_day + timedelta(days=day), datetime.min.time()) + current_hour):
                        for sp in incidence.affected_fields.all():
                            del free_spaces_per_hour[sp.id]
                schedule[str(start_day + timedelta(days=day))][str(get_int_hour(current_hour))+':00'] = free_spaces_per_hour
                hour += 1

    return schedule


@decorators.get_if_creator(Reservation)
def reservation_detail(request, instance):
    tbck = Timeblock.objects.filter(reservation=instance)

    context = {'reservation': instance, 'timeblocks': aggregate_timeblocks(list(tbck))}
    return render(request, 'eventApp/reservation_detail.html', context)


@decorators.manager_only
def report_view(request):
    if request.method == 'GET':
        return render(request, 'eventApp/report_form.html', {'form': ReportForm()})

    if request.method == 'POST':
        rf = ReportForm(request.POST)
        if rf.is_valid():
            rep_json = report.generate_report(
                rf.cleaned_data['start_date'],
                rf.cleaned_data['end_date'],
                rf.cleaned_data['include']
            )
            charts = report.as_charts(rep_json)
            for chart in charts:  # To allow frontend to parse the content properly
                chart['chart'] = chart['chart'].replace('\\', '\\\\')

            return render(request, 'eventApp/report_view.html', {
                'charts': charts,
                'from': rf.cleaned_data['start_date'],
                'to': rf.cleaned_data['end_date']
            })
        else:
            return http.HttpResponseRedirect(request.get_raw_uri())  # Do not move


class ReservationStatusView(TemplateView):
    template_name = 'eventApp/manage_reservation.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request):
        _id = int(request.POST.get('id', "-1"))
        res = get_object_or_404(Reservation, id=_id)
        res.status = request.POST.get('status', "")
        res.save()
        context = self.get_context_data()
        context['reservation'] = res
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['res'] = query.get_all_reservations(status=['U', 'CTR'])
        return context


def cancelled_oot(reservation):
    return (reservation.timeblock_set.first().start_time - datetime.now()).days < 7


@decorators.get_if_creator(Reservation)
def delete_reservation(request, instance):
    def create_manager_notification(content):
        Notification.objects.create(title='Cancel Reserve', content=content, user=manager_user)

    if request.method != 'POST':
        return HttpResponseForbidden()

    group_id = Group.objects.get(name='manager')
    manager_user = User.objects.filter(groups=group_id).first()
    if not cancelled_oot(instance):
        instance.status = Reservation.CANCELTOREFUND if instance.status == Reservation.PAID else Reservation.CANCEL
        logger.info("Reservation " + str(instance.id) + " successfully canceled as " + instance.status)
        create_manager_notification("Reserve " + str(instance.id) + " was canceled. You should check if needs to be refunded")
    else:
        instance.status = Reservation.CANCELOUTTIME
        logger.info("Reservation " + str(instance.id) + " changed status to " + Reservation.CANCELOUTTIME)
        create_manager_notification("Reserve " + str(instance.id) + " canceled out of time.")
    instance.save()

    return redirect(reverse('reservations'))


class SeasonListView(TemplateView):
    template_name = 'eventApp/seasons.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        form = SeasonForm(data=request.POST)
        if form.is_valid():
            season = form.save(commit=True)
            logger.info("Created season: " + str(season.id) + ' ' + season.name)
            return http.HttpResponse()
        return http.HttpResponseBadRequest(list(form.errors.values()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seasons = Season.objects.filter(is_deleted=False)
        context['seasons'] = seasons
        context['form'] = SeasonForm()
        return context


class SpacesListView(TemplateView):
    template_name = 'eventApp/spaces.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        form = SpaceForm(data=request.POST)
        if form.is_valid():
            space = form.save(commit=False)
            space.price_per_hour = 0
            space.save()
            logger.info("Created space: " + str(space.id) )
            return http.HttpResponse()
        return http.HttpResponseBadRequest(list(form.errors.values()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spaces = Space.objects.filter(is_deleted=False)
        context['spaces'] = spaces
        context['form'] = SpaceForm()
        return context


class SpaceView(TemplateView):
    template_name = 'eventApp/space_detail.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        space = get_object_or_404(Space, id=self.kwargs.get('obj_id'))
        form = SpaceForm(data=request.POST, instance=space)
        if form.is_valid():
            form.save(commit=True)
            logger.info("Edited space: " + str(space.id))
            return http.HttpResponse()
        return http.HttpResponseBadRequest(list(form.errors.values()))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['s'] = get_object_or_404(Space, id=self.kwargs.get('obj_id'))
        context['form'] = SpaceForm(instance=context['s'])
        return context


class SpacePrice(TemplateView):
    template_name = 'eventApp/space_price.html'

    def post(self, request):
        _id = int(request.POST.get("id", "-1"))
        space = get_object_or_404(Space, id=_id)
        space.price_per_hour = int(request.POST.get('price', space.price_per_hour))
        space.offer = float(request.POST.get('offer', space.offer))
        space.save()
        logger.info("Changed price and/or offer of '"+str(space)+"' to "+str(space.price_per_hour)+"€/"+str(space.offer)+"%")
        return render(request, self.template_name, self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['spaces'] = query.get_all_spaces(hasPrice=False).order_by('field')
        return context


class SeasonView(TemplateView):
    template_name = 'eventApp/season_detail.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        season = get_object_or_404(Season, id=self.kwargs.get('obj_id'))
        form = SeasonForm(data=request.POST, instance=season)
        if form.is_valid():
            form.save(commit=True)
            logger.info("Edited season: " + str(season.id) + ' ' + season.name)
            return http.HttpResponse()
        return http.HttpResponseBadRequest(list(form.errors.values()))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['s'] = get_object_or_404(Season, id=self.kwargs.get('obj_id'))
        context['form'] = SeasonForm(instance=context['s'])
        return context


@decorators.custom_login_required
@decorators.facility_responsible_only
def delete_space(request, obj_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    space = get_object_or_404(Space, id=obj_id)
    space.soft_delete()
    logger.info("Deleted space: " + str(space.id))
    return redirect(reverse('spaces'))

  
@decorators.custom_login_required
@decorators.facility_responsible_only
def delete_season(request, obj_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    season = get_object_or_404(Season, id=obj_id)
    season.soft_delete()
    logger.info("Deleted season: " + str(season.id) + ' ' + season.name)
    return redirect(reverse('season'))

  
@decorators.custom_login_required
@decorators.ajax_required
@decorators.get_if_creator(Notification)
def _ajax_mark_as_read(request, instance):
    if instance.is_deleted:
        return http.HttpResponseNotModified()
    instance.soft_delete()
    return http.HttpResponse()


@decorators.custom_login_required
@decorators.facility_responsible_only
@decorators.ajax_required
def _ajax_mark_completed_incidence(request):
    ids_list = request.GET.getlist('ids[]')
    for id_ins in ids_list:
        Incidence.objects.get(id=id_ins).soft_delete()
    return http.JsonResponse({})

@decorators.custom_login_required
def reservation_bill(request, obj_id):
    reservation = get_object_or_404(Reservation, id=obj_id)
    if not Invoice.objects.filter(reservation=reservation).exists():
        set = Timeblock.objects.filter(reservation=obj_id)
        invoice = Invoice.objects.create(
            reservation=reservation,
        )
        for timeblock in set:
            invoice.timeblocks.append(timeblock)
    else:
        invoice = get_object_or_404(Invoice, reservation=reservation)

    context = {'invoice': invoice}

    return render(request, 'eventApp/reservation_bill.html', context)


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

