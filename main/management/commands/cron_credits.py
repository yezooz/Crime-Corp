#!/usr/bin/python
from django.core.management.base import NoArgsCommand
from django.db import connection
import simplejson as json

import datetime
import crims.common.logger as logging
from crims.engine.engine import Engine
from crims.common.models import DummyRequest
import crims.common.logger as logging


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        logging.info('cron_credits.py started @ %s' % str(datetime.datetime.now()))

        fc = FreeCredit()
        fc.start()

        logging.info('cron_credits.py finished @ %s' % str(datetime.datetime.now()))


class FreeCredit(object):
    def __init__(self):
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, stat FROM user_stat WHERE created_at=CURRENT_DATE() AND stat!=''")
        self.qualify_users = cursor.fetchall()

    def start(self):
        for user in self.qualify_users:
            stats = json.loads(user[1])
            if not stats.has_key('robbery_done') or \
                            stats['robbery_done'] < 10:
                logging.debug('%d not qualify for free credit' % user[0])
                continue

            engine = Engine(DummyRequest(user[0]))
            engine.user.profile.credit += 1
            engine.user.profile.save()

            engine.stream.post('credit_awarded', 1)
            logging.debug('%d awarded with free credit' % user[0])
