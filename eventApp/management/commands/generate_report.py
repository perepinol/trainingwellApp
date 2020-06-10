from datetime import datetime

from xhtml2pdf import pisa
from django.core.management import BaseCommand

from requests_html import HTMLSession
from dateutils import relativedelta

from eventApp.views import logger


class Command(BaseCommand):
    help = 'Generates a monthly manager report and stores it in static files'
    include = ["use", "incomeoutcome", "performance"]

    def add_arguments(self, parser):
        parser.add_argument('username', help='The manager username')
        parser.add_argument('password', help='The manager password')
        parser.add_argument('-host', help='The host and port of the Django app', default='127.0.0.1:8000')

    def handle(self, *args, **options):
        base_url = 'http://%s/en' % options['host']
        cli = HTMLSession()

        # Login as manager
        res = cli.post(base_url + '/accounts/login/', data={
            'username': options['username'],
            'password': options['password'],
            'csrfmiddlewaretoken': Command._get_csrf_token(cli, base_url + '/accounts/login/')
        })
        if res.status_code != 200:
            raise RuntimeError('Could not login (status %d)' % res.status_code)

        # Get report HTML
        end_date = datetime.today().replace(day=1) - relativedelta(days=1)
        start_date = end_date.replace(day=1)
        res = cli.post(base_url + '/events/report/', data={
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'include': Command.include,
            'csrfmiddlewaretoken': Command._get_csrf_token(cli, base_url + '/events/report/')
        })
        if res.status_code != 200:
            raise RuntimeError('Could not get report (status %d)' % res.status_code)

        res.html.render(reload=False)
        result = open('output.pdf', 'w+b')
        status = pisa.CreatePDF(res.html.find('.container', first=True).raw_html, dest=result)
        result.close()
        cli.close()
        if status.err:
            raise RuntimeError('PDF did not process correctly')
        logger.info("Successfully generated PDF")

    @staticmethod
    def _get_csrf_token(cli, page):
        res = cli.get(page)
        if res.status_code != 200 or 'csrftoken' not in cli.cookies:
            raise RuntimeError('Could not get CSRF token (status %d)' % res.status_code)
        return cli.cookies['csrftoken']
