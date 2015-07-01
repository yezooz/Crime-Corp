from django.conf import settings
from django.http import HttpResponseRedirect

from crims.common.models import Task
from crims.helpers.slughifi import slughifi
from crims.userprofile.models import UserProfile


class Engine(object):
    def __init__(self, request, source='default'):
        self.request = request
        self.source = source
        self.settings = settings
        self.pref_lang = request.LANGUAGE_CODE[:2]

        self.register('log')

        # registered only default modules
        if not request.user.is_anonymous():
            self.register('user')
            self.register('stream')
            self.register('msg')
            self.register('city')

            self.city.set_id()
            self.user.cron_actions()
        else:
            self.user = None

    def login_as_someone(self, request, user):
        from django.contrib.auth import login, get_backends
        from django.contrib.auth.models import User

        backend = get_backends()[0]
        user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
        login(request, user)

    def register(self, name, *args, **argv):
        if self.__dict__.has_key(name): return

        try:
            plug = __import__('modules.%s' % name, globals(), locals(), [name.capitalize(), ], -1)
            self.__dict__[name] = plug.__dict__[name.capitalize()](self, *args, **argv)
        except ImportError, e:
            raise e
        except KeyError, e:
            raise e

    def unregister(self, name):
        try:
            del self.__dict__[name]
        except KeyError, e:
            raise e

    def slughifi(self, value):
        return slughifi(value)

    def query(self, query, param=None):
        from django.db import connection

        cursor = connection.cursor()
        if param is None:
            return cursor.execute(query)
        else:
            return cursor.execute(query, param)

    def redirect(self, page):
        return HttpResponseRedirect(page)

    def add_task(self, source='engine', task='', comment=''):
        t = Task()
        t.user_id = self.user.user.id
        t.source = source
        t.task = task
        t.comment = comment
        t.save()

    def send_mail(self, recipients, subject, message='', mime='text'):
        if settings.LOCAL: print 'mail sent to ', recipients, ' subject: ', subject, ' msg: ', message

        if isinstance(recipients, basestring):
            recipients = ",".join(recipients)

        if mime == 'html':
            from django.core.mail import EmailMessage

            msg = EmailMessage(subject, message, 'Crime Corp <robot@madfb.com>', recipients)
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send()
        else:
            from django.core.mail import send_mail

            send_mail(subject, message, 'Crime Corp <robot@madfb.com>', recipients, fail_silently=True)
