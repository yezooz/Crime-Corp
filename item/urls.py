# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
# from django.conf import settings

urlpatterns = patterns('crims.item.views',
                       url(r'^shop/$', 'shop.index', {'tab': 'weapon'}, name='shop'),
                       url(r'^shop/(?P<tab>\w+)/$', 'shop.index', name='shop'),

                       url(r'^hooker/$', 'hooker.index', name='hooker'),

                       # url(r'^item/details/(?P<item_type>\w+)/(?P<item_id>\d+)/$', 'shop.details', name='item_details'),
                       url(r'^item/activate/(?P<item_id>\d+)/$', 'shop.activate', name='activate_item'),
                       url(r'^item/deactivate/(?P<item_id>\d+)/$', 'shop.deactivate', name='deactivate_item'),

                       url(r'^garage/$', 'garage.index', name='garage'),
                       url(r'^garage/(?P<item_id>\d+)/$', 'garage.index', name='garage'),
                       url(r'^garage/show/(?P<item_id>\d+)/$', 'garage.details', name='garage_details'),
                       url(r'^garage/sell/(?P<item_id>\d+)/$', 'garage.sell', name='garage_sell'),
                       )
