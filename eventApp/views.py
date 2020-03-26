from datetime import date, datetime
from urllib.parse import parse_qs

from bootstrap_datepicker_plus import DatePickerInput
from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Create your views here.
from django.views.generic import TemplateView, ListView

from eventApp.forms import ReservationForm, DateForm
from eventApp.models import Reservation


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
