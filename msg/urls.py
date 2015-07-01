# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
# from django.conf import settings

urlpatterns = patterns('crims.msg.views',
                       url(r'^inbox/$', 'views.inbox', name='msg_inbox'),
                       url(r'^outbox/$', 'views.outbox', name='msg_outbox'),
                       url(r'^send/$', 'views.form', name='msg_send'),
                       )
