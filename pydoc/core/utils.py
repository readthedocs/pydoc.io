# -*- coding: utf-8 -*-


import time
import xmlrpc.client

import requests

from .tasks import build
from .models import Package, Release, Distribution, PackageIndex

PYPI_API_URL = 'https://pypi.python.org/pypi'
TIMEFORMAT = "%Y%m%dT%H:%M:%S"

try:
    basestring
except NameError:
    basestring = str


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


def get_package_json(package):
    package_resp = requests.get(
        'https://pypi.python.org/pypi/{name}/json'.format(name=package)
    )
    if package_resp.status_code != 200:
        print('Invalid Status code on {}: {}'.format(package, package_resp.status_code))
        return ''
    try:
        resp_json = package_resp.json()
        resp_json['info']['name'] = resp_json['info']['name'].lower()
        return resp_json
    except Exception as e:
        print('JSON Error: {}'.format(e))
    return ''


def handle_build(packages, latest=False, built=True):
    from pydoc.core.utils import update_package

    if packages:
        queryset = Package.objects.filter(name__in=packages)
        for arg in packages:
            update_package(arg)
    else:
        queryset = Package.objects.all()

    if latest:
        for package in queryset:
            versions = []
            for rel in package.releases.all():
                versions.append(rel.version)
            highest_version = sorted(versions)[-1]
            build.delay(project=package.name, version=highest_version)

    else:
        for package in queryset:
            qs = package.releases.all()
            if built:
                qs.filter(built=True)

            for release in qs:
                print("updating %s:%s" % (package, release))
                build.delay(project=release.package.name, version=release.version)


def update_package_list(url=None):
    index = PackageIndex.objects.first()
    for package_name in index.client.list_packages():
        print('Adding %s' % package_name)
        package, created = Package.objects.get_or_create(index=index, name=package_name.lower())


def update_packages(package_names=None):
    package_names = package_names or []
    for package_name in package_names:
        update_package(package_name)


def update_package(package, create=False, update_releases=True,
                   update_distributions=True, mirror_distributions=False):
    package_obj = get_package(package, create=create)
    if update_releases:
        package_json = get_package_json(package_obj.name)
        if not package_json:
            return
        for release, data in package_json['releases'].items():
            for dist in data:
                create_or_update_release(
                    package, release, dist,
                    update_distributions=update_distributions,
                    mirror_distributions=mirror_distributions)


def create_or_update_release(package, release, data=None,
                             update_distributions=False,
                             mirror_distributions=False):
    package = get_package(package, create=True)
    if not len(release) <= 128:
        # TODO: more general validation and save to statistics
        print('ERR: Release too long: {}'.format(release))
        return
    release_obj, created = Release.objects.get_or_create(package=package,
                                                         version=release)
    print('Updating release {}'.format(release_obj))
    update_data = {
        'filename': data['filename'],
        'md5_digest': data['md5_digest'],
        'size': data['size'],
        'url': data['url'],
        'comment': data['comment_text'],
    }
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


def process_changelog(since, update_releases=True,
                      update_distributions=True, mirror_distributions=False):
    client = xmlrpc.client.ServerProxy(PYPI_API_URL)
    timestamp = int(time.mktime(since.timetuple()))
    packages = {}
    for item in client.changelog(timestamp):
        packages[item[0]] = True
    print('Updating {} packages'.format(len(packages)))
    for package in packages.keys():
        print('Updating %s' % package)
        update_package(package, create=True,
                       update_releases=update_releases,
                       update_distributions=update_distributions,
                       mirror_distributions=mirror_distributions)
