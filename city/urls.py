# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
# from django.conf import settings

urlpatterns = patterns('crims.city.views',
                       # MAP
                       url(r'^$', 'city.index', name='city_map'),
                       url(r'^enter/(?P<city_id>\d+)/$', 'city.enter_city', name='city_enter'),
                       url(r'^city_map_frame/$', 'city.map_frame', name='city_map_frame'),

                       url(r'^units/$', 'unit.index', name='city_units'),
                       url(r'^units/move/$', 'unit.move', name='city_units_move', kwargs={'city_id': None}),
                       url(r'^units/move/(?P<city_id>\d+)/$', 'unit.move', name='city_units_move'),
                       url(r'^units/move/cancel/(?P<move_id>\d+)/$', 'unit.move_cancel', name='city_units_move_cancel'),
                       url(r'^units/cancel/(?P<order_id>\d+)/$', 'unit.cancel', name='city_units_cancel'),

                       # Production
                       url(r'^production/$', 'production.index', name='production'),
                       url(r'^production/set/$', 'production.set', name='production_set'),

                       # Tribute
                       url(r'^tribute/$', 'tribute.index', name='tribute'),
                       )
