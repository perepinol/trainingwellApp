from eventApp.models import *
from datetime import timedelta


def get_all_timeblocks_week(date_filter, space=None, field=None):
    """Returns a QuerySet with the models Timeblock which meets the parameter conditions.

    :param date_filter: Mandatory. Date first fay of the week (inclusive) which timeblocks are assigned.
    :param space: Field space where the timeblocks are performed. Note: if 'field' and 'space' are provided it will omit 'field'.
    :param field: Field where timeblock are assigned.
    :return: a QuerySet of Timeblocks model
    """
    space_qs = None
    if field or space:
        space_qs = get_all_spaces_in_field(field=space.field if space else field)
    timeblock_qs = Timeblock.objects.filter(start_time__day=date_filter.day,
                                            start_time__month=date_filter.month,
                                            start_time__year=date_filter.year)
    for i in range(1, 7):
        timeblock_qs = timeblock_qs | Timeblock.objects.filter(start_time__day=date_filter.day + i,
                                                               start_time__month=date_filter.month,
                                                               start_time__year=date_filter.year)
    if space_qs:
        timeblock_qs.filter(space__in=space_qs)
    return timeblock_qs


def get_all_spaces_in_field(field=None, only_active=True):
    """Returns a QuerySet of Space. If no filter parameters are provided it will return the whole model table.

    :param field: Field of the desired Spaces
    :param only_active: Mark if willing only active (non safe-deleted) or all.
    :return: a QuerySet of Space model
    """
    space_qs = Space.objects.filter(field=field) if field else Space.objects.all()
    return space_qs.filter(is_deleted=False) if only_active else space_qs
