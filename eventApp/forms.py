from bootstrap_datepicker_plus import DatePickerInput
from django.forms import ModelForm, ChoiceField
from datetime import date

from eventApp.models import Reservation, Space


class ReservationForm(ModelForm):
    name = "New reservation"
    submit_name = "Go to timetable"
    space_type = ChoiceField(choices=Space.FIELD_OPTIONS)

    class Meta:
        model = Reservation
        fields = ['event_name', 'space_type', 'event_date']

        widgets = {
            'event_date': DatePickerInput(options={
                'format': 'DD-MM-YYYY',
                'minDate': date.today().strftime('%Y-%m-%d'),
                'defaultDate': date.today().strftime('%Y-%m-%d'),
                'showClear': False
            })
        }
