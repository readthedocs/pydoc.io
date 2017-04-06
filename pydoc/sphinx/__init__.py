# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import environ
import json


def update_body(app, pagename, templatename, context, doctree):
    outdir = environ.Path(app.config.html_context['output_directory'])
    project = app.config.project
    version = app.config.version
    import ipdb; ipdb.set_trace()
    if not os.path.exists(outdir.root):
        os.makedirs(outdir.root)
    directory_name = "{name}-{version}".format(name=project, version=version)
    json_dir = outdir.path(directory_name)
    if not os.path.exists(json_dir.root):
        os.makedirs(json_dir.root)
    out_file = json_dir.path(pagename + '.json')
    out_file.write(json.dumps(context))


def setup(app):
    app.connect('html-page-context', update_body)
