from django.contrib import admin
from pydoc.core.models import Package, Release, Classifier, \
    Distribution, PackageIndex


class PackageIndexAdmin(admin.ModelAdmin):
    actions = ('full_update', 'update',)

    def full_update(self, request, queryset):
        for package_index in queryset:
            package_index.update_package_list(full=True)

    def update(self, request, queryset):
        for package_index in queryset:
            if not package_index.updated_from_remote_at:
                package_index.update_package_list(full=True)
            else:
                package_index.update_package_list(full=False)


admin.site.register(PackageIndex, PackageIndexAdmin)


class PackageReleaseInline(admin.TabularInline):
    model = Release
    extra = 0
    fields = ('version', 'metadata_version', 'built',)
    readonly_fields = ('version', 'metadata_version', 'built',)


class PackageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'updated_from_remote_at', 'parsed_external_links_at',)
    search_fields = ('name',)
    inlines = (PackageReleaseInline,)
    actions = ('update_release_metadata', 'update_external_release_metadata',)

    def update_release_metadata(self, request, queryset):
        for package in queryset:
            package.update_release_metadata()

    def update_external_release_metadata(self, request, queryset):
        for package in queryset:
            package.update_external_release_metadata()


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ('package', 'version', 'built', 'is_from_external',)
    search_fields = ('package__name', 'version',)
    list_filter = ('built', 'is_from_external',)
    raw_id_fields = ('package',)


class DistributionAdmin(admin.ModelAdmin):
    list_display = ('package_name', 'release_version', 'path',
                    'is_from_external', 'filetype', 'pyversion', 'mirrored_at', 'updated_at',)
    search_fields = ('release__package__name', 'release__version', 'comment',)
    list_filter = ('filetype', 'pyversion', 'is_from_external',)
    raw_id_fields = ('release',)
    actions = ('mirror_distribution',)

    def package_name(self, obj):
        return obj.release.package.name
    package_name.admin_order_field = 'release__package__name'

    def release_version(self, obj):
        return obj.release.version
    release_version.admin_order_field = 'release__version'

    def mirror_distribution(self, request, queryset):
        for distribution in queryset:
            distribution.mirror_package(commit=True)


admin.site.register(Package, PackageAdmin)
admin.site.register(Release, ReleaseAdmin)
admin.site.register(Distribution, DistributionAdmin)
admin.site.register(Classifier)
