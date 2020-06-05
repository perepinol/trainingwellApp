from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Generates a manager report and stores it in static files'

    def handle(self, *args, **options):
        pass