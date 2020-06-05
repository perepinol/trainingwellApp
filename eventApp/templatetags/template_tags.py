from django import template
from django.shortcuts import get_object_or_404

from eventApp.models import Reservation

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='since_modified')
def created(reservation):
    from datetime import datetime
    return int((datetime.today() - reservation.last_update).total_seconds() / 3600.0)+1


@register.filter(name='multiply')
def multiply(value, arg):
    return round(value * arg,2)


@register.filter(name='apply_discount')
def apply_discount(price, discount):
    result = price-(price*discount/100)
    return round(result)