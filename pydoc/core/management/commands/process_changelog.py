"""
Management command for loading all the known packages from the official
pypi.
"""

from django.core.management.base import BaseCommand
from pydoc.core.pypi import process_changelog
import datetime


class Command(BaseCommand):
    help = """Update the package index with changed packages"""

    def handle(self, *args, **options):
        since = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        print("updating change from pypi since %s" % since)
        process_changelog(since,
                          update_releases=True, update_distributions=True,
                          mirror_distributions=False)
