from datetime import timedelta

from chartjs.views.base import JSONResponseMixin
from chartjs.views.columns import BaseColumnsHighChartsView
from chartjs.views.lines import BaseLineChartView
from django.db.models import Count, Sum

from eventApp.models import Space, Reservation


def create_chart_json_view(title, datasets, data):
    class LineChartJSONView(BaseLineChartView):
        def __init__(self):
            super(LineChartJSONView, self).__init__()
            self.title = title
            self.yUnit = "%"

        def get_labels(self):
            return list(map(lambda row: row[0], data))

        def get_providers(self):
            return datasets

        def get_data(self):
            ret_val = []
            if not len(data):
                return []
            for i in range(1, len(data[0])):
                ret_val.append(list(map(lambda row: row[i], data)))
            return ret_val

    return LineChartJSONView


def generate_report(start_date, end_date, parts):
    result = {}
    if 'use' in parts:
        # Count number of usages of each space between start and end date
        counted_spaces = Space.objects.filter(
            timeblock__start_time__gte=start_date,
            timeblock__start_time__lte=end_date
        ).annotate(usage=Count('timeblock'))

        result['use'] = list(map(
            lambda space: [str(space), space.usage / count_open_hours(space, start_date, end_date) * 100],
            counted_spaces
        ))

        fill_with(result['use'], Space.objects.all(), 0, [0], mod=str)

    if 'incomeoutcome' in parts:
        # Aggregate all income by date (takes into account day of reservation)
        date_incomes = Reservation.objects.filter(
            reservation_date__gte=start_date,
            reservation_date__lte=end_date,
            is_paid=True
        )\
            .annotate(recalculated_price=Sum('timeblock__space__price_per_hour'))\
            .values('reservation_date', 'recalculated_price')

        result['incomeoutcome'] = list(map(
            lambda i_o: [
                i_o['reservation_date'].date().isoformat(),  # Date
                i_o['recalculated_price'],  # Income
                0,  # Expenses
                i_o['recalculated_price']  # Profit
            ],
            date_incomes
        ))

        fill_with(result['incomeoutcome'], days_between(start_date, end_date), 0, [0, 0, 0], mod=lambda d: d.isoformat())
        result['incomeoutcome'].sort()

    if 'performance' in parts:
        # Sum all prices of paid reservations in each space
        timeblock_counted_spaces = Space.objects.filter(
            timeblock__reservation__reservation_date__gte=start_date,
            timeblock__reservation__reservation_date__lte=end_date,
            timeblock__reservation__is_paid=True
        ).annotate(num_timeblocks=Count('timeblock'))

        result['performance'] = list(map(
            lambda s: [str(s), s.num_timeblocks * s.price_per_hour],
            timeblock_counted_spaces
        ))

        fill_with(result['performance'], Space.objects.all(), 0, [0], mod=str)
    print(result)
    return result


def as_charts(json_data):
    result = []
    if 'use' in json_data:
        chart = create_chart_json_view(
            title='Reservations of each space over number of reservation slots',
            datasets=['Usage (%)'],
            data=json_data['use']
        )()
        result.append({
            'title': 'Reservations of each space over number of reservation slots',
            'chart': JSONResponseMixin().convert_context_to_json(chart.get_context_data()),
            'max_val': 100
        })

    if 'incomeoutcome' in json_data:
        chart = create_chart_json_view(
            title='Reservations of each space over number of reservation slots',
            datasets=['Income', 'Outcome', 'Profit'],
            data=json_data['incomeoutcome']
        )()
        result.append({
            'title': 'Income/outcome over time',
            'chart': JSONResponseMixin().convert_context_to_json(chart.get_context_data()),
            'ylabel': '€'
        })

    if 'performance' in json_data:
        chart = create_chart_json_view(
            title='Performance of each space',
            datasets=['Performance (€)'],
            data=json_data['performance']
        )()

        result.append({
            'title': 'Performance of each space',
            'chart': JSONResponseMixin().convert_context_to_json(chart.get_context_data())
        })
    return result


def days_between(start_date, end_date):
    return map(lambda i: start_date + timedelta(days=i), range((end_date - start_date).days + 1))


def count_open_hours(space, start_date, end_date):
    hour_count = 0
    for day in days_between(start_date, end_date):
        if space.is_available_in_season(day):
            hour_count += len(space.current_season(day).open_hours())
    return hour_count if hour_count else 1


def fill_with(struct, items, position, value, mod=lambda x: x):
    for instance in items:
        if mod(instance) not in map(lambda row: row[position], struct):
            struct.append([mod(instance)] + value)
