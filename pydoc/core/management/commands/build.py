"""Build a specific set of packages"""

from django.core.management.base import BaseCommand

from pydoc.core.tasks import handle_build
from pydoc.core.models import Release


class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

        parser.add_argument(
            '--latest',
            action='store_true',
            dest='latest',
            default=False,
            help='Build all the latest versions of the packages',
        )

        parser.add_argument(
            '--not-built',
            action='store_false',
            dest='built',
            default=True,
            help='Build unbuilt versions of this package',
        )

    def handle(self, *args, **options):
        releases = Release.objects.get_latest(args)
        handle_build(releases, built=options['built'])
