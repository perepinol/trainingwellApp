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
from eventApp.models import Reservation, Space

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


# @login_required()
def show_reservation_schedule_view(request):
    # TODO: check request user
    schedule = _get_schedule()
    return render(request, 'eventApp/reservation_schedule_view.html', schedule)


def _get_schedule(start_day=date.today(), num_days=7):
    """Gets the schedule for one week from the specified day as a parameter (inclusive).
    Should no parameter given, 'today' is used as default and schedule for a week time.

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
                open_season_hour = timedelta(hours=space.season.open_time.hour)
                end_season_hour = timedelta(hours=space.season.close_time.hour)

    # TODO: if no existing spaces

    timeblocks_qs = query.get_all_timeblocks(start_day, num_days=num_days)

    for day in range(0, num_days):
        hour = 0
        today_timeblocks = []
        for timeblock in timeblocks_qs:
            if timeblock.start_time.day == start_day.day + day:
                today_timeblocks.append(timeblock)
        if not today_timeblocks:
            schedule[str(start_day.day + day)] = get_day_all_spaces_free_(open_season_hour, end_season_hour, spaces)
        else:
            schedule[str(start_day.day + day)] = {}
            while open_season_hour + timedelta(hours=hour) < end_season_hour:
                current_hour = open_season_hour + timedelta(hours=hour)
                free_spaces_per_hour = deepcopy(spaces)
                for timeblock in today_timeblocks:
                    if timeblock.start_time.hour == get_int_hour(current_hour):
                        del free_spaces_per_hour[timeblock.space.id]
                schedule[str(start_day.day + day)][str(get_int_hour(current_hour))+':00'] = free_spaces_per_hour
                hour += 1

    return schedule
