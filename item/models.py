import simplejson as json
from django.conf import settings
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User

import crims.common.logger as logging
import datetime
import math
import cPickle as pickle
from crims.userprofile.models import UserProfile


class ItemManager(models.Manager):
    def get_by_id(self, item_id):
        key = 'item_%s' % item_id
        item = cache.get(key)

        if item is not None:
            return pickle.loads(str(item))

        try:
            item = self.get(pk=item_id)
        except Item.DoesNotExist:
            logging.warning('Item not found. ID:%s' % str(item_id))
            return None

        cache.set(key, pickle.dumps(item))
        return item

    def get_list(self, item_list):
        # TODO: z czasem pomyslec o optymalizacji, poki co starczy
        items = []

        for item in item_list:
            items.append(self.get_by_id(item))

        return items

    def get_all(self):
        key = 'items'
        item = cache.get(key)

        if item is not None:
            return pickle.loads(str(item))

        item = self.filter(is_active=True)

        cache.set(key, pickle.dumps(item))
        return item

    def get_by_type(self, name, select_list=None):
        if name in settings.INVENTORY_TYPES:

            if select_list is not None:
                new_items = []
                items = self.filter(type=name).order_by('-price', 'name').in_bulk(select_list)

                for item in select_list:
                    try:
                        new_items.append(items[long(item)])
                    except KeyError:
                        continue

                return new_items
            else:
                return self.filter(type=name)
        else:
            return None


class Item(models.Model):
    type = models.CharField(max_length=15)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    tier = models.PositiveSmallIntegerField(default=1)
    details = models.TextField()
    req_attack = models.IntegerField(default=0)

    attack = models.PositiveIntegerField(default=0)
    defense = models.PositiveIntegerField(default=0)
    respect = models.PositiveIntegerField(default=0)

    price = models.PositiveIntegerField(default=0)
    credit = models.PositiveSmallIntegerField(default=0)
    in_shop = models.BooleanField(default=True)

    image_filename = models.CharField(max_length=255)
    is_premium = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = ItemManager()

    class Meta:
        db_table = 'item'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __unicode__(self):
        return self.name


class InventoryManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_inventory_%s' % user.id
        elif user_id is not None:
            key = 'user_inventory_%s' % user_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user)
            elif user_id is not None:
                item = self.get(user__id=user_id)
            else:
                logging.warning('Inventory not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except Inventory.DoesNotExist:
            item = Inventory()
            item.user = user
            item.item = ''
            item.active = ''
            item.save()

        cache.set(key, pickle.dumps(item))
        return item

    # PRZYKLAD!
    def get_related_by_user(self, user=None, user_id=None, field='actives', filter=None):
        items_list = []
        if filter is None:
            [items_list.extend(x) for x in self.get_by_user(user, user_id).__dict__[field].itervalues()]
        else:
            items_list.append(self.get_by_user(user, user_id).__dict__[field][filter])

        for item in items_list:
            pass


class Inventory(models.Model):
    user = models.ForeignKey(User)
    item = models.TextField(blank=True)
    active = models.TextField(blank=True)

    objects = InventoryManager()

    class Meta:
        db_table = 'user_inventory'
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'

    def save(self):
        super(Inventory, self).save()  # Call the "real" save() method
        key = 'user_inventory_%s' % self.user.id
        cache.set(key, pickle.dumps(self))

    def __unicode__(self):
        return self.item

    def __getattr__(self, name):
        if name == 'items':
            return [x for x in self.item.split(',') if len(x) > 0]
        elif name == 'actives':
            return [x for x in self.active.split(',') if len(x) > 0]
        else:
            return self.__getattribute__(name)

    def buy_item(self, item_id):
        items = self.items[:]
        items.append(item_id)
        self.item = ','.join(items)

        self.save()

    def sell_item(self, item_id):
        items = self.items[:]
        del items[items.index(str(item_id))]
        self.item = ','.join(items)

        self.save()

    def activate(self, item_id):
        # remove from items
        items = self.items[:]
        del items[items.index(str(item_id))]
        self.item = ','.join(items)

        # add to actives
        items = self.actives[:]
        items.append(str(item_id))
        self.active = ','.join(items)

        self.save()

    def deactivate(self, item_id):
        # remove from actives
        items = self.actives[:]
        del items[items.index(str(item_id))]
        self.active = ','.join(items)

        # add back to items
        items = self.items[:]
        items.append(str(item_id))
        self.item = ','.join(items)

        self.save()


class GarageManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_garage_%s' % user.id
        elif user_id is not None:
            key = 'user_garage_%s' % user_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user)
            elif user_id is not None:
                item = self.get(user__id=user_id)
            else:
                logging.warning('Garage not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except Garage.DoesNotExist:
            car = Garage()
            car.user = user
            car.item = ''
            car.save()
            item = car

        cache.set(key, pickle.dumps(item))
        return item


class Garage(models.Model):
    user = models.ForeignKey(User)
    item = models.TextField(blank=True)

    objects = GarageManager()

    class Meta:
        db_table = 'user_garage'
        verbose_name = 'Garage'

    def save(self):
        super(Garage, self).save()  # Call the "real" save() method
        key = 'user_garage_%s' % self.user.id
        cache.set(key, pickle.dumps(self))

    def __unicode__(self):
        return self.item

    def __getattr__(self, name):
        if name == 'items':
            return [x for x in self.item.split(',') if len(x) > 0]
        else:
            return self.__getattribute__(name)

    def buy_item(self, item_id):
        items = self.items[:]
        items.append(str(item_id))
        self.item = ','.join(items)

        self.save()

    def sell_item(self, item_id):
        items = self.items[:]
        del items[items.index(str(item_id))]
        self.item = ','.join(items)

        self.save()


class HookerManager(models.Manager):
    def get_by_id(self, hooker_id):
        key = 'hooker_%s' % hooker_id
        hooker = cache.get(key)

        if hooker is not None:
            return pickle.loads(str(hooker))

        try:
            hooker = self.get(pk=hooker_id)
        except Hooker.DoesNotExist:
            logging.warning('Hooker not found. ID:%s' % str(hooker_id))
            return None

        cache.set(key, pickle.dumps(hooker))
        return hooker

    def get_all(self):
        key = 'item_hooker'

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        item = self.all()

        cache.set(key, pickle.dumps(item))
        return item


class Hooker(models.Model):
    name = models.CharField(max_length=100)
    base_price = models.IntegerField()
    credit = models.PositiveSmallIntegerField()
    base_per_day_cash = models.IntegerField()
    look = models.IntegerField(default=0)

    objects = HookerManager()

    class Meta:
        db_table = 'item_hooker'
        verbose_name = 'Hooker'

    def __unicode__(self):
        return self.name


class GiftManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_gifts_%s' % user.id
        elif user_id is not None:
            key = 'user_gifts_%s' % user_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.filter(user=user)
            elif user_id is not None:
                item = self.filter(user__id=user_id)
            else:
                logging.warning('Gift not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except Garage.DoesNotExist:
            return ()

        cache.set(key, pickle.dumps(item))
        return item


class Gift(models.Model):
    user = models.ForeignKey(User)
    type = models.CharField(max_length=25)
    type_id = models.PositiveIntegerField(default=0)
    amount = models.PositiveIntegerField(default=0)
    has_received = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GiftManager()

    class Meta:
        db_table = 'item_gift'
        verbose_name = 'Gift'

    def __unicode__(self):
        return 'Gift %s %d %d' % (self.type, self.type_id, self.amount)
