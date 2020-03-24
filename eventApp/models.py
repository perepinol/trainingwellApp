from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Customer(User):
    is_adult = models.BooleanField()
    last_update = models.DateField()
    modified_by = models.ForeignKey('self', on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.username


class Space(models.Model):
    FIELD_OPTIONS = ('football_field', 'swimming_pool')

    field = models.CharField(max_length=50, choices=FIELD_OPTIONS)
    available_since = models.TimeField()
    available_until = models.TimeField()
    price_per_hour = models.IntegerField
    size = models.IntegerField()  # review if necessary
    photo = models.ImageField()
    description = models.TextField(blank=True, null=True)
    offer = models.FloatField()  # percentage by the moment
    last_update = models.DateField()
    modified_by = models.ForeignKey(Customer, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.field, self.id


class Reservation(models.Model):
    event_name = models.CharField(max_length=100)
    organizer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    space = models.ForeignKey(Space, on_delete=models.PROTECT)
    reservation_date = models.DateField(auto_now_add=True)
    event_date = models.DateField()
    starting_hour = models.TimeField()
    ending_hour = models.TimeField()
    price = models.IntegerField()
    is_paid = models.BooleanField(default=False)
    last_update = models.DateField()
    modified_by = models.ForeignKey(Customer, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s" % self.event_name
