from django.conf import settings
import os

# This is disabled on pypi.python.org, can be useful if you make mistakes
ALLOW_VERSION_OVERWRITE = False

""" The upload_to argument for the file field in releases. This can either be 
a string for a path relative to your media folder or a callable. For more 
information, see http://docs.djangoproject.com/ """


def distribution_upload_to(instance, filename):
    return os.path.join('dists', instance.release.package.name, filename)


RELEASE_UPLOAD_TO = distribution_upload_to

# RELEASE_UPLOAD_TO = 'dists'

OS_NAMES = (
    ("aix", "AIX"),
    ("beos", "BeOS"),
    ("debian", "Debian Linux"),
    ("dos", "DOS"),
    ("freebsd", "FreeBSD"),
    ("hpux", "HP/UX"),
    ("mac", "Mac System x."),
    ("macos", "MacOS X"),
    ("mandrake", "Mandrake Linux"),
    ("netbsd", "NetBSD"),
    ("openbsd", "OpenBSD"),
    ("qnx", "QNX"),
    ("redhat", "RedHat Linux"),
    ("solaris", "SUN Solaris"),
    ("suse", "SuSE Linux"),
    ("yellowdog", "Yellow Dog Linux"),
)

ARCHITECTURES = (
    ("alpha", "Alpha"),
    ("hppa", "HPPA"),
    ("ix86", "Intel"),
    ("powerpc", "PowerPC"),
    ("sparc", "Sparc"),
    ("ultrasparc", "UltraSparc"),
)

DIST_FILE_TYPES = (
    ('sdist', 'Source'),
    ('bdist_dumb', '"dumb" binary'),
    ('bdist_rpm', 'RPM'),
    ('bdist_wininst', 'MS Windows installer'),
    ('bdist_egg', 'Python Egg'),
    ('bdist_dmg', 'OS X Disk Image'),
)

PYTHON_VERSIONS = (
    ('any', 'Any i.e. pure python'),
    ('2.1', '2.1'),
    ('2.2', '2.2'),
    ('2.3', '2.3'),
    ('2.4', '2.4'),
    ('2.5', '2.5'),
    ('2.6', '2.6'),
    ('2.7', '2.7'),
    ('3.0', '3.0'),
    ('3.1', '3.1'),
    ('3.2', '3.2'),
)

METADATA_FIELDS = {
    '1.0': ('platform', 'summary', 'description', 'keywords', 'home_page',
            'author', 'author_email', 'license', ),
    '1.1': ('platform', 'supported_platform', 'summary', 'description',
            'keywords', 'home_page', 'download_url', 'author', 'author_email',
            'license', 'classifier', 'requires', 'provides', 'obsoletes',),
    '1.2': ('platform', 'supported_platform', 'summary', 'description',
            'keywords', 'home_page', 'download_url', 'author', 'author_email',
            'maintainer', 'maintainer_email', 'license', 'classifier',
            'requires_dist', 'provides_dist', 'obsoletes_dist',
            'requires_python', 'requires_external', 'project_url'),
}

METADATA_FORMS = {
    '1.0': 'packageindex.forms.Metadata10Form',
    '1.1': 'packageindex.forms.Metadata11Form',
    '1.2': 'packageindex.forms.Metadata12Form',
}

FALLBACK_VIEW = 'packageindex.views.releases.index'

ACTION_VIEWS = {
    "file_upload": 'packageindex.views.distutils.register_or_upload',
    "submit": 'packageindex.views.distutils.register_or_upload',
    "list_classifiers": 'packageindex.views.distutils.list_classifiers',
}

XMLRPC_COMMANDS = {
    'list_packages': 'packageindex.views.xmlrpc.list_packages',
    'package_releases': 'packageindex.views.xmlrpc.package_releases',
    'release_urls': 'packageindex.views.xmlrpc.release_urls',
    'release_data': 'packageindex.views.xmlrpc.release_data',
}

""" These settings enable proxying of packages that are not in the local index
to another index, http://pypi.python.org/ by default. This feature is disabled
by default and can be enabled by setting packageindex_PROXY_MISSING to True in
your settings file. """
PROXY_BASE_URL = 'https://pypi.python.org/simple'

PROXY_MISSING = False

""" Allow any user to maintain a package. """
GLOBAL_OWNERSHIP = False

for k in dir(settings):
    if k.startswith('packageindex_'):
        locals()[k.split('packageindex_', 1)[1]] = getattr(settings, k)
