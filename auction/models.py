from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User

import datetime
import cPickle as pickle
from crims.userprofile.models import UserProfile


class AuctionManager(models.Manager):
    pass


class Auction(models.Model):
    seller = models.ForeignKey(User)
    buyer_id = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=50)
    details = models.CharField(max_length=255)
    respect = models.PositiveIntegerField(default=0)
    image_filename = models.CharField(max_length=100)

    start_price = models.PositiveIntegerField(default=1)
    current_price = models.PositiveIntegerField(default=1)
    is_for_credits = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)

    start_at = models.DateTimeField(auto_now_add=True)
    end_at = models.DateTimeField(default=datetime.datetime.now() + datetime.timedelta(days=3))

    objects = AuctionManager()

    class Meta:
        db_table = 'auction'
        verbose_name = 'Auction'

    def __unicode__(self):
        return 'Auction %s' % str(self.id)


class AuctionOfferManager(models.Manager):
    def get_by_user_auction(self, user, auction=None, auction_id=None):
        if auction is None and auction_id is None: return None

        try:
            if auction is not None:
                return self.get(auction=auction, buyer=user)
            else:
                return self.get(auction__id=auction_id, buyer=user)
        except AuctionOffer.DoesNotExist:
            return None

    def get_by_auction(self, auction=None, auction_id=None):
        if auction is None and auction_id is None: return None

        try:
            if auction is not None:
                return self.filter(auction=auction).order_by('-price').select_related()
            else:
                return self.filter(auction__id=auction_id).order_by('-price').select_related()
        except AuctionOffer.DoesNotExist:
            return ()


class AuctionOffer(models.Model):
    buyer = models.ForeignKey(User)
    auction = models.ForeignKey(Auction)
    price = models.PositiveIntegerField(default=0)
    max_price = models.PositiveIntegerField(default=0)
    is_refunded = models.BooleanField(default=False)

    auction_end_at = models.DateTimeField(default=datetime.datetime.now())
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AuctionOfferManager()

    class Meta:
        db_table = 'auction_offer'
        verbose_name = 'Auction Offer'

    def __unicode__(self):
        return '%s (offer)' % str(self.auction)

    def save(self):
        if self.created_at == self.updated_at:
            self.auction_end_at = Auction.objects.get(pk=self.auction.id).end_at
        super(AuctionOffer, self).save()  # Call the "real" save() method
