from datetime import datetime, date

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    is_adult = models.BooleanField(default=False)
    last_update = models.DateTimeField()
    passw_changed = models.BooleanField(default=False)
    modified_by = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.username

    def save(self, *args, **kwargs):
        self.last_update = datetime.now()
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
        self.last_update = datetime.now()
        super(Season, self).save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return u"%s" % self.name

    @staticmethod
    def ongoing_season(day=date.today()):
        return Season.objects.filter(start_date__lte=day, end_date__gt=day).first()

    def open_hours(self):
        hours = [self.open_time]
        next_datetime = datetime.combine(date.today(), hours[-1]) + settings.RESERVATION_GRANULARITY
        while next_datetime.time() < self.close_time:
            hours.append(next_datetime.time())
            next_datetime = datetime.combine(date.today(), hours[-1]) + settings.RESERVATION_GRANULARITY
        return hours


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
        self.last_update = datetime.now()
        super(Space, self).save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def current_season(self, day=date.today()):
        return self.season.filter(start_date__lte=day, end_date__gt=day).first()

    def is_available_in_season(self, day=date.today()):
        return self.current_season(day) is not None

    def get_season_open_hour(self, day=date.today()):
        return self.current_season(day).open_time.hour

    def get_season_close_hour(self, day=date.today()):
        return self.current_season(day).close_time.hour


class Reservation(models.Model):
    PAID = 'P'
    UNPAID = 'U'
    CANCELTOREFUND = 'CTR'
    CANCELANDREFUND = 'CR'
    CANCELOUTTIME = 'COT'
    CANCEL = 'C'
    STATUS = ((PAID, 'Paid'), (UNPAID, 'Unpaid'), (CANCELTOREFUND, 'Canceled, waiting refund'),
              (CANCELANDREFUND, 'Canceled and refunded'), (CANCELOUTTIME, 'Canceled out of time'), (CANCEL, 'Canceled'))
    status = models.CharField(max_length=100, choices=STATUS)
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
        self.last_update = datetime.now()
        super(Reservation, self).save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def current_state(self):
        for s in self.STATUS:
            if self.status == s[0]: return s[1]


def get_timeblock_space(timeblock):
    def callable_func():
        return timeblock.space
    return callable_func


class Timeblock(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.SET(get_timeblock_space('self').__str__()))
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        ordering = ['start_time']

    def save(self, *args, **kwargs):
        self.end_time = self.start_time + settings.RESERVATION_GRANULARITY
        super(Timeblock, self).save(*args, **kwargs)

    def __str__(self):
        return u"%s at %s" % (self.space, self.start_time.isoformat())


class Incidence(models.Model):
    name = models.CharField(max_length=50)
    content = models.TextField()
    limit = models.DateTimeField()
    affected_fields = models.ManyToManyField(Space, blank=True)
    disable_fields = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)  # Also represents a finished Incidence

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.is_deleted = True
        self.save()


class Invoice(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT)
    timeblocks = []

    def __str__(self):
        return "Invoice of " + self.reservation.event_name
