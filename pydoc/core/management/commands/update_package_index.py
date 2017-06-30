"""Load all the known packages from the official PyPI"""

from django.core.management.base import BaseCommand
from pydoc.core.tasks import update_package_list


class Command(BaseCommand):
    help = """Update the package index (packages only. no releases.)"""

    def handle(self, *args, **options):
        update_package_list()
