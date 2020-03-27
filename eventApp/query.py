from eventApp.models import *


def get_all_reservations(user=None, date_filter=None, field=None, space=None):
    """Returns a QuerySet with the models Reservation which meets the parameter conditions. Returns all the Reservations if no parameter is profided.

    :param user: User whose reservations is owner
    :param date_filter: Date which reservations are assigned
    :param field: Field where the reservations are associated.
    :param space: Field space where the reservations are performed. Note: if 'field' and 'space' are provided it will omit 'space'
    :return: a QuerySet of Reservation model
    """

    space_queryset = get_all_spaces_in_field(field=space.field if space else field)
    reservation_queryset = Reservation.objects.filter(space__in=space_queryset)
    if date_filter: reservation_queryset.filter(event_date=date_filter)
    if user: reservation_queryset.filter(organizer=user)
    return reservation_queryset


def get_all_spaces_in_field(field=None):
    """Returns a QuerySet of Space. If no filter parameters are provided it will return the whole model table.

    :param field: Field of the desired Spaces
    :return: a QuerySet of Space model
    """
    return Space.objects.filter(field=field) if field else Space.objects.all()
