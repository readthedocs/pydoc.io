"""Core Pydoc forms"""

from django import forms

from .utils import get_highest_version


class PackageForm(forms.Form):

    package = forms.CharField(label='Package', max_length=100)


class SearchPackageForm(PackageForm):
    pass


class BuildPackageForm(PackageForm):

    def clean_package(self):
        package = self.cleaned_data['package']
        self.version = get_highest_version(package)
        if not self.version:
            raise forms.ValidationError("Package not found on PyPI")
        return package

    def get_version(self):
        if self.is_valid():
            return self.version
