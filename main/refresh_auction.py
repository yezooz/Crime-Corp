#!/usr/bin/python
import urllib
import re
import os
import getopt

import simplejson as json

import sys
import datetime

sys.path.append(os.path.dirname(__file__) + "../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'crims.settings'

from django.db import models, connection
from django.conf import settings
import crims.common.logger as logging
from crims.engine.engine import Engine
from crims.common.models import DummyRequest
from crims.auction.models import Auction as AuctionModel, AuctionOffer
from crims.item.models import Item, Garage
from crims.userprofile.models import UserProfile


class Auction(object):
    def __init__(self):
        pass

    def start(self):
        auctions = AuctionModel.objects.filter(end_at__lt=datetime.datetime.now, is_refunded=False)

        for self.auction in auctions:
            logging.info("Finishing auction of %s" % self.auction.title)

            self.bids = AuctionOffer.objects.get_by_auction(auction=self.auction)
            self.finish_auction(self.auction.id)

    def finish_auction(self, auction_id):
        # Refund
        if len(self.bids) == 0:
            profile = UserProfile.objects.get_by_id(self.auction.seller.id)
            if self.auction.seller.id != 1187:
                self.give_item(profile)

            self.auction.is_refunded = True
            self.auction.save()
            self.engine = Engine(DummyRequest(self.auction.seller.id))
            self.engine.stream.post('auction_not_sold', self.auction.title)
            self.engine.stream.trigger('auction_not_sold')
            return True

        # Buyer
        bid = self.bids[0]
        profile = UserProfile.objects.get_by_id(bid.buyer.id)
        profile.earn('cash', bid.max_price - bid.price)

        bid.is_refunded = True
        bid.save()

        self.engine = Engine(DummyRequest(bid.buyer.id))
        self.engine.stream.post('auction_won', self.auction.title, fb='%s|%simages/cars/m/%s' % (
        self.auction.title, settings.MEDIA_URL, self.auction.image_filename))
        self.engine.stream.trigger('auction_won')

        if self.give_item(profile) is False:  # pass item to the winner
            return False

        # Seller
        s_profile = UserProfile.objects.get_by_id(self.auction.seller.id)
        s_profile.earn('cash', self.auction.current_price)
        self.engine.stream.post('auction_sold', '|'.join((self.auction.title, profile.username, str(bid.price))),
                                fb='%s|%simages/cars/m/%s' % (
                                self.auction.title, settings.MEDIA_URL, self.auction.image_filename),
                                user_id=self.auction.seller.id)
        self.engine.stream.trigger('auction_sold')

        self.auction.is_refunded = True
        self.auction.buyer_id = profile.user.id
        self.auction.save()

        if len(self.bids) == 1: return True

        for bid in self.bids[1:]:
            if bid.is_refunded == True: continue

            profile = UserProfile.objects.get_by_id(bid.buyer.id)
            profile.earn('cash', bid.max_price)
            bid.is_refunded = True
            bid.save()
            self.engine.stream.post('auction_lost', self.auction.title, user=bid.buyer)
            self.engine.stream.trigger('auction_lost')

    def give_item(self, profile):
        auction_details = json.loads(self.auction.details)
        if auction_details['product_type'] != 'car':
            logging.warning("give item / product type: %s" % auction_details['product_type'])
            return False

        car = Item.objects.get_by_id(auction_details['product_id'])
        if car is None:
            logging.warning("give item / unknown car with id: %s" % auction_details['product_id'])
            return False

        garage = Garage.objects.get_by_user(user=profile.user)
        garage.buy_item(car.id)

        profile.next_total_recalc = True
        profile.save()
        return True


if __name__ == '__main__':
    a = Auction()
    a.start()
