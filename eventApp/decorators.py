from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.defaulttags import register
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.urls import reverse

from eventApp.models import User


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


def custom_login_required(f):
    def wrap(request, *args, **kwargs):
        user = request.user
        path = request.build_absolute_uri()
        if not user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path, settings.LOGIN_URL, REDIRECT_FIELD_NAME)
        if not user.passw_changed:
            return redirect(reverse('change_password'))
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap


'''def custom_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    def decorator(f):
        @wraps(f)
        def wrap(request, *args, **kwargs):
            user = request.user
            path = request.build_absolute_uri()
            if not user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(path, settings.LOGIN_URL, REDIRECT_FIELD_NAME)
            return wrap
        return decorator'''


@register.filter
def lookup(lst, index):
    if index >= len(lst):
        return None
    return lst[index]


