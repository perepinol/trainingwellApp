from django.core.exceptions import PermissionDenied


def ajax_required(f):
    def wrap(request, *args, **kwargs):
            if not request.is_ajax():
                raise PermissionDenied
            return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap