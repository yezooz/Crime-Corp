#!/usr/bin/python
# coding=utf-8
import os
import getopt

import sys
import time
import datetime

sys.path.append('/home/marek/')
sys.path.append('/home/marek/crims/')
# sys.path.append('/Users/marekmikuliszyn/Sites/')
# sys.path.append('/Users/marekmikuliszyn/Sites/crims/')
os.environ["DJANGO_SETTINGS_MODULE"] = 'crims.settings'

import daemon, lockfile, random, md5, MySQLdb
import crims.common.logger as logging
from django.conf import settings
# from django.db import connection, transaction
from django.core.cache import cache
from django.core.urlresolvers import reverse
import simplejson as json

from crims.engine.engine import Engine
from crims.common.models import DummyRequest
from crims.userprofile.models import UserProfile
from crims.city.models import CityUnit, CityUnitProgress, MapMove, MapMoveGroup, Product, ProductPrice
from crims.msg.models import Msg

from crims.main.refresh_auction import Auction
from crims.main.refresh_city import CityRefresh


class Refresh(object):
    def __init__(self):
        try:
            self.every_req = [self.unit, self.task]
            self.every_1 = [self.auction]
            self.every_5 = []
            self.every_15 = [self.msg_notify]
        except Exception, e:
            logging.error('Daemon error %s' % e)

    def start(self):
        c = 1
        while True:
            print '->', datetime.datetime.now()

            for act in self.every_req:
                act()

            if c % 6 == 0:
                for act in self.every_1:
                    act()

            if c % 30 == 0:
                for act in self.every_5:
                    act()

            if c % 90 == 0:
                for act in self.every_15:
                    act()

            print '<-', datetime.datetime.now()

            if c == 3600: c = 0
            time.sleep(10)
            c += 1

    # --- Task
    def task(self):
        self._task()

    def _task(self):
        def execute(engine, module, method, params):
            engine.register(module)
            engine.__dict__[module].__getattribute__(method)(*params)

        available_actions = ('engine', 'sql', 'city')

        crs = query('SELECT id, user_id, task, comment, source FROM task WHERE run_at <= NOW() ORDER BY run_at')
        rows = crs.fetchall()

        for row in rows:
            # Archive
            query(
                """INSERT INTO archive.crims_task_archive (user_id, task, comment, source) VALUES ("%s", "%s", "%s", "%s")""" % (
                row[1], row[2], row[3], row[4]), True)

            if row[4] == 'sql':
                sql(task)
                continue

            if row[4] == 'city':
                city_id = row[2]

                cache.delete('city_building_%s' % city_id)
                profile = UserProfile.objects.get_by_id(user_id=row[1])
                if profile is None: continue

                r = CityRefresh(profile, city_id)
                r.do_refresh()
                continue

            engine = Engine(DummyRequest(row[1]))

            try:
                module, method, params = row[2].split('|')
                params = params.split(',')

                execute(engine, module, method, params)
            except ValueError:
                logging.error("Error executing wait job %s for %s" % (row[2], engine.user.user))

        if len(rows) > 0: query("DELETE FROM task WHERE id IN (%s)" % ','.join(["%s" % str(x[0]) for x in rows]), True)

    # --- Unit
    def unit(self):
        self._unit()

    def _unit(self):
        self._unit_build()
        self._unit_move()

    def _unit_build(self):
        qualify_tasks = query(
            "SELECT user_id, city_id FROM city_unit_progress WHERE next_at<=NOW() + INTERVAL 1 MINUTE AND unit!=''")

        for task in qualify_tasks.fetchall():

            engine = Engine(DummyRequest(task[0]))
            engine.city.id = task[1]
            engine.city.set_action_type('unit')

            for unit in engine.city.city_unit_progress.units:
                if unit[1] > int(time.time()): continue

                engine.city.city_unit.add_unit(unit[0])

                engine.stream.post('unit_hired', '%s|<a href="%s">%s</a>' % (
                engine.city.all_unit[str(unit[0])].name, reverse('city_enter', args=[task[1]]),
                engine.city.city_map.name))
                logging.debug('%s unit hired' % engine.user.user)

            new_list = [x for x in engine.city.city_unit_progress.units if x[1] > int(time.time())]
            engine.city.city_unit_progress.unit = json.dumps(new_list)
            if len(new_list) > 0:
                engine.city.city_unit_progress.next_at = datetime.datetime.fromtimestamp(min([x[1] for x in new_list]))
                engine.city.city_unit_progress.save()
            else:
                engine.city.city_unit_progress.delete()

    def _unit_move(self):
        qualify_tasks = query(
            "SELECT user_id, unit FROM city_move WHERE next_at<=NOW() + INTERVAL 1 MINUTE AND unit!=''")

        for task in qualify_tasks.fetchall():

            for group in json.loads(task[1]):
                if group[3] > int(time.time()): continue

                units_move = MapMove.objects.get_by_user(user_id=task[0])
                units_move_group = MapMoveGroup.objects.get_by_id(group[2])

                from_units = CityUnit.objects.get_by_user(city_id=group[0], user_id=task[0])
                to_units = CityUnit.objects.get_by_user(city_id=group[1], user_id=task[0])

                engine = Engine(DummyRequest(task[0]))
                engine.city.id = group[1]
                engine.city.set_action_type('unit')

                try:
                    for unit_id, unit_cnt in units_move_group.units.iteritems():
                        to_units.add_unit(unit_id, unit_cnt)
                        from_units.rem_unit(unit_id, unit_cnt)

                        engine.stream.post('unit_moved', '%s|<a href="%s">%s</a>' % (
                        engine.city.UNIT[engine.city.all_unit[str(unit_id)].name],
                        reverse('city_enter', args=[group[1]]), engine.city.city_map.name))
                        logging.debug('%s unit moved' % engine.user.user)

                    units_move_group.delete()

                    new_list = [x for x in units_move.units if x[3] > int(time.time())]
                    units_move.unit = json.dumps(new_list)
                    if len(new_list) > 0:
                        units_move.next_at = datetime.datetime.fromtimestamp(min([x[3] for x in new_list]))
                        units_move.save()
                    else:
                        try:
                            units_move.delete()
                        except AssertionError:
                            continue

                except AttributeError:
                    logging.error(
                        'Problem with moving units. %s, %s. AttErr' % (str(units_move), str(units_move_group)))

    # --- Stat recalc
    def stat_recalc(self):
        pass

    def _stat_recalc(self):
        pass

    # --- Auction
    def auction(self):
        self._auction()

    def _auction(self):
        a = Auction()
        a.start()

    # --- Msg
    def msg_notify(self):
        from django.template import loader, Context

        for msg in Msg.objects.filter(is_notified=False)[:50]:
            if not msg.receiver.email.endswith('@madfb.com'):
                profile = UserProfile.objects.get_by_id(msg.receiver.id)
                if profile.pref_lang == 'pl':
                    title = 'Nowa wiadomość na Crime Corp'
                else:
                    title = 'New message on Crime Corp'
                    profile.pref_lang = 'en'

                t = loader.get_template('email/%s/msg.txt' % profile.pref_lang)
                c = Context({
                    msg: msg.content,
                })

                self._send_mail([msg.receiver.email], title, t.render(c))

            msg.is_notified = True
            msg.save()

    def _send_mail(self, recipients, subject, message=''):
        if settings.LOCAL: print 'mail sent to ', recipients, ' subject: ', subject, ' msg: ', message

        if isinstance(recipients, basestring):
            recipients = ",".join(recipients)

        from django.core.mail import EmailMessage

        msg = EmailMessage(subject, message, 'Crime Corp <robot@madfb.com>', recipients)
        msg.content_subtype = "html"  # Main content is now text/html

    # msg.send()

    # --- Product price
    def product_price(self):
        pass

    def _product_price(self):
        for prod in Product.objects.get_all():
            pp = ProductPrice.objects.get_by_type(str(prod.type))

            # archive
            query(
                """INSERT INTO archive.crims_product_price_archive(`type`, `source`, `price`, `created_at`)
                 VALUES('%s', '%s', '%s', '%s', NOW())""" %
                (str(pp.type), str(pp.source), int(pp.price)), True
            )

            # new_price = []
            # for price in pp.prices:
            # new_price.append(random.randint(int(prod.min_sell_price), int(prod.max_sell_price)))
            # pp.price = new_price.join('|')
            pp.valid_string = md5.new(
                "%d+%s+%d" % (dp.price, str(datetime.datetime.now()), random.randint(1, 1000))).hexdigest()
            pp.save()


def query(query, w_cmt=False):
    db = MySQLdb.connect(user=settings.DATABASE_USER, db=settings.DATABASE_NAME, passwd=settings.DATABASE_PASSWORD,
                         host='')
    cursor = db.cursor()
    cursor.execute(query)

    if w_cmt:
        db.commit()
    return cursor


if __name__ == '__main__':
    r = Refresh()
    r.start()
