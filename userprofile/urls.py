# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
# from django.conf import settings

urlpatterns = patterns('crims.userprofile.views',
                       url(r'^$', 'profile', name='profile', kwargs={'username': None}),
                       url(r'^public/(?P<username>[\w\-_]{1,})/$', 'profile', name='profile'),
                       url(r'^edit/$', 'edit', name='profile_edit'),

                       url(r'^skills/$', 'skills', name='skills'),
                       url(r'^skills/do_skill/(?P<skill_type>[\w_]{1,})/$', 'do_skill', name='do_skill'),

                       url(r'^wall/delete/(?P<stream_id>\d+)/$', 'wall_stream_delete', name='wall_stream_delete'),
                       url(r'^stream/delete/(?P<stream_id>\d+)/$', 'stream_delete', name='stream_delete'),
                       )
