from bootstrap_datepicker_plus import DatePickerInput
from django.forms import ModelForm, ModelChoiceField, Form, DateField, DateTimeField, MultipleChoiceField, \
    SelectMultiple
from datetime import date, datetime, timedelta

from eventApp.models import Reservation


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
