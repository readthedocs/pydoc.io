"""Build packages from pip freeze output"""

import sys
import logging

from django.core.management.base import BaseCommand

from pydoc.core.models import Release
from pydoc.core.tasks import handle_build


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        # TODO this could probably be replace with actual parsing of freeze
        # output through pip import
        pairs = []
        for line in sys.stdin:
            line = line.strip()
            if not line or '#' in line:
                continue
            package, version = line.split('==')
            pairs.append((package, version))
        releases = Release.objects.get_pairs(pairs)
        handle_build(releases, built=False)
