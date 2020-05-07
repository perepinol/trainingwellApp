from django.db.models import Count, Sum

from eventApp.models import *
from datetime import timedelta


class AlreadyExistsException(Exception):
    """Represents the situation where an object that already exists is being created (e.g. Timeblock overlap)."""
    pass


def get_all_timeblocks(start_date, num_days=1, space=None, field=None):
    """Returns a QuerySet with the models Timeblock which meets the parameter conditions.

    :param start_date: Mandatory. Date first day of the interval (inclusive) which timeblocks are assigned.
    :param num_days: Number of days from start day. Default 1 day (only  today).
    :param space: Field space where the timeblocks are performed. Note: if 'field' and 'space' are provided it will omit 'field'.
    :param field: Field where timeblock are assigned.
    :return: a QuerySet of Timeblocks model
    """
    space_qs = None
    if field or space:
        space_qs = get_all_spaces(field=space.field if space else field)
    timeblock_qs = Timeblock.objects.filter(start_time__day=start_date.day,
                                            start_time__month=start_date.month,
                                            start_time__year=start_date.year)
    for i in range(1, num_days):
        start_date += timedelta(days=1)
        timeblock_qs = timeblock_qs | Timeblock.objects.filter(start_time__day=start_date.day,
                                                               start_time__month=start_date.month,
                                                               start_time__year=start_date.year)
    if space_qs:
        timeblock_qs.filter(space__in=space_qs)
    return timeblock_qs


def get_all_spaces(field=None, only_active=True):
    """Returns a QuerySet of Space. If no filter parameters are provided it will return the whole model table.

    :param field: Field of the desired Spaces
    :param only_active: Mark if willing only active (non safe-deleted) or all.
    :return: a QuerySet of Space model
    """
    space_qs = Space.objects.filter(field=field) if field else Space.objects.all()
    return space_qs.filter(is_deleted=False) if only_active else space_qs


def generate_report(start_date, end_date, parts):
    result = {}
    if 'use' in parts:
        # Count number of usages of each space between start and end date
        counted_spaces = Space.objects.filter(
            timeblock__start_time__gte=start_date,
            timeblock__start_time__lte=end_date
        ).annotate(usage=Count('timeblock'))

        result['use'] = get_dict_from_iterator(map(
            lambda space: (str(space), space.usage / count_open_hours(space, start_date, end_date) * 100),
            counted_spaces
        ))

    if 'incomeoutcome' in parts:
        # Aggregate all income by date (takes into account day of reservation)
        date_incomes = Reservation.objects.filter(
            reservation_date__gte=start_date,
            reservation_date__lte=end_date,
            is_paid=True
        )\
            .annotate(recalculated_price=Sum('timeblock__space__price_per_hour'))\
            .values('reservation_date', 'recalculated_price')

        result['incomeoutcome'] = get_dict_from_iterator(map(
            lambda i_o: (i_o['reservation_date'].date().isoformat(), i_o['recalculated_price']),
            date_incomes
        ))

    if 'performance' in parts:
        # Sum all prices of paid reservations in each space
        timeblock_counted_spaces = Space.objects.filter(
            timeblock__reservation__reservation_date__gte=start_date,
            timeblock__reservation__reservation_date__lte=end_date,
            timeblock__reservation__is_paid=True
        ).annotate(num_timeblocks=Count('timeblock'))

        result['performance'] = get_dict_from_iterator(map(
            lambda s: (str(s), s.num_timeblocks * s.price_per_hour),
            timeblock_counted_spaces
        ))

    return result


def count_open_hours(space, start_date, end_date):
    hour_count = 0
    for day in map(lambda i: start_date + timedelta(days=i), range((end_date - start_date).days + 1)):
        if space.is_available_in_season(day):
            hour_count += len(space.current_season(day).open_hours())
    return hour_count


def get_dict_from_iterator(iterator):
    d = {}
    for elem, value in iterator:
        d[elem] = value
    return d
