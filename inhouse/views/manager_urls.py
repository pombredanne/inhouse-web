# -*- coding: utf-8 -*-

"""URL mapping for manager views."""

from django.conf.urls.defaults import patterns, url

# lower-case urlpatterns is wanted, pylint: disable=C0103

urlpatterns = patterns(
    'inhouse.views.admin',
    #url(r'^$', 'index', name='certids_index'),
    #url(r'^(\d+)/$', 'details', name='certid_details'),
    url(r'^(\d+)/default_steps', 'default_steps', name='default_steps'),
    )
