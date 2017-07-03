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

import requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.template.loader import get_template

from .models import Release, Package, Distribution, PackageIndex
from .querysets import sort_versions


log = logging.getLogger(__name__)

PYPI_API_URL = 'https://pypi.python.org/pypi'
TIMEFORMAT = "%Y%m%dT%H:%M:%S"

try:
    basestring
except NameError:
    basestring = str


def get_package_data(package):
    resp = requests.get('{api_root}/{package}/json'
                        .format(api_root=PYPI_API_URL, package=package))
    if resp.status_code != 200:
        log.error('Error fetching package from PyPI: url=%s, status_code=%s',
                  resp, resp.status_code)
        return {}
    try:
        resp_json = resp.json()
        resp_json['info']['name'] = resp_json['info']['name'].lower()
        return resp_json
    except json.decoder.JSONDecodeError:
        log.error('Package not found on PyPI: package=%s', package)
    return {}


def get_highest_version(package, data=None):
    # Get highest version
    versions = []
    if not data:
        data = get_package_data(package)
    try:
        for version in data['releases']:
            versions.append(version)
    except KeyError:
        return None
    if not versions:
        return None
    version = versions.sort(key=sort_versions)[-1]
    return version
