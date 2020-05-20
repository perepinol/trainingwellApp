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
from eventApp.decorators import facility_responsible_only, manager_only
from django.urls import path

from eventApp.views import TestView, IncidenceView, SeasonListView, reservation_view, show_reservation_schedule_view, \
    _ajax_change_view, SpacePrice, \
    reservation_detail, _ajax_mark_as_read, _ajax_mark_completed_incidence, delete_reservation, EventView, \
    SpacesListView, SpaceView, delete_space, report_view, SeasonView, delete_season, ReservationStatusView
    

urlpatterns = [
    path('reservation/', reservation_view, name="reservations"),
    path('reservation/new', show_reservation_schedule_view, name="schedule_view"),
    path('reservation/<int:obj_id>/', reservation_detail, name='reservation_detail'),
    path('reservation/delete/<int:obj_id>/', delete_reservation, name='delete_reservation'),
    path('season/', facility_responsible_only(SeasonListView.as_view()), name='season'),
    path('season/<int:obj_id>', facility_responsible_only(SeasonView.as_view()), name='season_detail'),
    path('season/delete/<int:obj_id>', delete_season, name='season_delete'),
    path('space/', facility_responsible_only(SpacesListView.as_view()), name='spaces'),
    path('space/<int:obj_id>', facility_responsible_only(SpaceView.as_view()), name='space_detail'),
    path('space/delete/<int:obj_id>', delete_space, name='space_delete'),
    path('manage_reservations/', manager_only(ReservationStatusView.as_view()), name='reservation_status'),
    path('space/prices/', manager_only(SpacePrice.as_view()), name='space_price'),
    path('reservation/delete/<int:obj_id>/', delete_reservation, name='delete_reservation'),
    path('ajax/change_week/', _ajax_change_view, name='ajax_change_week'),
    path('ajax/mark_completed_incidence/', _ajax_mark_completed_incidence, name='ajax_completed'),
    path('notification/<int:obj_id>/', _ajax_mark_as_read, name='ajax_mark_read'),
    path('schedule', EventView.as_view(), name='event_schedule'),
    path('incidences/', facility_responsible_only(IncidenceView.as_view()), name="incidences"),
    path('report/', report_view, name="report"),
    path('', TestView.as_view(), name='home'),
]
