"""
Most of this modeling came from https://github.com/stefanfoulis/django-packageindex
Thanks to all those who contributed.
"""

import xmlrpc
import datetime
import time

from django.db import models
from django.utils.datastructures import MultiValueDict
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField

from . import conf


try:
    basestring
except NameError:
    basestring = str

PYPI_API_URL = 'https://pypi.python.org/pypi'
PYPI_SIMPLE_URL = 'https://pypi.python.org/simple'
MIRROR_FILETYPES = ['*.zip', '*.tgz', '*.egg', '*.tar.gz', '*.tar.bz2']


class Classifier(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    class Meta:
        verbose_name = _(u"classifier")
        verbose_name_plural = _(u"classifiers")
        ordering = ('name',)

    def __str__(self):
        return self.name


class PackageIndexManager(models.Manager):
    pass


class PackageIndex(models.Model):
    slug = models.CharField(max_length=255, unique=True, default='pypi')
    updated_from_remote_at = models.DateTimeField(null=True, blank=True)
    xml_rpc_url = models.URLField(blank=True, default=PYPI_API_URL)
    simple_url = models.URLField(blank=True, default=PYPI_SIMPLE_URL)

    objects = PackageIndexManager()

    class Meta:
        verbose_name_plural = 'package indexes'

    def __str__(self):
        return self.slug

    @property
    def client(self):
        if not hasattr(self, '_client'):
            self._client = xmlrpc.client.ServerProxy(self.xml_rpc_url)
        return self._client


class Package(models.Model):
    index = models.ForeignKey(PackageIndex)
    name = models.CharField(max_length=255, unique=True, primary_key=True)
    auto_hide = models.BooleanField(default=True, blank=False)
    updated_from_remote_at = models.DateTimeField(null=True, blank=True)
    parsed_external_links_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _(u"package")
        verbose_name_plural = _(u"packages")
        get_latest_by = "releases__latest"
        ordering = ['name', ]

    def __str__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('packageindex-package', (), {'package': self.name})

    @property
    def latest(self):
        try:
            return self.releases.latest()
        except Release.DoesNotExist:
            return None

    def get_release(self, version):
        """Return the release object for version, or None"""
        try:
            return self.releases.get(version=version)
        except Release.DoesNotExist:
            return None


class Release(models.Model):
    package = models.ForeignKey(Package, related_name="releases")
    version = models.CharField(max_length=128)
    metadata_version = models.CharField(max_length=64, default='1.0')
    package_info = JSONField(default=dict)
    built = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    is_from_external = models.BooleanField(default=False)

    class Meta:
        verbose_name = _(u"release")
        verbose_name_plural = _(u"releases")
        unique_together = ("package", "version")
        get_latest_by = 'distributions__uploaded_at'
        ordering = ['-distributions__uploaded_at']

    def __str__(self):
        return self.release_name

    @property
    def release_name(self):
        return u"%s-%s" % (self.package.name, self.version)

    @models.permalink
    def get_absolute_url(self):
        return ('packageindex-release', (), {'package': self.package.name,
                                             'version': self.version})

    @property
    def summary(self):
        return self.package_info.get('summary', u'')

    @property
    def description(self):
        return self.package_info.get('description', u'')

    @property
    def classifiers(self):
        return self.package_info.getlist('classifier')


class Distribution(models.Model):
    release = models.ForeignKey(Release, related_name="distributions")
    filename = models.CharField(blank=True, default='', max_length=5000,
                                help_text="the filename as provided by pypi")
    file = models.FileField(upload_to=conf.RELEASE_UPLOAD_TO,
                            null=True, blank=True,
                            help_text='the distribution file (if it was mirrord locally)',
                            max_length=5000)
    url = models.URLField(null=True, blank=True,
                          help_text='the original url provided by pypi',
                          max_length=5000)
    size = models.IntegerField(null=True, blank=True)
    md5_digest = models.CharField(max_length=32, blank=True)
    filetype = models.CharField(max_length=32, blank=False,
                                choices=conf.DIST_FILE_TYPES)
    pyversion = models.CharField(max_length=16, blank=True,
                                 choices=conf.PYTHON_VERSIONS)
    comment = models.TextField(blank=True, default='')
    signature = models.TextField(blank=True, default='')

    uploaded_at = models.DateTimeField(null=True, blank=True,
                                       help_text='The time the package was uploaded (on pypi)')
    mirrored_at = models.DateTimeField(null=True, blank=True,
                                       help_text='The time the package was downloaded (here)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_from_external = models.BooleanField(default=False)

    class Meta:
        verbose_name = _(u"distribution")
        verbose_name_plural = _(u"distributions")
        unique_together = ("release", "filetype", "pyversion")

    def __str__(self):
        return self.filename

    def get_absolute_url(self):
        return "%s#md5=%s" % (self.path, self.md5_digest)

    @property
    def display_filetype(self):
        for key, value in conf.DIST_FILE_TYPES:
            if key == self.filetype:
                return value
        return self.filetype

    @property
    def path(self):
        if self.file:
            return self.file.url
        else:
            return self.url
