#!/usr/bin/python
from django.core.management.base import NoArgsCommand
from django.db import connection

import datetime
import crims.common.logger as logging


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        opts, args = getopt.getopt(sys.argv[1:], "clstu")

        logging.info('cron_sql_purge.py started @ %s' % str(datetime.datetime.now()))

        s = Sql()
        s.start()

        logging.info('cron_sql_purge.py finished @ %s' % str(datetime.datetime.now()))


class Sql(object):
    def __init__(self):
        pass

    def start(self):
        self.query("DELETE FROM facebook_spam_queue WHERE expire_at <= NOW()")
        self.query("DELETE FROM user_stream WHERE created_at <= NOW() + INTERVAL 7 DAY")
        self.query("DELETE FROM user_stat WHERE stat = ''")
        self.query("DELETE FROM city_move WHERE unit = ''")
        self.query("DELETE FROM city_unit WHERE unit = ''")
        self.query("DELETE FROM city_unit_progress WHERE unit = ''")

    # przesuwanie starych aukcji do archiwum
    # zamienic facebook_spam_log na _archive

    def query(self, query):
        cursor = connection.cursor()
        cursor.execute(query)
        connection.connection.commit()
