"""
Management command for loading all the known packages from the official
pypi.
"""

import sys
from django.core.management.base import BaseCommand
from pydoc.core.tasks import build
from pydoc.core.utils import update_package


class Command(BaseCommand):
    help = """Build docs from pip freeze output"""

    def handle(self, *args, **options):
        for line in sys.stdin:
            line = line.strip()
            if not line or '#' in line:
                continue
            print(line)
            package, version = line.split('==')
            print("Building %s:%s" % (package, version))
            update_package(package=package)
            build.delay(project=package, version=version)
