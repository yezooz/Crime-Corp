from django.conf.urls.defaults import *
# from django.conf import settings

urlpatterns = patterns('',
                       (r'^i18n/', include('django.conf.urls.i18n')),

                       url(r'^$', 'crims.main.views.index.index', name='home'),
                       (r'^accounts/', include('crims.registration.urls')),
                       (r'^profiles/', include('crims.userprofile.urls')),

                       (r'^main/', include('crims.main.urls')),
                       (r'^auction/', include('crims.auction.urls')),
                       (r'^city/', include('crims.city.urls')),
                       (r'^job/', include('crims.job.urls')),
                       (r'^item/', include('crims.item.urls')),
                       (r'^gang/', include('crims.gang.urls')),
                       (r'^msg/', include('crims.msg.urls')),
                       (r'^intranet/', include('crims.intranet.urls')),

                       url(r'^maintance/$', 'crims.main.views.index.maintance', name="maintance"),
                       url(r'^ping_on_install/$', 'crims.main.views.index.ping_on_install'),
                       url(r'^ping_on_uninstall/$', 'crims.main.views.index.ping_on_uninstall'),

                       # Secret
                       (r'^login_as_someone/$', 'crims.main.views.index.login_as_someone'),
                       )
