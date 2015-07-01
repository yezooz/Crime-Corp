import crims.common.logger as logging
import datetime
# import cPickle as pickle
from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from crims.gang.models import Gang
from crims.userprofile.models import UserProfile


class MsgManager(models.Manager):
    def get_by_user(self, user, start=0, end=None, catalog='inbox'):
        if catalog == 'inbox':
            msgs = self.filter(receiver=user)
        else:
            msgs = self.filter(sender=user, is_deleted=False)

        msgs = msgs.filter(is_spam=False, is_invite=False).order_by('-sent_at')

        # TODO: load more in background
        # if end is None:
        # 	return msgs[start:start+settings.DEFAULT_MSGS_PER_PAGE]
        # else:
        # 	return msgs[start:end]

        return msgs

    def get_unread_count(self, user, last_id):
        return self.filter(receiver=user, is_spam=False, is_invite=False, pk__gt=last_id).count()

    def get_gang_unread_count(self, user, last_id):
        return self.filter(receiver=user, is_spam=False, is_invite=False, is_gang=True, pk__gt=last_id).count()


class MsgSendManager(models.Manager):
    def send_to(self, sender, receiver, msg):
        try:
            user = User.objects.get(username__iexact=receiver)
            return self._send_to_user(sender, user, msg)
        except User.DoesNotExist:
            try:
                gang = Gang.objects.get_by_name(name=receiver)
                return self._send_to_gang(sender, gang, msg)
            except Gang.DoesNotExist:
                pass

        logging.debug('No msg receiver %s' % receiver)
        return False

    def _send_to_user(self, sender, user, txt, gang=False):
        msg = Msg()
        msg.sender = sender
        msg.receiver = user
        if txt.startswith('@'):
            msg.is_public = False
        else:
            msg.is_public = True
        msg.content = txt

        msg.is_gang = gang
        msg.save()

        logging.info('sent message from %s to %s' % (sender, user))
        return True

    def _send_to_gang(self, sender, gang, msg):
        for member in gang.members:
            user = User.objects.get(username__iexact=member)
            self._send_to_user(sender, user, msg, gang=True)
        return True


class Msg(models.Model):
    """Internal msg"""

    sender = models.ForeignKey(User, related_name='sender')
    receiver = models.ForeignKey(User, related_name='receiver')
    content = models.CharField(max_length=255)

    is_gang = models.BooleanField(default=False)
    is_invite = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    is_notified = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    send = MsgSendManager()
    objects = MsgManager()

    class Meta:
        db_table = 'msg'

    def __unicode__(self):
        return "Msg from %s to %s @ %s" % (self.sender, self.receiver, str(self.sent_at))

    def as_spam(self):
        self.is_spam = True
        self.save()
