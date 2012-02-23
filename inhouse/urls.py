# -*- coding: utf-8 -*-

"""URL mapping for dlgicert module."""

from django.conf.urls import patterns, url, include

# lower-case urlpatterns is wanted, pylint: disable=C0103

urlpatterns = patterns(
    'inhouse.views',
    url(r'^$', 'index', name='home'),
    url(r'accounts/login/$', 'login',
            {'template_name': 'inhouse/login.html',}, name='login'),
    url(r'^profile/$', 'profile_details', name='profile'),
    url(r'^manager/', include('inhouse.views.manager_urls')),
)

urlpatterns += patterns(
    '',
    url(r'accounts/logout/$', 'django.contrib.auth.views.logout_then_login',
        name='logout'),
)
