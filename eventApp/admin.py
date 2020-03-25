from django.contrib import admin

# Register your models here.
from eventApp import models

admin.site.register(models.CustomUser)
admin.site.register(models.Space)
admin.site.register(models.Reservation)
admin.site.register(models.Field)
