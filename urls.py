# -*- coding: utf-8 -*-

"""Global URL routing."""

from django.conf.urls import patterns, url, include

from django.contrib import admin
admin.autodiscover()


js_info_dict = {
    'packages': ('inhouse',),
}

urlpatterns = patterns(
    '',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    (r'', include('inhouse.urls', namespace='inhouse')),
)
