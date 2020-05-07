from bootstrap_datepicker_plus import DatePickerInput
from django.forms import ModelForm, ModelChoiceField, Form, DateField
from datetime import date

from eventApp.models import Reservation, Space, Season


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
            'defaultDate': self.chosen_date.date().strftime('%Y-%m-%d'),
            'showClear': False
        })

    chosen_date = DateField()

class SpaceForm(ModelForm):

    class Meta:
        model = Space
        fields = ['field', 'season', 'price_per_hour', 'sqmt', 'photo',
                  'description','offer', 'last_update']

class SeasonForm(ModelForm):

    class Meta:
        model = Season
        fields = ['name','start_date','end_date','open_time',
                  'close_time','last_update']