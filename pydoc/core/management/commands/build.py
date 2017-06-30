"""Build a specific set of packages"""

from django.core.management.base import BaseCommand

from pydoc.core.tasks import handle_build


class Command(BaseCommand):
    help = """Build docs passed in."""

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
        handle_build(packages=args, latest=options['latest'], built=options['built'])
