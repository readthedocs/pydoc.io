import os

from django.views.generic import TemplateView
from django.conf import settings

from pydoc.taskapp.celery import build
from pydoc.core.models import Release


class HomeView(TemplateView):
    template_name = "pages/home.html"
    title = "Pydoc Home"

    def projects(self):
        return Release.objects.filter(built=True)


class BuildView(TemplateView):
    template_name = "pages/build.html"
    title = "Pydoc Build"

    def build(self):
        build.delay(project='requests', version='2.9.2')
