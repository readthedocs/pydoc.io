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


log = logging.getLogger(__name__)

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
        try:
            data = package_resp.json()
        except json.decoder.JSONDecodeError:
            log.error('Package not found: package=%s', package)
            log.debug('Response: %s', package_resp.content)
            return None
    for version in data['releases']:
        versions.append(version)
    if not versions:
        return None
    version = sorted(versions)[-1]
    return version
