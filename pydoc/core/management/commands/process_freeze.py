"""
Management command for loading all the known packages from the official
pypi.
"""

import sys
from django.core.management.base import BaseCommand
from pydoc.taskapp.celery import build
from pydoc.core.pypi import create_or_update_release


class Command(BaseCommand):
    help = """Update the package index with changed packages"""

    def handle(self, *args, **options):
        for line in sys.stdin:
            line = line.strip()
            package, version = line.split('==')
            print("Building %s:%s" % (package, version))
            create_or_update_release(package=package, release=version)
            build.delay(project=package, version=version)
