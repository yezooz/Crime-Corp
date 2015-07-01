#!/usr/bin/python
from django.core.management.base import NoArgsCommand
from django.db import connection
from django.core.cache import cache

import datetime
from crims.userprofile.models import UserProfile, Bonus, UserBonus
import crims.common.logger as logging


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        logging.info('cron_bonus.py started @ %s' % str(datetime.datetime.now()))

        b = Bonus()
        b.start()

        logging.info('cron_bonus.py finished @ %s' % str(datetime.datetime.now()))


class Bonus(object):
    def __init__(self):
        self.profile = None

    def start(self):
        uid_list = self.get_to_update_list()

        for uid in uid_list:
            self.per_user(uid)

        # delete memcached keys
        [cache.delete('user_%s' % x) for x in uid_list]

    def per_user(self, uid):
        self.profile = UserProfile.objects.get_by_id(uid)
        self.user_bonuses = UserBonus.objects.get_by_user(user_id=uid)
        for subject, bonuses in self.user_bonuses.iteritems():
            for ub in bonuses:
                if not ub.is_active or ub.end_at > datetime.datetime.now(): continue
                ub.deactivate()

    def get_to_update_list(self):
        cursor = connection.cursor()
        cursor.execute(
            "SELECT DISTINCT user_id FROM user_bonus WHERE end_at <= '%s'" % str(datetime.datetime.now())[:19])
        return ["%s" % str(x[0]) for x in cursor.fetchall()]
