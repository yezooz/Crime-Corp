from django.conf.urls.defaults import *

urlpatterns = patterns('crims.gang.views',
                       url(r'^$', 'show.index', {}, name='gang'),
                       )
