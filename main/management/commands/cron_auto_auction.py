#!/usr/bin/python
import random

import simplejson as json
from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

import datetime
import crims.common.logger as logging
from crims.auction.models import Auction
from crims.item.models import Item

SELLER = User.objects.get(pk=1187)


class Command(NoArgsCommand):
    def __add_auction(self, car):

        if car.tier in (1, 2):
            days = 1
        elif car.tier in (3, 4):
            days = 2
        else:
            days = 3

        a = Auction()
        a.seller = SELLER
        a.title = car.name[:50]

        det = json.loads(car.details)
        if det.has_key('bhp'): det['hp'] = det['bhp']
        if not det.has_key('look'): det['look'] = 5

        a.details = json.dumps(
            {"engine": det['engine'], "product_type": "car", "look": det['look'], "hp": det['hp'], "year": det['year'],
             "product_id": int(car.id)})
        a.respect = car.respect
        a.start_price = car.price
        a.current_price = car.price
        a.end_at = datetime.datetime.now() + datetime.timedelta(days=days, hours=random.randint(0, 12),
                                                                minutes=random.randint(0, 60))
        a.save()

    def handle_noargs(self, **options):
        logging.info('cron_auto_auction.py started @ %s' % str(datetime.datetime.now()))

        CONFIG = {'6': 1, '5': 1, '4': 3, '3': 3, '2': 5, '1': 5}

        tier = {}
        for x in xrange(1, 7):
            tier[str(x)] = Item.objects.filter(is_active=True, is_premium=False, is_unique=False, tier=x,
                                               type='vehicle')

        for k, v in CONFIG.iteritems():
            if not tier.has_key(k) or len(tier[k]) == 0: continue
            [self.__add_auction(random.choice(tier[k])) for x in xrange(0, v)]

        logging.info('cron_auto_auction.py finished @ %s' % str(datetime.datetime.now()))
