from __future__ import absolute_import

import os
import tempfile
from collections import defaultdict

from celery import Celery
from django.apps import apps, AppConfig
from django.conf import settings
from django.template.loader import get_template
import requests
import urllib.request
import zipfile

if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')  # pragma: no cover


app = Celery('pydoc')


class CeleryConfig(AppConfig):
    name = 'pydoc.taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        app.config_from_object('django.conf:settings')
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)

        if hasattr(settings, 'RAVEN_CONFIG'):
            # Celery signal registration
            from raven import Client as RavenClient
            from raven.contrib.celery import register_signal as raven_register_signal
            from raven.contrib.celery import register_logger_signal as raven_register_logger_signal

            raven_client = RavenClient(dsn=settings.RAVEN_CONFIG['DSN'])
            raven_register_logger_signal(raven_client)
            raven_register_signal(raven_client)


def _build_docs(project, version, project_url, project_filename):
    conf_template = get_template('sphinx/conf.py.tmpl')
    index_template = get_template('sphinx/index.rst.tmpl')

    with tempfile.TemporaryDirectory() as tmp_dir:
        directory_name = "{name}-{version}".format(name=project, version=version)
        filename = os.path.join(tmp_dir, project_filename)
        extract_dir = os.path.join(tmp_dir, directory_name)
        urllib.request.urlretrieve(project_url, filename=filename)
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        print('File now in %s' % extract_dir)

        autoapi_dir = ''
        for possible_project in os.listdir(extract_dir):
            if '__init__.py' in os.listdir(os.path.join(extract_dir, possible_project)):
                autoapi_dir = os.path.join(extract_dir, possible_project)
        print('Autoapi now in %s' % autoapi_dir)

        conf_filename = os.path.join(extract_dir, 'conf.py')
        with open(conf_filename, 'w+') as conf_file:
            to_write = conf_template.render(dict(
                autoapi_dir=autoapi_dir,
                project=project,
                version=version,
            ))
            conf_file.write(to_write)
        print('Conf File now in %s' % conf_filename)

        index_filename = os.path.join(extract_dir, 'index.rst')
        with open(index_filename, 'w+') as index_file:
            to_write = index_template.render(dict(
                autoapi_dir=autoapi_dir,
                project=project,
                version=version,
            ))
            index_file.write(to_write)
        print('Index File now in %s' % index_filename)

        outdir = settings.DOCS_DIR.path(directory_name)
        if not os.path.exists(outdir.root):
            os.makedirs(outdir.root)
        print('Running Sphinx')
        sphinx_command = 'sphinx-build -b html -d {root}_build/{name}-doctrees {root} {outdir}'.format(
            outdir=outdir.root,
            root=extract_dir,
            name=directory_name
        )
        print(sphinx_command)
        os.system(sphinx_command)


def _get_highest_version(project):
    # Get highest version
    versions = defaultdict(list)
    package_resp = requests.get(
        'https://pypi.python.org/pypi/{name}/json'.format(name=project)
    )
    package_json = package_resp.json()
    for version in package_json['releases']:
        versions[project].append(version)
    version = sorted(versions[project])[-1]
    return version


@app.task
def build(project, version=None):
    from pydoc.core.pypi import create_or_update_release
    if not version:
        version = _get_highest_version(project)

    release = create_or_update_release(project, version)

    project_resp = requests.get(
        'https://pypi.python.org/pypi/{project}/{version}/json'.format(
            project=project,
            version=version,
        )
    )
    project_json = project_resp.json()

    project_url = project_filename = ''
    for rel in project_json['releases'][version]:
        if rel['packagetype'] == 'bdist_wheel':
            project_url = rel['url']
            project_filename = rel['filename']
            break

    if not project_url or not project_filename:
        print("No valid wheel found. Skipping")
        return

    _build_docs(project, version, project_url, project_filename)
    release.built = True
    release.save()
