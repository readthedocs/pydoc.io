from __future__ import absolute_import

import json
import os
import tempfile
import urllib.request
import zipfile

from celery import Celery
from django.apps import apps, AppConfig
from django.conf import settings
from django.template.loader import get_template


if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pydoc.settings.local')  # pragma: no cover


app = Celery('pydoc')


class CeleryConfig(AppConfig):
    name = 'pydoc.core.tasks'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        app.config_from_object('django.conf:settings')
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)


def _build_docs(project, version, project_url, project_filename, releases):
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

        autoapi_dirs = []
        for possible_project in os.listdir(extract_dir):
            if '__init__.py' in os.listdir(os.path.join(extract_dir, possible_project)):
                autoapi_dirs.append(os.path.join(extract_dir, possible_project))
        print('Autoapi now in %s' % autoapi_dirs)

        conf_filename = os.path.join(extract_dir, 'conf.py')
        with open(conf_filename, 'w+') as conf_file:
            to_write = conf_template.render(dict(
                autoapi_dirs=json.dumps(autoapi_dirs),
                project=project,
                version=version,
                releases=releases,
                output_directory=settings.JSON_DIR(),
                python_path=settings.ROOT_DIR(),
            ))
            conf_file.write(to_write)
        print('Conf File now in %s' % conf_filename)

        index_filename = os.path.join(extract_dir, 'index.rst')
        with open(index_filename, 'w+') as index_file:
            to_write = index_template.render(dict(
                project=project,
                version=version,
            ))
            index_file.write(to_write)
        print('Index File now in %s' % index_filename)

        outdir = settings.DOCS_DIR.path(directory_name)
        if not os.path.exists(outdir.root):
            os.makedirs(outdir.root)
        print('Running Sphinx')
        sphinx_command = 'sphinx-build -b html ' \
            '-d {root}_build/{name}-doctrees {root} {outdir}'.format(
                outdir=outdir.root,
                root=extract_dir,
                name=directory_name
            )
        print(sphinx_command)
        os.system(sphinx_command)


@app.task
def build(project, version=None):
    from .utils import get_highest_version
    from .models import Release
    if not version:
        version = get_highest_version(project)

    release = Release.objects.get(package__name=project, version=version)
    releases = Release.objects.filter(package__name=project, built=True)
    try:
        dist = release.distributions.get(filetype='bdist_wheel')
        project_url = dist.url
        project_filename = dist.filename
    except Exception:
        print("No valid wheel found. Skipping: {}".format(release))
        raise

    _build_docs(project, version, project_url, project_filename, releases)

    directory_name = "{name}-{version}".format(name=project, version=version)
    outdir = settings.DOCS_DIR.path(directory_name)
    if os.path.exists(os.path.join(outdir.root, 'index.html')):
        release.built = True
        release.save()


@app.task
def update_from_pypi(**time_kwargs):
    from .utils import build_changelog
    build_changelog(**time_kwargs)
