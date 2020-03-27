from datetime import date, time, datetime, timedelta
from urllib.parse import parse_qs

from bootstrap_datepicker_plus import DatePickerInput
from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Create your views here.
from django.views.generic import TemplateView, ListView

from eventApp import query
from eventApp.forms import ReservationForm, DateForm
from eventApp.models import Reservation, Field

import json


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


@login_required()
def create_reservation_view(request):
    if request.method == 'POST':
        # TODO: process POST and redirect to timetable view with name, date and activity in context
        return http.HttpResponseRedirect('/events')

    return render(request, 'eventApp/form.html', {'form': ReservationForm(), 'back': '/events/reservation'})


@login_required()
def show_reservation_schedule_view(request):
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
