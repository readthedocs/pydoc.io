"""
Management command for loading all the known packages from the official
pypi.
"""

from django.core.management.base import BaseCommand
from pydoc.core.utils import updated_packages_since, update_package, thread_update, build_changelog
from pydoc.core.models import Package
import datetime


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

    def handle(self, *args, **options):
        if options['build']:
            print('Building changelog')
            build_changelog()
        else:
            since = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            print("updating change from pypi since %s" % since)
            packages = updated_packages_since(since)
            print('Processing {} packages'.format(len(packages)))
            queryset = Package.objects.filter(name__in=packages).iterator()
            thread_update(queryset=queryset, task=update_package)
