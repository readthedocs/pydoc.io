#-*- coding: utf-8 -*-

from pydoc.core.models import Package, Release, Distribution, PackageIndex
import datetime
import time
import xmlrpc.client


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
            package = Package.objects.get_or_create(index=index, name=package)[0]
        else:
            try:
                package = Package.objects.get(index=index, name=package)
            except Package.DoesNotExist:
                package = None
    return package


def update_package_list(url=None):
    index = PackageIndex.objects.first()
    for package_name in index.client.list_packages():
        print('Adding %s' % package_name)
        package, created = Package.objects.get_or_create(index=index, name=package_name)


def update_packages(package_names=None):
    package_names = package_names or []
    for package_name in package_names:
        update_package(package_name)


def update_package(package, create=False, update_releases=True,
                   update_distributions=True, mirror_distributions=False):
    package = get_package(package, create=create)
    client = xmlrpc.client.ServerProxy(PYPI_API_URL)
    if update_releases:
        for release in client.package_releases(package.name, True):  # True-> show hidden
            release = create_or_update_release(
                package, release,
                update_distributions=update_distributions,
                mirror_distributions=mirror_distributions)


def create_or_update_release(package, release,
                             update_distributions=False,
                             mirror_distributions=False):
    client = xmlrpc.client.ServerProxy(PYPI_API_URL)
    package = get_package(package)
    if isinstance(release, basestring):
        if not len(release) <= 128:
            # TODO: more general validation and save to statistics
            return
        print('Creating release %s:%s' % (package, release))
        release, created = Release.objects.get_or_create(package=package,
                                                         version=release)
        print('Updated release %s for %s' % (release.version, package.name))
    data = client.release_data(package.name, release.version)
    release.hidden = data.get('_pypi_hidden', False)
    for key, value in data.items():
        release.package_info[key] = value
    release.save()
    if update_distributions:
        for dist in client.release_urls(package.name, release.version):
            data = {
                'filename': dist['filename'],
                'md5_digest': dist['md5_digest'],
                'size': dist['size'],
                'url': dist['url'],
                'comment': dist['comment_text'],
            }
            try:
                data['uploaded_at'] = datetime.datetime.strptime(
                    dist['upload_time'].value, TIMEFORMAT)
            except:
                pass
            distribution, created = Distribution.objects.get_or_create(
                release=release,
                filetype=dist['packagetype'],
                pyversion=dist['python_version'],
                defaults=data)
            if not created:
                # this means we have to update the existing record
                for key, value in data.items():
                    setattr(distribution, key, value)
            # distribution.mirror_package(commit=False)
            distribution.save()


def process_changelog(since, update_releases=True,
                      update_distributions=True, mirror_distributions=False):
    client = xmlrpc.client.ServerProxy(PYPI_API_URL)
    timestamp = int(time.mktime(since.timetuple()))
    packages = {}
    for item in client.changelog(timestamp):
        packages[item[0]] = True
    for package in packages.keys():
        print('Updating %s' % package)
        update_package(package, create=True,
                       update_releases=update_releases,
                       update_distributions=update_distributions,
                       mirror_distributions=mirror_distributions)

