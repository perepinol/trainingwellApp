from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from eventApp import models

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Space)
admin.site.register(models.Reservation)
admin.site.register(models.Field)
