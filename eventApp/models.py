from datetime import date

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    is_adult = models.BooleanField(default=False)
    last_update = models.DateField()
    modified_by = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.username

    def save(self, *args, **kwargs):
        self.last_update = date.today()
        super(User, self).save(*args, **kwargs)


class Field(models.Model):
    kind_of_field = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return u'%s' % self.kind_of_field


class Space(models.Model):
    field = models.ForeignKey(Field, on_delete=models.PROTECT)
    available_since = models.TimeField()
    available_until = models.TimeField()
    price_per_hour = models.IntegerField
    size = models.IntegerField()  # review if necessary
    photo = models.ImageField()
    description = models.TextField(blank=True, null=True)
    offer = models.FloatField(default=0)  # percentage by the moment
    last_update = models.DateField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s %d" % (self.field, self.id)

    def save(self, *args, **kwargs):
        self.last_update = date.today()
        super(Space, self).save(*args, **kwargs)


class Reservation(models.Model):
    event_name = models.CharField(max_length=100)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organizer")
    space = models.ForeignKey(Space, on_delete=models.PROTECT)
    reservation_date = models.DateField(auto_now_add=True)
    event_date = models.DateField()
    starting_hour = models.TimeField()
    ending_hour = models.TimeField()
    price = models.IntegerField()
    is_paid = models.BooleanField(default=False)
    last_update = models.DateField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, default=organizer)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.event_name
    
    def save(self, *args, **kwargs):
        self.last_update = date.today()
        super(Reservation, self).save(*args, **kwargs)
