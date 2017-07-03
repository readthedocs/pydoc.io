"""Pydoc querysets"""

from functools import cmp_to_key
from typing import List, Tuple, TypeVar, Iterator

import semver
from django.db import models


TypeReleasePair = Tuple[str, str]
TypeRelease = TypeVar('Release')


class ReleaseQuerySet(models.QuerySet):

    def get_pairs(self, pairs: List[TypeReleasePair]) -> Iterator[TypeRelease]:
        """Generator for release lookup of pairs of package names and versions

        :param pairs: List of release lookup pairs, should be tuples of
            (``package name``, ``release version``)
        """
        for (package, version) in pairs:
            try:
                yield self.get(package__name=package, version=version)
            except self.model.DoesNotExist:
                continue

    def get_latest(self, packages: List[str]) -> Iterator[TypeRelease]:
        """Generator for release lookup of latest versions

        :param packages: List of package names to lookup
        """
        for package in packages:
            try:
                yield self.filter(package__name=package).highest_version()
            except self.model.DoesNotExist:
                continue

    def highest_version(self):
        releases = list(self.all())
        releases.sort(key=sort_versions)
        return releases[-1]


def sort_versions(obj):
    def version_sorter(a, b):
        try:
            return semver.compare(a.version, b.version)
        except (ValueError, TypeError):
            return semver.cmp(a.version, b.version)

    return cmp_to_key(version_sorter)(obj)
