from bootstrap_datepicker_plus import DatePickerInput
from django.forms import ModelForm, ModelChoiceField, Form, DateField
from datetime import date

from eventApp.models import Reservation


class ReservationNameForm(ModelForm):

    class Meta:
        model = Reservation
        fields = ['event_name']


class DateForm(Form):
    def __init__(self, *args, **kwargs):
        self.chosen_date = kwargs.pop('chosen_date') if 'chosen_date' in kwargs else date.today()
        super().__init__(*args, **kwargs)
        self.fields['chosen_date'].widget = DatePickerInput(options={
            'format': 'DD-MM-YYYY',
            'minDate': date.today().strftime('%Y-%m-%d'),
            'defaultDate': self.chosen_date.strftime('%Y-%m-%d'),
            'showClear': False
        })

    chosen_date = DateField()
