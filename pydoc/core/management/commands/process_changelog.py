"""Update the package index with changed packages"""

import datetime

from django.core.management.base import BaseCommand

from pydoc.core.models import Package
from pydoc.core.tasks import (
    updated_packages_since, update_package, thread_update, build_changelog)


class Command(BaseCommand):
    help = """Update the package index with changed packages"""

    def add_arguments(self, parser):
        parser.add_argument(
            '--build',
            action='store_true',
            dest='build',
            default=True,
            help='Build changelog as well as update',
        )

        parser.add_argument(
            '--minutes',
            dest='minutes',
            type=int,
            default=120,
            help='Number of minutes to go back',
        )

    def handle(self, *args, **options):
        if options['build']:
            print('Building changelog')
            build_changelog(minutes=options['minutes'])
        else:
            since = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            print("updating change from pypi since %s" % since)
            packages = updated_packages_since(since)
            print('Processing {} packages'.format(len(packages)))
            queryset = Package.objects.filter(name__in=packages).iterator()
            thread_update(queryset=queryset, task=update_package)
