# -*- coding: utf-8 -*-
import simplejson as json
from django.utils.translation import ugettext as _

import datetime
import crims.common.logger as logging
from crims.auction.models import Auction as AuctionModel, AuctionOffer
from crims.item.models import Item, Garage


class Auction(object):
    def __init__(self, engine, tab='auction'):
        self.engine = engine

        if tab == 'auction':
            self.items = AuctionModel.objects.filter(end_at__gte=str(datetime.datetime.now())[0:19]).order_by('end_at')
        elif tab == 'bidding':
            self.items = AuctionOffer.objects.filter(buyer=self.engine.user.user, is_refunded=False).order_by(
                'auction_end_at')
        elif tab == 'bidded':
            self.items = AuctionOffer.objects.filter(buyer=self.engine.user.user, is_refunded=True).order_by(
                '-auction_end_at')

    def get_auction(self, auction_id):
        try:
            item = AuctionModel.objects.get(pk=auction_id)
        except AuctionModel.DoesNotExist:
            return None

        self.auction = item
        self.details = json.loads(item.details)
        self.bids = AuctionOffer.objects.get_by_auction(auction=item)
        self.item = Item.objects.get_by_id(self.details['product_id'])

        return self.item

    def bid(self, item_id, amount):
        # Validation
        try:
            auction_id = int(item_id)
            amount = int(amount)
        except KeyError:
            return None
        except ValueError:
            return None
        except TypeError:
            return None

        if self.get_auction(auction_id) is None:
            return None

        # Too old auction?
        if datetime.datetime.now() > self.auction.end_at:
            self.engine.log.message(message=_("Auction ended"))
            return False

        # Your auction?
        if self.auction.seller == self.engine.user.user:
            self.engine.log.message(message=_("Can't bid on your auction of course :)"))
            return False

        # Less then curren_price?
        if amount <= self.auction.current_price:
            self.engine.log.message(
                message=_("Offer more than $%(amount)d") % {'amount': int(self.auction.current_price)})
            return None

        # Have space in the garage?
        if self.engine.user.profile.max_cars == len(Garage.objects.get_by_user(user=self.engine.user.user).items):
            self.engine.log.message(message=_("No space left in the garage. Other your cars will park on the street."))

        # Highest offer?
        if len(self.bids) == 0:
            if self.get_bid(self.auction.start_price, amount) is not False:
                self._outbid(self.auction.start_price)
                return True
            return False

        highest_bid = self.bids[0]

        # Podnies wlasny udzial
        if highest_bid.buyer == self.engine.user.user:
            if self.block_money(amount - highest_bid.max_price) is not False:
                highest_bid.max_price = amount
                highest_bid.save()

                self.engine.log.message(
                    message=_("Your current maximum offer is %(max)d") % {'max': highest_bid.max_price})
                return True
            return False

        # Automatycznie podbicie
        if amount > highest_bid.price and amount <= highest_bid.max_price:
            if self.get_bid(amount, amount) is False: return False

            if amount == highest_bid.max_price:
                highest_bid.price = highest_bid.max_price
                highest_bid.save()
            else:
                highest_bid.price = amount + 1
                highest_bid.save()

            self.my_offer.price = amount
            self.my_offer.max_price = amount
            self.my_offer.save()

            self.auction.current_price = highest_bid.price
            self.auction.save()

            self.engine.log.message(message=_("You have been outbidded"))
            return True

        # Przebijam
        if amount > highest_bid.max_price:
            if self.get_bid(amount, amount) is False: return False

            highest_bid.price = highest_bid.max_price
            highest_bid.save()

            self.my_offer.price = highest_bid.max_price + 1
            self.my_offer.max_price = amount
            self.my_offer.save()

            self.auction.current_price = self.my_offer.price
            self.auction.save()

            self.engine.log.message(message=_("Your offer is currently the highest"))
            if highest_bid.buyer != self.my_offer.buyer:
                self.engine.stream.post('auction_outbid', title_replace='%s' % self.auction.title,
                                        user=highest_bid.buyer)
            return True

        logging.warning("Unknown bid option")
        return False

    def get_bid(self, amount, max_amount):
        self.my_offer = AuctionOffer.objects.get_by_user_auction(self.engine.user.user, auction=self.auction)
        if self.my_offer is not None:
            if not self.block_money(max_amount - self.my_offer.max_price): return False
            return self.my_offer

        if not self.block_money(max_amount): return False

        ao = AuctionOffer()
        ao.buyer = self.engine.user.user
        ao.auction = self.auction
        ao.price = amount
        ao.max_price = max_amount
        ao.save()

        self.my_offer = ao
        return self.my_offer

    def _outbid(self, amount):
        self.auction.current_price = amount
        self.auction.save()

    def block_money(self, amount):
        if amount <= 0:
            logging.warning("%s: tried to block <= 0 amount" % (self.engine.user.user))
            self.engine.log.message(message=_("You highest offer is higher"))
            return False

        if self.engine.user.profile.has_enough('cash', amount):
            self.engine.user.profile.cash -= amount
            self.engine.user.profile.save()

            logging.debug("%s: blocked $%d for auction" % (self.engine.user.user, amount))
            return True
        self.engine.log.message(message=_("Not enough cash"))
        return False
