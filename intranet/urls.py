# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

urlpatterns = patterns('crims.intranet.views',
                       url(r'^$', 'main.index', name='intranet'),

                       url(r'^jobs/(?P<job_id>\d+)/$', 'jobs.index', name='intranet_jobs'),
                       url(r'^jobs/$', 'jobs.index', name='intranet_jobs', kwargs={'job_id': None}),

                       url(r'^items/$', 'items.index', name='intranet_items'),

                       url(r'^import_cars/$', 'main.import_cars_from_gta', name='intranet_cars'),
                       url(r'^gen_promo_code/$', 'main.code', name='admin_stats_code'),
                       url(r'^social/$', 'main.social_notify', name='admin_social'),
                       url(r'^add_cars/$', 'main.add_cars', name='admin_stats_add_cars'),
                       )
