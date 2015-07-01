# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from django.db import connection
from django.core.cache import cache
from django.utils.translation import ugettext as _

import crims.common.logger as logging
import math
import cPickle as pickle


class Item(object):
    def __init__(self, engine):
        self.engine = engine
        self.user = self.engine.user.user

        self.ITEM = settings.ALL_ITEM

    def set_item_type(self, item_type):
        self.item_type = item_type

        # Item
        if item_type == 'item':
            from crims.item.models import Item, Inventory

            self.all_item = {}
            if hasattr(self, 'item_tab'):
                for item in Item.objects.get_by_type(self.item_tab):
                    self.all_item[str(item.id)] = item
            else:
                for item in Item.objects.get_all():
                    self.all_item[str(item.id)] = item

            self.user_item = Inventory.objects.get_by_user(user=self.user)

            self.item_inventory = dict(zip(settings.INVENTORY_TYPES, ([], [], [], [])))
            for item_id in self.user_item.items:
                try:
                    item = self.all_item[str(item_id)]
                except KeyError:
                    continue

                if not self.item_inventory.has_key(str(item.type)):
                    self.item_inventory[str(item.type)] = []

                self.item_inventory[str(item.type)].append(item)

            self.active_inventory = dict(zip(settings.INVENTORY_TYPES, ([], [], [], [])))
            for item_id in self.user_item.actives:
                try:
                    item = self.all_item[str(item_id)]
                except KeyError:
                    continue

                if not self.active_inventory.has_key(str(item.type)):
                    self.active_inventory[str(item.type)] = []

                self.active_inventory[str(item.type)].append(item)

        # Hooker
        elif item_type == 'hooker':
            from crims.item.models import Hooker
            from crims.city.models import CityHooker

            self.all_hooker = {}
            for item in Hooker.objects.get_all():
                self.all_hooker[str(item.id)] = item

            self.city_hooker = CityHooker.objects.get_by_city(city_id=self.engine.user.profile.active_city_id)

            self.hooker_inventory = []
            for item in self.city_hooker.hookers:
                self.hooker_inventory.append(self.all_hooker[str(item)])

        # Garage
        elif item_type == 'vehicle':
            from crims.item.models import Item, Garage

            self.all_car = {}
            for item in Item.objects.filter(type='vehicle'):
                self.all_car[str(item.id)] = item

            self.garage_obj = Garage.objects.get_by_user(user=self.user)

            self.garage = []
            for item in self.garage_obj.items:
                self.garage.append(self.all_car[str(item)])

    # --- Item / Inventory

    def set_item_tab(self, tab_name):
        self.item_tab = tab_name

    def buy_item(self, item_id):
        try:
            item = self.all_item[str(item_id)]
        except KeyError:
            return

        profile = self.engine.user.profile

        # Enough cash?
        if not profile.has_enough('cash', item.price):
            self.engine.log.message(message=_("Not enough cash"))
            return

        # Enough credits?
        if int(item.credit) > 0:
            if not profile.has_enough('credit', item.credit):
                self.engine.log.message(
                    message=_("You need %(credits)s credits buy this item.") % {'credits': item.credit})
                return

                # if item.type == 'gadget' and item in self.item_inventory['gadget'] or item in self.active_inventory['gadget']:
                # self.engine.log.message(message=_("Already have %(item)s") % {'item': item.name})
                # return

        if item.type == 'vehicle':
            self.garage_obj.buy_item(str(item.id))
            profile.next_total_recalc = 1
            profile.spend('cash', item.price, autosave=False)
            profile.spend('credit', item.credit)

            self.engine.log.message(
                message=_("Bought %(item)s for $%(price)s. Go to your garage to see it.") % {'item': item,
                                                                                             'price': item.price})
            self.engine.stream.trigger('vehicle_bought')
            self.engine.stream.trigger('vehicle_%d_bought' % int(item.id))
        else:
            self.user_item.buy_item(str(item.id))
            profile.spend('cash', item.price, autosave=False)
            profile.spend('credit', item.credit)

            self.engine.log.message(
                message=_("Bought %(item)s for $%(price)s. In order to use it, you have to activate it.") % {
                'item': item, 'price': item.price})
            self.engine.stream.trigger('item_bought')
            self.engine.stream.trigger('item_%d_bought' % int(item.id))

    def sell_item(self, item_id):
        profile = self.engine.user.profile

        if self.item_type == 'vehicle':
            try:
                item = self.all_car[str(item_id)]
            except KeyError:
                return

            if str(item.id) not in self.garage_obj.items:
                return
            self.garage_obj.sell_item(str(item.id))
            profile.next_total_recalc = 1
            profile.earn('cash', item.price)

            self.engine.log.message(
                message=_("Sold %(item)s for $%(price)s.") % {'item': item, 'price': int(int(item.price) * 0.5)})
            self.engine.stream.trigger('vehicle_sold')
            self.engine.stream.trigger('vehicle_%d_sold' % int(item.id))

        else:
            try:
                item = self.all_item[str(item_id)]
            except KeyError:
                return

            # Has item?
            if str(item.id) not in self.user_item.items and str(item.id) not in self.user_item.actives:
                self.engine.log.message(message=_("This item is not in your inventory"))
                return

            self.user_item.sell_item(str(item.id))
            profile.earn('cash', int(item.price) * 0.5)

            self.engine.log.message(
                message=_("Sold %(item)s for $%(price)d") % {'item': item, 'price': int(int(item.price) * 0.5)})
            self.engine.stream.trigger('item_sold')
            self.engine.stream.trigger('item_%d_sold' % int(item.id))

    def activate_item(self, item_id):
        try:
            item = self.all_item[str(item_id)]
        except KeyError:
            return None

        sorry_part = item.type
        if len(self.active_inventory[str(item.type)]) >= settings.MAX_ACTIVE_INVENTORY_TYPES[str(item.type)]:
            self.engine.log.message(message=_("You've already reached maximum of %(max)s active items. Sorry.") % {
            'max': settings.MAX_ACTIVE_INVENTORY_TYPES[str(item.type)]})
            return item

        try:
            self.user_item.activate(str(item.id))
        except ValueError:
            self.engine.log.message(message=_("%(item)s not found") % {'item': item})
            return None

        self.active_inventory[str(item.type)].append(item)

        self.engine.log.message(message=_("%(item)s is active") % {'item': item})
        self.engine.stream.trigger('item_activated')
        self.engine.stream.trigger('item_%d_activated' % int(item.id))

        self.engine.user.recalculate_total()

        return item

    def deactivate_item(self, item_id):
        try:
            item = self.all_item[str(item_id)]
        except KeyError:
            return None

        try:
            self.user_item.deactivate(str(item.id))
        except ValueError:
            self.engine.log.message(message=_("%(item)s not found") % {'item': item})
            return None

        del self.active_inventory[str(item.type)][self.active_inventory[str(item.type)].index(item)]

        self.engine.log.message(message=_("%(item)s is not active") % {'item': item})
        self.engine.stream.trigger('item_deactivated')
        self.engine.stream.trigger('item_%d_deactivated' % int(item.id))

        self.engine.user.recalculate_total()

        return item

    def sort_item(self, to_sort_list):
        def sorter(a, b):
            if a.respect > b.respect:
                return 1
            elif a.respect == b.respect:
                return 0
            else:
                return -1

        to_sort_list.sort(sorter)
        return to_sort_list

    # --- Hooker

    def buy_hooker(self, hooker_id):
        try:
            hooker = self.all_hooker[str(hooker_id)]
        except KeyError:
            return

        profile = self.engine.user.profile

        # Enough cash?
        if not profile.has_enough('cash', hooker.base_price):
            self.engine.log.message(message=_("Not enough cash"))
            return

        # Enough credits?
        if int(hooker.credit) > 0:
            if not profile.has_enough('credit', hooker.credit):
                self.engine.log.message(
                    message=_("You need %(credits)s credits buy this preety lady.") % {'credits': hooker.credit})
                return

        # Enough space?
        if len(self.city_hooker.hookers) >= int(self.engine.user.profile.max_hookers):
            self.engine.log.message(message=_("Not enough space in whorehouse"))
            return

        # Buy
        self.city_hooker.buy_hooker(hooker)
        self.engine.log.message(
            message=_("%(name)s bought for $%(price)s") % {'name': hooker.name, 'price': hooker.base_price})
        self.engine.stream.trigger('hooker_bought')
        self.engine.stream.trigger('hooker_%d_bought' % int(hooker.id))

        # $$$
        profile.spend('cash', hooker.base_price, autosave=False)
        profile.spend('credit', hooker.credit)
        profile.add_per_day(source='hooker', source_id=hooker.id, amount=hooker.base_per_day_cash)

    def sell_hooker(self, hooker_id):
        try:
            hooker = self.all_hooker[str(hooker_id)]
        except KeyError:
            return

        # Has item?
        if str(hooker.id) not in self.city_hooker.hookers:
            self.engine.log.message(message=_("This hooker is not in your inventory"))
            return

        # Sell
        self.city_hooker.sell_hooker(hooker)
        self.engine.log.message(
            message=_("%(name)s sold for $%(price)s") % {'name': hooker.name, 'price': int(hooker.base_price * 0.5)})
        self.engine.stream.trigger('hooker_sold')
        self.engine.stream.trigger('hooker_%d_sold' % int(hooker.id))

        # $$$
        self.engine.user.profile.earn('cash', int(hooker.base_price * 0.5))
        self.engine.user.profile.remove_per_day(source='hooker', source_id=hooker.id)

    def sort_hooker(self, to_sort_list):
        def sorter(a, b):
            if a.look > b.look:
                return 1
            elif a.look == b.look:
                return 0
            else:
                return -1

        to_sort_list.sort(sorter)
        return to_sort_list

    # --- Car

    def sort_car(self, to_sort_list):
        def sorter(a, b):
            if a.name < b.name:
                return -1
            elif a.name > b.name:
                return 1
            return 0

        to_sort_list.sort(sorter)
        return to_sort_list
