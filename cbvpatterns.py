from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.views.generic import View
from functools import partial

import django
DJANGO_VERSION = django.VERSION

if DJANGO_VERSION <= (1, 9, 0, 'final', 0):
    raise ImproperlyConfigured(
        'cbvpatterns can be used only when using Django >= 1.10. Please consider upgrading your Django version'
    )

if DJANGO_VERSION < (2, 0, 0, 'final', 0):
    from django.core.urlresolvers import RegexURLPattern as URLPattern, RegexURLResolver as URLResolver, get_callable
else:
    from django.urls.resolvers import URLPattern, URLResolver, RegexPattern, RoutePattern, get_callable


class CBVURLPattern(URLPattern):
    _callback_processed = None

    def __init__(self, regex, callback, default_args=None, name=None):
        super(CBVURLPattern, self).__init__(regex, callback, default_args, name)
        if isinstance(self.callback, type) and issubclass(self.callback, View):
            self.callback = callback.as_view()


# For Django 1.10 and 1.11
def url(regex, view, kwargs=None, name=None, prefix=''):
    if DJANGO_VERSION >= (2, 0, 0, 'final', 0):
        raise ImportError(
            'cbvpatterns.url can only be call when using Django < 2.0'
        )
    """As url() in Django."""
    if isinstance(view, (list, tuple)):
        # For include(...) processing.
        urlconf_module, app_name, namespace = view
        return URLResolver(regex, urlconf_module, kwargs, app_name=app_name, namespace=namespace)
    else:
        if isinstance(view, six.string_types):
            if not view:
                raise ImproperlyConfigured('Empty URL pattern view name not permitted (for pattern %r)' % regex)
            if prefix:
                view = prefix + '.' + view

            view = get_callable(view)
        return CBVURLPattern(regex, view, kwargs, name)


# For Django >= 2.0
def _path(route, view, kwargs=None, name=None, Pattern=None):
    if DJANGO_VERSION < (2, 0, 0, 'final', 0):
        raise ImportError(
            'cbvpatterns.path and cbvpatterns.re_path can only be call when using Django >= 2.0'
        )

    if isinstance(view, (list, tuple)):
        # For include(...) processing.
        pattern = Pattern(route, is_endpoint=False)
        urlconf_module, app_name, namespace = view
        return URLResolver(
            pattern,
            urlconf_module,
            kwargs,
            app_name=app_name,
            namespace=namespace,
        )
    else:
        if isinstance(view, six.string_types):
            view = get_callable(view)
            pattern = Pattern(route, name=name, is_endpoint=True)
            return CBVURLPattern(pattern, view, kwargs, name)
        else:
            raise TypeError('view must be a callable or a list/tuple in the case of include().')


try:
    RoutePattern = RoutePattern
    RegexPattern = RegexPattern
except NameError:
    RoutePattern = object
    RegexPattern = object

path = partial(_path, Pattern=RoutePattern)
re_path = partial(_path, Pattern=RegexPattern)

