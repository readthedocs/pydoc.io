# -*- coding: utf-8 -*-

from __future__ import absolute_import

import datetime
import json
import logging
import os
import tempfile
import threading
import time
import urllib.request
import xmlrpc.client
import zipfile
from queue import Queue
from typing import List

import requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.template.loader import get_template

from .models import Release, Package, Distribution, PackageIndex
from .utils import get_package_data, get_highest_version
from .conf import TYPE_WHEEL

log = logging.getLogger(__name__)

PYPI_API_URL = 'https://pypi.python.org/pypi'
TIMEFORMAT = "%Y%m%dT%H:%M:%S"

try:
    basestring
except NameError:
    basestring = str


def build_release(release):
    # TODO refactor these variables
    package = release.package.name
    version = release.version
    releases = release.package.releases.filter(built=True)
    try:
        dist = release.distributions.get(filetype=TYPE_WHEEL)
        dist_url = dist.url
        dist_filename = dist.filename
    except Distribution.DoesNotExist:
        return False

    conf_template = get_template('sphinx/conf.py.tmpl')
    index_template = get_template('sphinx/index.rst.tmpl')

    with tempfile.TemporaryDirectory() as tmp_dir:
        directory_name = "{name}-{version}".format(name=package, version=version)
        filename = os.path.join(tmp_dir, dist_filename)
        extract_dir = os.path.join(tmp_dir, directory_name)
        urllib.request.urlretrieve(dist_url, filename=filename)
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        log.debug('Wheel extracted: path=%s', extract_dir)

        autoapi_dirs = []
        for possible_module in os.listdir(extract_dir):
            if '__init__.py' in os.listdir(os.path.join(extract_dir, possible_module)):
                autoapi_dirs.append(os.path.join(extract_dir, possible_module))
        log.debug('AutoAPI paths detected: paths=%s', autoapi_dirs)

        conf_filename = os.path.join(extract_dir, 'conf.py')
        with open(conf_filename, 'w+') as conf_file:
            to_write = conf_template.render(dict(
                autoapi_dirs=json.dumps(autoapi_dirs),
                package=package,
                version=version,
                releases=releases,
                output_directory=settings.JSON_DIR(),
                python_path=settings.ROOT_DIR(),
            ))
            conf_file.write(to_write)
        log.debug('Sphinx conf.py generated: path=%s', conf_filename)

        index_filename = os.path.join(extract_dir, 'index.rst')
        with open(index_filename, 'w+') as index_file:
            to_write = index_template.render(dict(
                package=package,
                version=version,
            ))
            index_file.write(to_write)
        log.debug('Index file generated: path=%s', index_filename)

        outdir = settings.DOCS_DIR.path(directory_name)
        if not os.path.exists(outdir.root):
            os.makedirs(outdir.root)
        # TODO Run as an application, not as a shell command here
        sphinx_command = 'sphinx-build -b html ' \
            '-d {root}_build/{name}-doctrees {root} {outdir}'.format(
                outdir=outdir.root,
                root=extract_dir,
                name=directory_name
            )
        log.debug('Executing Sphinx: cmd=%s', sphinx_command)
        os.system(sphinx_command)


def get_package(package, create=False):
    """
    returns a package or none if it does not exist.
    """
    index = PackageIndex.objects.first()
    if isinstance(package, basestring):
        if create:
            package = Package.objects.get_or_create(index=index, name=package.lower())[0]
        else:
            try:
                package = Package.objects.get(index=index, name=package)
            except Package.DoesNotExist:
                package = None
    return package


def update_package_list(url=None):
    index = PackageIndex.objects.first()
    for package_name in index.client.list_packages():
        package, created = Package.objects.get_or_create(index=index, name=package_name.lower())


def update_package(package, create=True, update_releases=True,
                   update_distributions=True, mirror_distributions=False):
    package_obj = get_package(package, create=create)
    if update_releases:
        package_data = get_package_data(package_obj.name)
        if not package_data or 'releases' not in package_data:
            return
        for release, data in package_data['releases'].items():
            for dist in data:
                create_or_update_release(
                    package,
                    release,
                    package_info=package_data['info'],
                    data=dist,
                    update_distributions=update_distributions,
                    mirror_distributions=mirror_distributions
                )


def create_or_update_release(package, release, package_info=None, data=None,
                             update_distributions=False,
                             mirror_distributions=False):
    package = get_package(package, create=True)
    if len(release) > 128:
        # TODO: more general validation and save to statistics
        log.error('Release name too long: release=%s', release)
        return
    release_obj, created = Release.objects.get_or_create(package=package,
                                                         version=release)

    release_obj.package_info = package_info
    release_obj.save()
    update_data = {
        'filename': data['filename'],
        'md5_digest': data['md5_digest'],
        'size': data['size'],
        'url': data['url'],
        'comment': data['comment_text'],
        'uploaded_at': data['upload_time']
    }
    if len(data['filename']) > 128:
        # TODO: more general validation and save to statistics
        log.error('Package filename too long: filename=%s', data['filename'])
        return
    distribution, created = Distribution.objects.get_or_create(
        release=release_obj,
        filetype=data['packagetype'],
        pyversion=data['python_version'],
        defaults=update_data)
    if not created:
        # this means we have to update the existing record
        for key, value in update_data.items():
            setattr(distribution, key, value)
        distribution.save()
    return release_obj


def updated_packages_since(since):
    client = xmlrpc.client.ServerProxy(PYPI_API_URL)
    timestamp = int(time.mktime(since.timetuple()))
    packages = {}
    for item in client.changelog(timestamp):
        packages[item[0]] = True
    log.info('Packages updated updated: count=%d since=%s', len(packages), since)
    return packages.keys()


def thread_update(queryset, task, thread_count=20, **kwargs):

    def worker(q):
        while True:
            package = q.get()
            print(threading.current_thread().name, package)
            task(package, **kwargs)
            q.task_done()

    def run_queue(queryset):

        q = Queue()

        for i in range(thread_count):
            t = threading.Thread(target=worker, args=(q,))
            t.daemon = True
            t.start()

        for item in queryset:
            q.put(item)

        q.join()

    run_queue(queryset)


def build_changelog(**time_kwargs):
    # TODO this should pick out versions if possible, not just rely on `latest`
    # being the version that was updated
    since = datetime.datetime.utcnow() - datetime.timedelta(**time_kwargs)
    packages = updated_packages_since(since)
    releases = Release.objects.get_latest(packages)
    # TODO force builds here on not built?
    handle_build(releases, built=False)


def handle_build(releases: List[Release], built=True):
    """Trigger build on releases

    :param releases: List of releases to build
    :param built: Only build release if not built already
    """
    for release in releases:
        if built and release.built:
            log.error(
                'Latest version package already built: package=%s version=%s',
                release.package, release.version
            )
        else:
            build.delay(release_pk=release.pk)


def update_popular():
    api_key = getattr(settings, 'LIBRARIES_API_KEY', None)
    if not api_key:
        return ()
    url = 'https://libraries.io/api/search/?platforms=Pypi&sort=rank?api_key={key}'.format(
        key=api_key,
    )
    resp = requests.get(url)
    data = resp.json()
    popular = [obj['name'] for obj in data]
    cache.set('homepage_popular', popular, 3600)
    return popular


@shared_task
def build(release_pk):
    try:
        release = Release.objects.get(
            distributions__filetype=TYPE_WHEEL,
            pk=release_pk,
        )
        # TODO move this to build_release?
        result = build_release(release)
        if result:
            release.built = True
            release.save()
    except Release.DoesNotExist:
        log.info('Release does not include wheel distributions: release=%s',
                 release_pk)


@shared_task
def update_from_pypi(**time_kwargs):
    build_changelog(**time_kwargs)
