"""
Build a specific set of packages.
"""

from django.core.management.base import BaseCommand

from pydoc.core.tasks import build
from pydoc.core.models import Package


class Command(BaseCommand):
    help = """Build docs passed in."""

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        for package_name in args:
            package = Package.objects.get(name=package_name)
            for release in package.releases.filter(built=True):
                print("updating %s:%s" % (package, release))
                build.delay(project=release.package.name, version=release.version)
        else:
            for package in Package.objects.filter(releases__built=True):
                for release in package.releases.filter(built=True):
                    print("updating %s:%s" % (package, release))
                    build.delay(project=release.package.name, version=release.version)
