from django.utils import timezone

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    is_adult = models.BooleanField(default=False)
    last_update = models.DateTimeField()
    modified_by = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.username

    def save(self, *args, **kwargs):
        self.last_update = timezone.now()
        super(AbstractUser, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()


class Field(models.Model):
    kind_of_field = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return u'%s' % self.kind_of_field


class Space(models.Model):
    field = models.ForeignKey(Field, on_delete=models.PROTECT)
    available_since = models.TimeField()
    available_until = models.TimeField()
    price_per_hour = models.IntegerField()
    sqmt = models.IntegerField()
    photo = models.ImageField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    offer = models.FloatField(default=0)  # percentage by the moment
    last_update = models.DateTimeField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s %d" % (self.field, self.id)

    def save(self, *args, **kwargs):
        self.last_update = timezone.now()
        super(Space, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()


class Reservation(models.Model):
    event_name = models.CharField(max_length=100)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organizer")
    reservation_date = models.DateTimeField(auto_now_add=True)
    price = models.IntegerField()
    is_paid = models.BooleanField(default=False)
    last_update = models.DateTimeField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, default=organizer)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.event_name
    
    def save(self, *args, **kwargs):
        self.last_update = timezone.now()
        super(Reservation, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()


def get_timeblock_space(timeblock):
    def callable_func():
        return timeblock.space
    return callable_func


class Timeblock(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.SET(get_timeblock_space('self').__str__()))
    start_time = models.DateTimeField()

    def __str__(self):
        return u"%s at %s" % (self.space, self.start_time.isoformat())


