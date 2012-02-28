# -*- coding: utf-8 -*-

"""URL mapping for manager views."""

from django.conf.urls.defaults import patterns, url

# lower-case urlpatterns is wanted, pylint: disable=C0103

urlpatterns = patterns(
    'inhouse.views.manager',
    url(r'^(\d+)/copy_project', 'copy_project', name='copy_project'),
    url(r'^(\d+)/default_steps', 'default_steps', name='default_steps'),
    )
