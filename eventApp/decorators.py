from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.template.defaulttags import register


def ajax_required(f):
    def wrap(request, *args, **kwargs):
            if not request.is_ajax():
                raise PermissionDenied
            return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def manager_only(f):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.groups.filter(name='manager').count() == 0:
            raise PermissionDenied
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def facility_responsible_only(f):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.groups.filter(name='facility').count() == 0:
            raise PermissionDenied
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


def get_if_creator(model, admin=False):
    def decorator(function):
        @wraps(function)
        def wrap(request, *args, **kwargs):
            if 'obj_id' not in kwargs:
                raise RuntimeError('"obj_id" not in arguments')
            target = get_object_or_404(model, pk=kwargs['obj_id'])
            del kwargs['obj_id']

            # TODO: If 'admin', check if user is one of the organisation's users that can see the model
            if target.user != request.user or admin:
                return HttpResponseForbidden()
            kwargs['instance'] = target
            return function(request, *args, **kwargs)
        return wrap
    return decorator


@register.filter
def lookup(lst, index):
    if index >= len(lst):
        return None
    return lst[index]
