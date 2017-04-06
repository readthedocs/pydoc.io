"""
Management command for loading all the known packages from the official
pypi.
"""

from django.core.management.base import BaseCommand
from pydoc.core.models import Package
from pydoc.core.utils import update_package, thread_update


class Command(BaseCommand):
    args = '<package_name package_name ...>'
    help = """Update the package index (packages only. no releases.)"""

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        if not args:
            # update all packages! using iterator() because querysets get cahced
            # and we access files in the loop. they use a lot of ram.
            queryset = Package.objects.all().iterator()
            thread_update(queryset=queryset, task=update_package)
        for package_name in args:
            try:
                package = Package.objects.get(name=package_name)
                print("updating <%s>" % package.name)
                update_package(package=package, update_releases=True,
                               update_distributions=True)
            except Package.DoesNotExist:
                print("package <%s> does not exist in local database" % package_name)
