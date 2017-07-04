from django.core.cache import cache
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from .forms import PackageForm
from .models import Release, Distribution, Package
from .tasks import handle_build, update_package, update_popular
from .utils import get_highest_version
from .conf import TYPE_WHEEL


class HomeView(TemplateView):
    template_name = "pages/home.html"
    title = "Pydoc Home"

    def releases(self):
        return Release.objects.filter(built=True)

    def popular(self):
        releases = set()
        popular = cache.get('homepage_popular', None) or update_popular()
        packages = Package.objects.filter(name__in=popular)

        for package in packages:
            release_qs = package.releases.filter(built=True)
            if release_qs.exists():
                releases.add(release_qs.latest())
        return releases


class BuildView(View):
    form_class = PackageForm
    template_name = "pages/build.html"
    title = "Pydoc Build"

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        success = False
        if form.is_valid():
            tried = True
            package = form.cleaned_data['package']
            version = form.get_version()
            if version:
                # TODO the following should be an async task and should avoid
                # form validation
                update_package(package)
                try:
                    release = (
                        Release.objects
                        .get(
                            distributions__filetype=TYPE_WHEEL,
                            release__package__name=package,
                            release__version=version,
                        ))
                except Release.DoesNotExist:
                    form.add_error(
                        'package',
                        'This package release has no wheels available'
                    )
                else:
                    success = True
                    handle_build([release])
        return render(request, self.template_name, {
            'form': form, 'success': success, 'tried': tried
        })


class ProjectSearchView(View):
    form_class = PackageForm
    template_name = "pages/search.html"

    def get(self, request, *args, **kwargs):
        query = request.GET.get('package')
        if query:
            form = self.form_class(request.GET)
            packages = Package.objects.filter(name__icontains=query, releases__built=True)
            rels = [package.releases.latest() for package in packages]
            return render(
                request,
                self.template_name,
                {'form': form, 'releases': rels}
            )
        return render(request, self.template_name, {'form': self.form_class()})
