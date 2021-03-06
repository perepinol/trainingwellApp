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


def get_all_spaces(field=None, hasPrice = True, only_active=True):
    """Returns a QuerySet of Space. If no filter parameters are provided it will return the whole model table.

    :param field: Field of the desired Spaces
    :param only_active: Mark if willing only active (non safe-deleted) or all.
    :return: a QuerySet of Space model
    """
    space_qs = Space.objects.filter(field=field) if field else Space.objects.all()
    if hasPrice: space_qs = space_qs.filter(price_per_hour__gt=0)
    return space_qs.filter(is_deleted=False) if only_active else space_qs


def get_all_reservations(status=None, only_active=True):
    reserv_qs = Reservation.objects.all()
    if status: reserv_qs = reserv_qs.filter(status__in=status)
    return reserv_qs.filter(is_deleted=False) if only_active else reserv_qs


def get_all_incidences(limit=None, only_disabling_fields=True, only_active=True):
    incidences = Incidence.objects.filter(limit__lte=limit) if limit else Incidence.objects.all()
    if only_disabling_fields: incidences = incidences.filter(disable_fields=True)
    return incidences.filter(is_deleted=False) if only_active else incidences
