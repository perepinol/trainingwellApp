from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Create your views here.
from django.views.generic import TemplateView

from eventApp.forms import ReservationForm


class TestView(TemplateView):
    template_name = 'eventApp/test.html'


@login_required()
def reservation_view(request):
    if request.method == 'POST':
        # TODO: process POST and redirect to timetable view with name, date and activity in context
        return http.HttpResponseRedirect('/events')

    return render(request, 'eventApp/form.html', {'form': ReservationForm()})
