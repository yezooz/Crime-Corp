# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
# from django.conf import settings

urlpatterns = patterns('crims.job.views',
                       url(r'^robbery/$', 'robbery.index', {'tab': None, 'page': 0}, name='robbery'),
                       url(r'^robbery/(?P<page>\d+)/$', 'robbery.index', {'tab': None}, name='robbery'),
                       url(r'^robbery/(?P<page>\d+)/(?P<tab>\d+)/$', 'robbery.index', name='robbery'),
                       url(r'^special/$', 'special.index', name='special_job'),  # Special
                       )
