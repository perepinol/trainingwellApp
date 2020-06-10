"""trainingwellApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import url
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]
urlpatterns += i18n_patterns(
    path('accounts/', include('django.contrib.auth.urls')),
    path('events/', include('eventApp.urls')),
    path('', RedirectView.as_view(url='/events')),
    prefix_default_language=True,
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
