from datetime import date, time, datetime, timedelta
from urllib.parse import parse_qs

from bootstrap_datepicker_plus import DatePickerInput
from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
from django.views.generic import TemplateView, ListView

from eventApp import query
from eventApp.forms import ReservationNameForm, DateForm
from eventApp.models import Reservation, Field, Timeblock

import json
import logging

logger = logging.getLogger(__name__)


class TestView(TemplateView):
    template_name = 'eventApp/test.html'

class ReservationView(TemplateView):
    template_name = 'eventApp/reservation_list_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['res_list'] = Reservation.objects.filter(organizer=self.request.user, is_deleted=False)
        return context


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
    return HttpResponse("HOLA")

@login_required()
def create_reservation_view(request):
    if request.method == 'POST':
        # TODO: process POST and redirect to timetable view with name, date and activity in context
        return http.HttpResponseRedirect('/events')

    return render(request, 'eventApp/form.html', {'form': ReservationNameForm(), 'back': '/events/reservation'})


def aggregate_timeblocks(timeblocks):
    """{
        'start_time',
        'end_time',
        'space'
    }"""
    agg_list = []
    agg = {}
    for timeblock in timeblocks.order_by('space', 'start_time'):
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
        # TODO: get context from request
        # Temporal context simulation
        import random
        context = {
            'event': {
                'name': "Event Name",
                'date': date.today(),
                'num_spaces': 1,
                'space_type': random.choice(Field.objects.all())
            }
        }
        # ###################
        event_date = context['event']['date']
        event_field = context['event']['space_type']
        event_num_spaces = context['event']['num_spaces']

        spaces = query.get_all_spaces_in_field(field=event_field)
        reservations = query.get_all_reservations(date_filter=event_date, field=event_field)
        schedule = _get_schedule(spaces, reservations, event_num_spaces)

        context['event']['num_spaces'] = 1
        context['schedule'] = schedule

        return render(request, 'eventApp/reservation_schedule_view.html', context)

    else:
        requested_timeblocks = Timeblock.objects.all()  # TODO: get timeblocks from POST
        timeblock_sum = requested_timeblocks.aggregate(price=Sum('space__price_per_hour'))['price']
        context = {
            'form': ReservationNameForm(),
            'timeblocks': aggregate_timeblocks(Timeblock.objects.all()),
            'price': timeblock_sum if timeblock_sum is not None else 0
        }
        return render(request, 'eventApp/reservation_confirmation.html', context)


def _get_week_schedule():
    pass


def _get_schedule(spaces, reservations, num_desired_spaces):
    def get_int_hour(_timedelta):
        return int(_timedelta.seconds/3600)

    def space_available(_space, hour):
        if not (_space.available_since.hour <= hour < _space.available_until.hour): return False
        for reservation in list_reservations:
            if space == reservation[2] and hour_taken(reservation, hour):
                return False
        return True

    def hour_taken(_reservation, hour):
        return _reservation[0] <= hour < _reservation[1]

    schedule = {}
    first_available_hour = min(set(map(lambda _space: timedelta(hours=_space.available_since.hour), list(spaces))))
    last_available_hour = max(set(map(lambda _space: timedelta(hours=_space.available_until.hour-1), list(spaces))))

    list_reservations = [(r.starting_hour.hour, r.ending_hour.hour, r.space) for r in reservations]

    i = 0
    while first_available_hour + timedelta(hours=i) <= last_available_hour:
        current_hour = get_int_hour(first_available_hour)+i
        schedule[str(current_hour)] = {'hour_str': str(current_hour) + ':00', 'free': True, 'spaces': []}

        for space in spaces:
            if space_available(space, current_hour):
                schedule[str(current_hour)]['spaces'].append(str(space))
        if len(schedule[str(current_hour)]['spaces']) < num_desired_spaces:
            schedule[str(current_hour)]['free'] = False

        i += 1

    return schedule

def reservation_detail(request, id):
    reservation = Reservation.objects.get(id=id)
    return render(request, 'eventApp/reservation_detail.html', {'reservation': reservation})
    #return HttpResponse(id)
