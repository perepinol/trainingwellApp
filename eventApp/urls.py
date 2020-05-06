"""eventApp URL Configuration

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
from django.contrib.auth.decorators import login_required
from eventApp.decorators import facility_responsible_only
from django.urls import path

from eventApp.views import TestView, IncidenceView, reservation_view, show_reservation_schedule_view, _ajax_change_view, \
    reservation_detail, _ajax_mark_as_read, _ajax_mark_completed_incidence, delete_reservation

urlpatterns = [
    path('reservation/', reservation_view, name="reservations"),
    path('reservation/new', show_reservation_schedule_view, name="schedule_view"),
    path('reservation/<int:obj_id>/', reservation_detail, name='reservation_detail'),
    path('reservation/delete/<int:pk>/', delete_reservation, name='delete_reservation'),
    path('ajax/change_week/', _ajax_change_view, name='ajax_change_week'),
    path('ajax/mark_completed_incidence/', _ajax_mark_completed_incidence, name='ajax_completed'),
    path('notification/<int:obj_id>/', _ajax_mark_as_read, name='ajax_mark_read'),
    path('incidences/', facility_responsible_only(IncidenceView.as_view()), name="incidences"),
    path('', TestView.as_view(), name='home'),
]
