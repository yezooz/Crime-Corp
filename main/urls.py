# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
# from django.conf import settings

urlpatterns = patterns('crims.main.views',
                       url(r'^bank/$', 'bank.index', name='bank'),
                       url(r'^prison/$', 'prison.index', name='prison'),

                       # payments
                       url(r'^payment/$', 'payment.index', name='payment'),
                       url(r'^payment_country_part/$', 'payment.country_payment_part', name='payment_country_part'),
                       url(r'^payment/process/srpoints/$', 'payment.srpoints', name='payment_process_srpoints',
                           kwargs={'site': 'fb'}),
                       url(r'^payment/process/www/$', 'payment.srpoints', name='payment_process_srpoints',
                           kwargs={'site': 'www'}),
                       url(r'^payment/process/offerpal/$', 'payment.offerpal', name='payment_process_offerpal',
                           kwargs={'site': 'fb'}),
                       url(r'^payment/process/offerpal_www/$', 'payment.offerpal', name='payment_process_offerpal',
                           kwargs={'site': 'www'}),
                       url(r'^payment/process/webtopay/$', 'payment.webtopay', name='payment_process_webtopay'),
                       url(r'^payment/process/furtumo/$', 'payment.furtumo', name='payment_process_furtumo'),

                       url(r'^premium/$', 'payment.premium', name='premium'),

                       # stats
                       url(r'^stats/by_respect/$', 'stat.by_respect', name='stats_by_respect', kwargs={'page_no': 1}),
                       url(r'^stats/by_respect/(?P<page_no>\d+)/$', 'stat.by_respect', name='stats_by_respect'),
                       url(r'^stats/by_population/$', 'stat.by_population', name='stats_by_population',
                           kwargs={'page_no': 1}),
                       url(r'^stats/by_population/(?P<page_no>\d+)/$', 'stat.by_population',
                           name='stats_by_population'),
                       url(r'^stats/search/$', 'stat.search', name='stat_search', kwargs={'page_no': 1}),
                       )
