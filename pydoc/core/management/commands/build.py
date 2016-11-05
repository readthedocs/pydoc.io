"""
Build a specific set of packages.
"""

from django.core.management.base import BaseCommand

from pydoc.taskapp.celery import build
from pydoc.core.models import Package


class Command(BaseCommand):
    help = """Build docs from pip freeze output"""

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):
        for package_name in args:
            package = Package.objects.get(name=package_name)
            for release in package.releases.filter(built=True):
                print("updating %s:%s" % (package, release))
                build.delay(project=release.package.name, version=release.version)
