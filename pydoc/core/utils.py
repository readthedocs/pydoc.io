# -*- coding: utf-8 -*-


import datetime
import time
import xmlrpc.client
import threading
from queue import Queue

import requests

from .models import Package, Release, Distribution, PackageIndex

PYPI_API_URL = 'https://pypi.python.org/pypi'
TIMEFORMAT = "%Y%m%dT%H:%M:%S"

try:
    basestring
except NameError:
    basestring = str


def get_highest_version(package, data=None):
    # Get highest version
    versions = []
    if not data:
        package_resp = requests.get(
            'https://pypi.python.org/pypi/{name}/json'.format(name=package)
        )
        data = package_resp.json()
    for version in data['releases']:
        versions.append(version)
    if not versions:
        return None
    version = sorted(versions)[-1]
    return version


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
    from .tasks import build

    if packages:
        # Create objects that don't exist
        for arg in packages:
            update_package(arg, create=True)
        queryset = Package.objects.filter(name__in=packages)
    else:
        queryset = Package.objects.all()

    if latest:
        for package in queryset:
            versions = []
            for rel in package.releases.all():
                versions.append(rel.version)
            if len(versions):
                highest_version = sorted(versions)[-1]
                if package.releases.filter(version=highest_version, built=built).exists():
                    build.delay(project=package.name, version=highest_version)
                else:
                    print(
                        'Latest version package already built: {}-{}'.format(
                            package, highest_version
                        )
                    )
            else:
                print("No versions; {}".format(package))

    else:
        for package in queryset:
            qs = package.releases.all()
            if built:
                qs = qs.filter(built=True)
            for release in qs:
                print("updating %s:%s" % (package, release))
                build.delay(project=release.package.name, version=release.version)


def update_package_list(url=None):
    index = PackageIndex.objects.first()
    for package_name in index.client.list_packages():
        print('Adding %s' % package_name)
        package, created = Package.objects.get_or_create(index=index, name=package_name.lower())


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
    if len(release) > 128:
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
    if len(data['filename']) > 128:
        # TODO: more general validation and save to statistics
        print('ERR: Release too long: {}'.format(release))
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
    print('{} packages updated since {}'.format(len(packages), since))
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
    since = datetime.datetime.utcnow() - datetime.timedelta(**time_kwargs)
    packages = updated_packages_since(since)
    handle_build(packages, latest=True, built=False)
