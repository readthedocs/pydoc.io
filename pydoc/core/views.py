from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View

from django import forms

from pydoc.taskapp.celery import build
from pydoc.core.models import Release


class BuildForm(forms.Form):
    project = forms.CharField(label='Project', max_length=100)


class HomeView(TemplateView):
    template_name = "pages/home.html"
    title = "Pydoc Home"

    def projects(self):
        return Release.objects.filter(built=True)


class BuildView(View):
    form_class = BuildForm
    # initial = {'project': 'requests'}
    template_name = "pages/build.html"
    title = "Pydoc Build"

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        success = False
        if form.is_valid():
            # <process form cleaned data>
            project = form.cleaned_data['project']
            build.delay(project=project)
            success = True
        return render(request, self.template_name, {
            'form': form, 'success': success
        })
