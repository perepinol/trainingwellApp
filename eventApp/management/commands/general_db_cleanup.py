from datetime import datetime
from dateutils import relativedelta

from django.core.management import BaseCommand

from eventApp.models import User, Season, Space
from eventApp.views import logger


class Command(BaseCommand):
    help = 'Deletes all database objects (except Reservations) that have been soft-deleted for 6 months'
    db_models = [User, Season, Space]

    def handle(self, *args, **options):
        last_mod = datetime.now() - relativedelta(months=6)
        for model in Command.db_models:
            instances_to_delete = model.objects.filter(is_deleted=True, last_update__lte=last_mod)
            logger.info("Hard-deleting %d %s instances" % (instances_to_delete.count(), model.__name__))

