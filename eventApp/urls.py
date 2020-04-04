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
from django.urls import path

from eventApp.views import TestView, EventView, ReservationView, show_reservation_schedule_view

urlpatterns = [
    path('reservation/', login_required(ReservationView.as_view()), name="reservations"),
    path('reservation/new', show_reservation_schedule_view, name="schedule_view"),
    path('reservation/<int:id>/', TestView.as_view(), name='reservation_detail'),
    path('', TestView.as_view(), name='home')
]
