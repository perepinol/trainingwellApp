from datetime import date, datetime, timedelta
from urllib.parse import parse_qs
from django.utils import timezone

from bootstrap_datepicker_plus import DatePickerInput
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView

from eventApp import query, decorators
from eventApp.forms import ReservationNameForm, DateForm
from eventApp.models import Reservation, Timeblock, User

import json
from functools import reduce
import logging

logger = logging.getLogger(__name__)


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


def prova_view(request):
    logger.info("SOC EL REI")
    return http.HttpResponse("HOLA")


def generate_timeblocks(post_data):
    timeblocks = []
    for timestamp in sorted(post_data.keys()):
        if timestamp == 'user':
            continue
        for space_id in sorted(post_data[timestamp]):
            timestamp = int(timestamp)
            tb = Timeblock(
                space_id=space_id,
                start_time=datetime.fromtimestamp(timestamp).astimezone(timezone.utc)
            )
            timeblocks.append(tb)
    return timeblocks


@login_required()
def reservation_view(request):
    if request.method == 'POST':
        res_name_form = ReservationNameForm(request.POST)
        if 'timeblocks' not in request.session or not res_name_form.is_valid():
            return http.HttpResponseBadRequest()

        # Make timeblocks. No need to check format because it has been checked before
        timeblocks = generate_timeblocks(request.session['timeblocks'])

        price = reduce(lambda agg, tb: agg + tb.space.price_per_hour, timeblocks, 0)

        # Create reservation object
        res = Reservation.objects.create(
            event_name=res_name_form.cleaned_data['event_name'],
            price=price,
            organizer=request.user,
            modified_by=request.user
        )

        # Add price to reservation and save
        logger.info("Created new reservation (id: %d, user: %s)" % (res.id, res.organizer))

        # Save timeblocks
        for timeblock in timeblocks:
            timeblock.reservation = res
            timeblock.save()

    return render(request, 'eventApp/reservation_list_view.html', {
        'res_list': Reservation.objects.filter(organizer=request.user, is_deleted=False)
    })


def aggregate_timeblocks(timeblocks):
    """{
        'start_time',
        'end_time',
        'space'
    }"""
    agg_list = []
    agg = {}
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
def show_reservation_schedule_view(request):
    if request.method == 'GET':
        # TODO: check request user
        # Remove session if available
        if 'timeblocks' in request.session:
            del request.session['timeblocks']

        context = {'schedule': _get_schedule(), 'scheduleJSON': json.dumps(_get_schedule()),
                   'back': 'reservations', 'user': request.user.id}
        return render(request, 'eventApp/reservation_schedule_view.html', context)

    else:
        # Get JSON and process timeblocks
        tb_json = json.loads(request.POST['reservations'])
        try:
            requested_timeblocks = generate_timeblocks(tb_json)
        except:  # Means that timeblocks had faulty format
            return http.HttpResponseBadRequest("Bad body format")

        request.session['timeblocks'] = tb_json  # So that we have the data in next view
        context = {
            'form': ReservationNameForm(),
            'timeblocks': aggregate_timeblocks(requested_timeblocks),
            'price': reduce(lambda agg, tb: agg + tb.space.price_per_hour, requested_timeblocks, 0)
        }
        return render(request, 'eventApp/reservation_confirmation.html', context)


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

    # TODO: if no existing spaces

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
