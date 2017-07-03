from django.test import TestCase

from ..models import PackageIndex, Package, Release


class ReleaseTests(TestCase):

    def setUp(self):
        (self.index, _) = PackageIndex.objects.get_or_create(slug='pypi')

    def test_ordering_sorts_correctly(self):
        pkg = Package.objects.create(index=self.index, name='foo')
        a = Release.objects.create(package=pkg, version='1.19.0')
        b = Release.objects.create(package=pkg, version='1.9.0')
        self.assertEqual(pkg.releases.highest_version().pk, a.pk)

    def test_ordering_sorts_fallback(self):
        pkg = Package.objects.create(index=self.index, name='foo')
        a = Release.objects.create(package=pkg, version='bar')
        b = Release.objects.create(package=pkg, version='foo')
        self.assertEqual(pkg.releases.highest_version().pk, b.pk)

    def test_pair_lookup(self):
        pkg_foo = Package.objects.create(index=self.index, name='foo')
        pkg_bar = Package.objects.create(index=self.index, name='bar')
        a = Release.objects.create(package=pkg_foo, version='1.19.0')
        b = Release.objects.create(package=pkg_foo, version='1.9.0')
        c = Release.objects.create(package=pkg_bar, version='1.9.0')
        self.assertEqual(
            list(Release.objects.get_pairs([('foo', '1.9.0')])),
            [b]
        )
        self.assertEqual(
            list(Release.objects.get_pairs([('bar', '1.9.0')])),
            [c]
        )

    def test_latest_lookup(self):
        pkg_foo = Package.objects.create(index=self.index, name='foo')
        pkg_bar = Package.objects.create(index=self.index, name='bar')
        a = Release.objects.create(package=pkg_foo, version='1.19.0')
        b = Release.objects.create(package=pkg_foo, version='1.9.0')
        c = Release.objects.create(package=pkg_bar, version='1.9.0')
        self.assertEqual(
            list(Release.objects.get_latest(['foo', 'bar'])),
            [a, c]
        )
