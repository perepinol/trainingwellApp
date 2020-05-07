from bootstrap_datepicker_plus import DatePickerInput
from django.forms import ModelForm, ModelChoiceField, Form, DateField
from datetime import date

from eventApp.models import Reservation, Season, Space


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


class SeasonForm(ModelForm):
    class Meta:
        model = Season
        fields = ['name', 'start_date', 'end_date', 'open_time', 'close_time']

    def __init__(self, *args, **kwargs):
        super(SeasonForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget = DatePickerInput(options={
            'format': 'DD/MM/YYYY',
            'showClear': False,
        })
        self.fields['start_date'].input_formats = ['%d/%m/%Y']
        self.fields['end_date'].widget = DatePickerInput(options={
            'format': 'DD/MM/YYYY',
            'showClear': False,
        })
        self.fields['end_date'].input_formats = ['%d/%m/%Y']
        self.fields['open_time'].widget = DatePickerInput(options={
            'format': 'HH:mm',
            'showClear': False,
        })
        self.fields['open_time'].input_formats = ['%H:%M']
        self.fields['close_time'].widget = DatePickerInput(options={
            'format': 'HH:mm',
            'showClear': False,
        })
        self.fields['close_time'].input_formats = ['%H:%M']

class SpaceForm(ModelForm):
    class Meta:
        model = Space
        fields = ['field', 'season', 'price_per_hour', 'sqmt', 'photo', 'description', 'offer']



