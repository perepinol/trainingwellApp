from django.utils import timezone
from datetime import date

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

    def soft_delete(self):
        self.is_deleted = True
        self.save()


class Notification(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)  # Also represents a seen notification

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.is_deleted = True
        self.save()


class Field(models.Model):
    kind_of_field = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return u'%s' % self.kind_of_field

    def soft_delete(self):
        self.is_deleted = True
        self.save()


class Season(models.Model):
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    open_time = models.TimeField()
    close_time = models.TimeField()
    last_update = models.DateTimeField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.last_update = timezone.now()
        super(Season, self).save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return u"%s" % self.name


class Space(models.Model):
    field = models.ForeignKey(Field, on_delete=models.PROTECT)
    season = models.ManyToManyField(Season)
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

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def current_season(self):
        return self.season.filter(start_date__lte=date.today(), end_date__gt=date.today()).first()

    def is_available_in_season(self):
        return self.current_season() is not None

    def get_season_open_hour(self):
        return self.current_season().open_time.hour

    def get_season_close_hour(self):
        return self.current_season().close_time.hour


class Reservation(models.Model):
    event_name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reservation_date = models.DateTimeField(auto_now_add=True)
    price = models.IntegerField()
    is_paid = models.BooleanField(default=False)
    last_update = models.DateTimeField()
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="modifier")
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.event_name
    
    def save(self, *args, **kwargs):
        self.last_update = timezone.now()
        super(Reservation, self).save(*args, **kwargs)

    def soft_delete(self):
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

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return u"%s at %s" % (self.space, self.start_time.isoformat())


