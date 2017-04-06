# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import environ
import json
import copy


def update_body(app, pagename, templatename, context, doctree):
    outdir = environ.Path(app.config.html_context['output_directory'])
    project = app.config.project
    version = app.config.version
    if not os.path.exists(outdir.root):
        os.makedirs(outdir.root)
    directory_name = "{name}-{version}".format(name=project, version=version)
    json_dir = outdir.path(directory_name)
    if not os.path.exists(json_dir.root):
        os.makedirs(json_dir.root)
    try:
        out_dir = json_dir.path('/'.join(pagename.split('/')[:-1]))
        if not os.path.exists(out_dir()):
            os.makedirs(out_dir())
        out_file = json_dir.path(pagename + '.json')
        to_write = open(out_file(), 'w+')
        to_context = copy.deepcopy(context)
        del to_context['hasdoc']
        del to_context['pathto']
        del to_context['toctree']
        del to_context['rellinks']
        to_write.write(json.dumps(to_context, indent=4))
    except Exception as e:
        print('ERRRRRRRRR: ', e)


def setup(app):
    app.connect('html-page-context', update_body)
