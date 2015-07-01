#!/usr/bin/python
from django.core.management.base import NoArgsCommand
from django.db import connection

import datetime
import crims.common.logger as logging
from crims.engine.engine import Engine
from crims.common.models import DummyRequest
from crims.userprofile.models import UserPerDay
import crims.common.logger as logging


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        logging.info('cron_cash_per_day.py started @ %s' % str(datetime.datetime.now()))

        cpd = CashPerDay()
        cpd.start()

        logging.info('cron_cash_per_day.py finished @ %s' % str(datetime.datetime.now()))


class CashPerDay(object):
    def __init__(self):
        pass

    def start(self):
        for row in UserPerDay.objects.get_sums():
            try:
                engine = Engine(DummyRequest(row[0]))
                engine.user.profile.earn('cash', int(row[1]))
                engine.stream.post('daily_income', str(row[1]))
            except TypeError:
                return None

    # ---

    def remove_invalid(self):
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM user_per_day WHERE is_limited=1 AND valid_until<='%s'" % str(datetime.datetime.now())[:19])
