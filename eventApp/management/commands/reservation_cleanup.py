from datetime import datetime, timedelta

from django.core.management import BaseCommand

from eventApp.models import Reservation, Notification
from eventApp.views import logger, cancelled_oot


class Command(BaseCommand):
    help = 'Deletes all reservation that have finished two years before now or that have not been paid in one ' \
           'day after the reservation date'

    def handle(self, *args, **options):
        now = datetime.now()
        two_years_ago = now.replace(year=now.year - 2)
        yesterday = now - timedelta(days=1)

        old_reservations = Reservation.objects.filter(timeblock__end_time__lt=two_years_ago)
        logger.info("Deleting %d old reservations" % old_reservations.count())
        old_reservations.delete()

        unpaid_reservations = Reservation.objects.filter(reservation_date__lt=yesterday, status=Reservation.UNPAID)
        logger.info("Cancelling %d unpaid reservations" % unpaid_reservations.count())
        for res in unpaid_reservations:
            res.status = Reservation.CANCELOUTTIME if cancelled_oot(res) else Reservation.CANCEL
            res.save()
            Notification.objects.create(
                title='Reservation cancelled',
                content='Reservation %s has been cancelled because it was not paid in a day' % res.event_name,
                user=res.user
            )
