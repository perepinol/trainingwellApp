from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='multiply')
def multiply(value, arg):
    return round(value * arg,2)


@register.filter(name='apply_discount')
def apply_discount(price, discount):
    result = price-(price*discount)
    return round(result)