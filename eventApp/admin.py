from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from eventApp import models


class ProjectAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        instance = form.save(commit=False)
        instance.modified_by = request.user
        instance.save()
        return instance


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Space, ProjectAdmin)
admin.site.register(models.Reservation, ProjectAdmin)
admin.site.register(models.Field, ProjectAdmin)
