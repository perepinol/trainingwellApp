from bootstrap_datepicker_plus import DatePickerInput
from django.forms import ModelForm, ModelChoiceField, Form, DateField, DateTimeField, MultipleChoiceField, \
    SelectMultiple
from datetime import date, datetime, timedelta

from eventApp.models import Reservation, Season, Space, Incidence


class ReservationNameForm(ModelForm):

    class Meta:
        model = Reservation
        fields = ['event_name']


class ReportForm(Form):
    current_date = date.today()
    start_date = DateField(required=True)
    end_date = DateField(required=True)
    include = MultipleChoiceField(label=False, choices=[
        ("use", "Space usage"),  # TODO: internationalize
        ("incomeoutcome", "Income/outcome"),
        ("performance", "Performance")
    ])

    def __init__(self, *args, **kwargs):
        def monthstart(day):
            return date(day.year, day.month, 1)

        def monthend(day):
            d = date(day.year, day.month + 1, 1)
            return d - timedelta(days=1)

        def dp(day):
            return DatePickerInput(options={
                'format': 'DD-MM-YYYY',
                'defaultDate': day.strftime('%Y-%m-%d'),
                'maxDate': date.today().strftime('%Y-%m-%d'),
                'showClear': False
            })
        super().__init__(*args, **kwargs)
        prev_month = monthstart(monthstart(date.today()) - timedelta(days=1))
        self.fields['start_date'].widget = dp(prev_month)
        self.fields['end_date'].widget = dp(monthend(prev_month))
        self.sd = prev_month
        self.ed = monthend(prev_month)

    def is_valid(self):
        if not super().is_valid():
            return False
        sd, ed = self.cleaned_data['start_date'], self.cleaned_data['end_date']
        if sd > ed:
            return False
        return True


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


        
class IncidenceForm(ModelForm):
    class Meta:
        model = Incidence
        fields = ['name', 'content', 'limit', 'affected_fields', 'disable_fields']

    def __init__(self, *args, **kwargs):
        super(IncidenceForm, self).__init__(*args, **kwargs)
        self.fields['limit'].widget = DatePickerInput(options={
            'format': 'DD/MM/YYYY HH:mm',
            'showClear': False,
            'minDate': date.today().strftime('%Y-%m-%d'),
        })
        self.fields['limit'].input_formats = ['%d/%m/%Y %H:%M']

    def save(self, commit=True):
        incidence = super(IncidenceForm, self).save(commit=False)
        if commit:
            incidence.save()
        return incidence
