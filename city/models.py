# -*- coding: UTF-8
import random

import simplejson as json
from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import crims.common.logger as logging
import datetime
import cPickle as pickle


# --- Map

class Map(models.Model):
    filename = models.CharField(max_length=20)
    desc = models.CharField(max_length=255)
    grid = models.CharField(max_length=128)

    variant_of = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'map'
        verbose_name = 'Map'

    def __unicode__(self):
        return "a map"

    def __getattr__(self, name):
        if name == 'grids':
            return [x.split(',') for x in self.grid.split('|')]
        else:
            return self.__getattribute__(name)


class CityMapManager(models.Manager):
    def get_by_id(self, cid, user_id=None):
        key = 'city_map_%s' % (cid)

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            item = self.get(pk=int(cid))
        except CityMap.DoesNotExist:
            if user_id is not None:
                item = CityMap()
                item.owner_id = user_id
                item.orig_owner_id = user_id
                item.population = settings.DEFAULT_CITY_POPULATION
                item.sector, item.position = Sector.objects.next_cords()
                item.save()
            else:
                return None

        cache.set(key, pickle.dumps(item))
        return item

    def get_names_list(self, ids_list):
        return self.all().in_bulk(ids_list)


class CityMap(models.Model):
    name = models.CharField(max_length=12)
    owner_id = models.PositiveIntegerField()
    orig_owner_id = models.PositiveIntegerField()
    population = models.PositiveIntegerField(default=settings.DEFAULT_CITY_POPULATION)
    used_population = models.PositiveIntegerField(default=settings.DEFAULT_CITY_POPULATION)

    slot = models.TextField()
    density = models.CharField(max_length=50)
    sector = models.PositiveIntegerField(default=0)
    position = models.PositiveSmallIntegerField(default=0)

    is_secured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CityMapManager()

    class Meta:
        db_table = 'city_map'
        verbose_name = 'City Map'
        verbose_name_plural = 'City Maps'

    def __unicode__(self):
        return self.name

    def save(self):
        super(CityMap, self).save()  # Call the "real" save() method
        key = 'city_map_%s_%s' % (self.sector, self.position)
        cache.set(key, pickle.dumps(self))

    def __getattr__(self, name):
        if name == 'slots':
            if self.slot == '':
                self.slot = json.dumps([0 for x in xrange(0, settings.MAX_BUILDINGS)])
                self.save()
            return json.loads(self.slot)
        elif name == 'owners':
            return json.loads(self.owner)
        elif name == 'densities':
            if len(self.density) == 0: return [0.0 for i in xrange(0, 8)]
            return self.density
        else:
            return self.__getattribute__(name)

    def add_bld(self, bld):
        limit = 100
        slots = self.slots

        while True:
            r = random.randint(0, len(slots) - 1)
            if slots[r] == 0:
                slots[r] = bld
                self.slot = json.dumps(slots)
                self.save()

                break

            limit -= 1
            if limit == 0: break

    def rem_bld(self, id):
        pass


class WorldMapManager(models.Manager):
    def get_by_user(self, sector, user=None, user_id=None):
        if user is not None:
            key = 'world_map_%s_sector_%s' % (user.id, sector)
        elif user_id is not None:
            key = 'world_map_%s_sector_%s' % (user_id, sector)

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user, sector=sector)
            elif user_id is not None:
                item = self.get(user__id=user_id, sector=sector)
            else:
                logging.warning('WorldMap not found. USER:%s, ID:%s. Sector: %s' % (str(user), str(user_id), sector))
                return None

        except WorldMap.DoesNotExist:
            wm = WorldMap()
            wm.user = user
            wm.city = json.dumps([0 for x in xrange(100)])
            wm.sector = sector
            wm.save()
            item = wm

        cache.set(key, pickle.dumps(item))
        return item


class WorldMap(models.Model):
    user = models.ForeignKey(User)
    city = models.TextField()
    sector = models.PositiveIntegerField()

    objects = WorldMapManager()

    class Meta:
        db_table = 'map_world'
        verbose_name = 'World Map'
        verbose_name_plural = 'World Maps'

    def __unicode__(self):
        return "%s's world map" % self.user

    def save(self):
        super(WorldMap, self).save()  # Call the "real" save() method
        key = 'world_map_%s_sector_%s' % (self.user.id, self.sector)
        cache.set(key, pickle.dumps(self))

    def __getattr__(self, name):
        if name == 'cities':
            return json.loads(self.city)
        else:
            return self.__getattribute__(name)


class SectorManager(models.Manager):
    def next_cords(self):
        import random

        sectors = self.filter(density__lt='0.85')
        while len(sectors) < 3:
            self.add_sectors()
            sectors = self.filter(density__lt='0.85')

        sector = random.choice(sectors)
        cities_in_sector = [int(x.position) for x in CityMap.objects.filter(sector=sector.id)]
        sector.density = str(len(cities_in_sector) / 100.0)
        sector.save()

        full = [x for x in xrange(1, 101) if x not in cities_in_sector]
        return (int(sector.id), random.choice(full))

    def add_sectors(self):
        from crims.common.helpers._crims import _get_slot
        from django.db.models import Max

        saved = 0

        start = int(self.aggregate(Max('x'))['x__max'])

        start_x = 1
        start_y = 1
        target = start + 1
        while start_x < target:
            s = Sector()
            s.x = target
            s.y = start_x
            s.save()
            saved += 1

            s = Sector()
            s.x = start_y
            s.y = target
            s.save()
            saved += 1

            start_y += 1
            start_x += 1

        s = Sector()
        s.x = target
        s.y = target
        s.save()
        saved += 1

        return saved


class Sector(models.Model):
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()

    density = models.DecimalField(max_digits=3, decimal_places=2, default="0.0")

    objects = SectorManager()

    class Meta:
        db_table = 'map_sector'
        verbose_name = 'Sector'

    def __unicode__(self):
        return "Sector %s" % self.id


class CityWallManager(models.Manager):
    def get_by_city(self, city_id, is_public=None):
        if is_public is None or is_public is False:
            return self.filter(city__id=city_id)
        else:
            return self.filter(city__id=city_id, is_public=is_public)

    def get_latest(self, city_id, is_public=None):
        return self.get_by_city(city_id, is_public).order_by('-created_at')[:10]


class CityWall(models.Model):
    city = models.ForeignKey(CityMap)
    source = models.CharField(max_length=25)
    title = models.CharField(max_length=100)
    content = models.CharField(max_length=255)
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = CityWallManager()

    class Meta:
        db_table = 'city_wall'
        verbose_name = 'CityWall'

    def __unicode__(self):
        return "CityWall %s" % self.id


# --- Building

class CityBuildingManager(models.Manager):
    def get_by_city_id(self, city_id, user_id=None):
        key = 'city_building_%s' % city_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            item = self.get(city__id=city_id)
        except CityBuilding.DoesNotExist:
            item = CityBuilding()
            item.city = CityMap.objects.get_by_id(city_id, user_id)
            item.save()

        cache.set(key, pickle.dumps(item))
        return item


class CityBuilding(models.Model):
    city = models.ForeignKey(CityMap)
    item = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CityBuildingManager()

    class Meta:
        db_table = 'city_building'
        verbose_name = 'CityBuilding'

    def __unicode__(self):
        return "CityBuilding %s" % self.id

    def __getattr__(self, name):
        if name == 'items':
            if self.item == '': return {}
            return json.loads(self.item)
        else:
            return self.__getattribute__(name)

    def add(self, type, entries):
        items = self.items

        if items.has_key(type):
            done = []
            [done.append(owned) for owned in items[type].itervalues()]
            for entry in entries:
                if entry in done: del entries[entries.index(entry)]
        else:
            items[type] = {'0': entries}
            self.item = json.dumps(items)

        if len(entries) > 0:
            if not items[type].has_key('0'): items[type]['0'] = []
            items[type]['0'].extend(entries)
            self.item = json.dumps(items)

        self.save()

    def remove(self, type, entries):
        to_notify = []

        items = self.items
        for owner, owner_items in items[type].iteritems():
            for entry in entries:
                try:
                    del owner_items[owner_items.index(str(entry))]
                    to_notify.append(owner)
                except ValueError:
                    continue
        if len(items[type]) == 0: del items[type]

        self.item = json.dumps(items)
        self.save()
        return to_notify

    def move_owner(self, bld_type, bld_id, curr_owner, new_owner):
        bld_type, bld_id, curr_owner, new_owner, items = str(bld_type), str(bld_id), str(curr_owner), str(
            new_owner), self.items

        if not items.has_key(bld_type):
            logging.error('No building_type %s' % bld_type)
            return False
        if not items[bld_type].has_key(curr_owner):
            logging.error('%s is not owner of %s:%s' % (curr_owner, bld_type, bld_id))
            return False
        if bld_id not in items[bld_type][curr_owner]:
            logging.error('%s:%s:%s not in the city' % (bld_type, curr_owner, bld_id))
            return False

        del items[bld_type][curr_owner][items[bld_type][curr_owner].index(bld_id)]
        if len(items[bld_type][curr_owner]) == 0: del items[bld_type][curr_owner]

        if not items[bld_type].has_key(new_owner):
            items[bld_type][new_owner] = []
        items[bld_type][new_owner].append(bld_id)

        self.item = json.dumps(items)
        self.save()
        return True


# --- Unit

class UnitManager(models.Manager):
    def get_all(self):
        key = 'units'
        items = cache.get(key)

        if items is not None:
            return pickle.loads(str(items))

        items = self.all()
        cache.set(key, pickle.dumps(items))
        return items


class Unit(models.Model):
    name = models.CharField(max_length=15)
    attack = models.PositiveIntegerField()
    defense = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    credit = models.PositiveSmallIntegerField()
    time_to_build = models.PositiveIntegerField()

    objects = UnitManager()

    class Meta:
        db_table = 'item_unit'
        verbose_name = 'Unit'

    def __unicode__(self):
        return "%s (%s/%s/%s)" % (self.name, self.attack, self.defense, self.time_to_build)


class CityUnitManager(models.Manager):
    def get_by_user(self, city_id, user=None, user_id=None, username=None):
        if username is not None:
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None

        if user is not None:
            key = 'city_unit_%s_%s' % (city_id, user.id)
        elif user_id is not None:
            key = 'city_unit_%s_%s' % (city_id, user_id)

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user, city_id=city_id)
            elif user_id is not None:
                item = self.get(user__id=user_id, city_id=city_id)
            else:
                logging.warning('CityUnit not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except CityUnit.DoesNotExist:
            item = CityUnit()
            item.user = user or User.objects.get(pk=user_id)
            item.city_id = city_id
            item.save()

        cache.set(key, pickle.dumps(item))
        return item

    def get_all_cities(self, user=None, user_id=None):
        if user is not None:
            return self.filter(user=user)
        elif user_id is not None:
            return self.filter(user__id=user_id)
        else:
            logging.error("user and user_id is None in city.models.get_all_cities :(")
            return ()


class CityUnit(models.Model):
    user = models.ForeignKey(User)
    city_id = models.PositiveIntegerField()
    unit = models.TextField()
    next_tribute_at = models.DateTimeField(default=datetime.datetime.now())

    objects = CityUnitManager()

    class Meta:
        db_table = 'city_unit'
        verbose_name = 'City Unit'

    def __unicode__(self):
        return "%s's city's units" % self.user

    def save(self):
        super(CityUnit, self).save()  # Call the "real" save() method
        if len(self.unit) == 0: self.delete()
        cache.delete('city_unit_%s_%s' % (self.city_id, self.user.id))

    def delete(self):
        super(CityUnit, self).delete()  # Call the "real" delete() method
        cache.delete('city_unit_%s_%s' % (self.city_id, self.user.id))

    def __getattr__(self, name):
        if name == 'units':
            if self.unit == '': return {}
            return json.loads(self.unit)
        else:
            return self.__getattribute__(name)

    def kill_units(self, how_many):
        logging.debug('kill %s units' % str(how_many))
        for x in xrange(0, how_many):
            self.rem_unit(random.choice(self.units.keys()))

    def add_unit(self, id, cnt=1):
        units = self.units
        try:
            units[str(id)] += cnt
        except KeyError:
            units[str(id)] = cnt

        self.unit = json.dumps(units)
        self.save()
        logging.debug('add_unit id:%s, city:%s, user:%s' % (id, self.city_id, self.user))
        return True

    def rem_unit(self, id, cnt=1):
        units = self.units
        try:
            if units[str(id)] <= 0 or units[str(id)] < cnt: raise ValueError
            units[str(id)] -= cnt
        except (KeyError, ValueError):
            logging.warning('Failed to remove unit_id:%s (city:%s, user:%s)' % (str(id), self.city_id, self.user))
            return False

        if units[str(id)] == 0: del units[str(id)]

        self.unit = json.dumps(units)
        self.save()
        logging.debug('rem_unit id:%s, city:%s, user:%s' % (id, self.city_id, self.user))
        return True

    def get_sums(self):
        all_unit = {}
        for item in Unit.objects.get_all():
            all_unit[str(item.id)] = item

        a, d, i = 0, 0, 0
        for k, x in self.units.iteritems():
            a += all_unit[k].attack * x
            d += all_unit[k].defense * x
            i += x

        return [a, d, i]


class CityUnitProgressManager(models.Manager):
    def get_by_user(self, city_id, user=None, user_id=None):
        # if user is not None:
        # 	key = 'city_unit_progress_%s_%s' % (city_id, user.id)
        # elif user_id is not None:
        # 	key = 'city_unit_progress_%s_%s' % (city_id, user_id)
        #
        # item = cache.get(key)
        # if item is not None:
        # 	return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user, city_id=city_id)
            elif user_id is not None:
                item = self.get(user__id=user_id, city_id=city_id)
            else:
                logging.warning('CityUnitProgress not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except CityUnitProgress.DoesNotExist:
            cs = CityUnitProgress()
            cs.user = user
            cs.city_id = city_id
            cs.save()
            item = cs

        # cache.set(key, pickle.dumps(item))
        return item


class CityUnitProgress(models.Model):
    user = models.ForeignKey(User)
    city_id = models.PositiveIntegerField()
    unit = models.TextField()

    next_at = models.DateTimeField(default=datetime.datetime.now())

    objects = CityUnitProgressManager()

    class Meta:
        db_table = 'city_unit_progress'
        verbose_name = 'City Unit Build'
        verbose_name_plural = 'City Units Progress'

    def __unicode__(self):
        return "%s's city's units' builds" % self.user

    def save(self):
        super(CityUnitProgress, self).save()  # Call the "real" save() method
        if len(self.unit) == 0: self.delete()

    # cache.delete('city_unit_progress_%s_%s' % (self.city_id, self.user.id))

    def delete(self):
        super(CityUnitProgress, self).delete()  # Call the "real" delete() method

    # cache.delete('city_unit_progress_%s_%s' % (self.city_id, self.user.id))

    def __getattr__(self, name):
        if name == 'units':
            if self.unit == '': return ()
            return json.loads(self.unit)
        else:
            return self.__getattribute__(name)


class MapMoveManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'map_move_%s' % (user.id)
        elif user_id is not None:
            key = 'map_move_%s' % (user_id)

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user)
            elif user_id is not None:
                item = self.get(user__id=user_id)
            else:
                logging.warning('MapMove not found. USER:%s, ID:%s.' % (str(user), str(user_id)))
                return None

        except MapMove.DoesNotExist:
            item = MapMove()
            item.user = user or User.objects.get(pk=user_id)
            item.save()

        cache.set(key, pickle.dumps(item))
        return item


class MapMove(models.Model):
    user = models.ForeignKey(User)
    unit = models.TextField()

    next_at = models.DateTimeField(default=datetime.datetime.now())

    objects = MapMoveManager()

    class Meta:
        db_table = 'city_move'
        verbose_name = 'City Unit Move'

    def __unicode__(self):
        return "%s's moves" % self.user

    def save(self):
        super(MapMove, self).save()  # Call the "real" save() method
        if len(self.units) == 0: return self.delete()
        cache.delete('map_move_%s' % (self.user.id))

    def delete(self):
        super(MapMove, self).delete()  # Call the "real" delete() method
        cache.delete('map_move_%s' % (self.user.id))

    def __getattr__(self, name):
        if name == 'units':
            if self.unit == '': return []
            return json.loads(self.unit)
        else:
            return self.__getattribute__(name)


class MapMoveGroupManager(models.Manager):
    def get_by_id(self, group_id):
        key = 'map_move_group_%s' % group_id
        item = cache.get(key)

        try:
            item = self.get(pk=group_id)
        except MapMoveGroup.DoesNotExist:
            logging.warning('MapMoveGroup not found. ID:%s' % str(group_id))
            return None

        cache.set(key, pickle.dumps(item))
        return item


class MapMoveGroup(models.Model):
    unit = models.TextField()

    objects = MapMoveGroupManager()

    class Meta:
        db_table = 'city_move_group'
        verbose_name = 'City Unit Move Group'

    def __unicode__(self):
        return "MapMoveGroup"

    def save(self):
        if len(self.units) == 0: return self.delete()
        super(MapMoveGroup, self).save()  # Call the "real" save() method
        try:
            cache.delete('map_move_group_%s' % (self.pk))
        except AssertionError:
            pass

    def delete(self):
        super(MapMoveGroup, self).delete()  # Call the "real" delete() method
        try:
            cache.delete('map_move_group_%s' % (self.pk))
        except AssertionError:
            pass

    def __getattr__(self, name):
        if name == 'units':
            if self.unit == '': return ()
            return json.loads(self.unit)
        else:
            return self.__getattribute__(name)


# --- Product

class ProductManager(models.Manager):
    def get_by_id(self, item_id):
        key = 'product_%s' % item_id
        item = cache.get(key)

        if item is not None:
            return json.loads(str(item))

        try:
            item = self.get(pk=item_id)
        except Product.DoesNotExist:
            logging.warning('Product not found. ID:%s' % str(item_id))
            return None

        cache.set(key, pickle.dumps(item))
        return item

    def get_by_type(self, type):
        key = 'products_%s' % str(type)
        item = cache.get(key)

        if item is not None:
            return pickle.loads(str(item))

        item = self.filter(type=type).order_by('order')

        cache.set(key, pickle.dumps(item))
        return item

    def get_all(self):
        key = 'products'
        item = cache.get(key)

        if item is not None:
            return pickle.loads(str(item))

        item = self.all().order_by('type', 'order')

        cache.set(key, pickle.dumps(item))
        return item


class Product(models.Model):
    type = models.CharField(max_length=10)
    name = models.CharField(max_length=20)
    order = models.PositiveSmallIntegerField()
    base_speed = models.PositiveSmallIntegerField()  # units per hour
    base_price = models.PositiveSmallIntegerField()  # per unit
    min_sell_price = models.PositiveSmallIntegerField()
    max_sell_price = models.PositiveSmallIntegerField()

    objects = ProductManager()

    class Meta:
        db_table = 'item_product'
        verbose_name = 'Product'

    def __unicode__(self):
        return self.name

    def save(self):
        super(Product, self).save()  # Call the "real" save() method


class ProductPriceManager(models.Manager):
    def get_by_type(self, type, source='main'):
        key = 'product_%s_price_%s' % (type, source)
        item = cache.get(key)

        if item is not None:
            return pickle.loads(str(item))

        try:
            item = self.get(type=type, source=source)
        except ProductPrice.DoesNotExist:
            logging.warning('ProductPrice not found. TYPE:%s' % str(type))
            return None

        cache.set(key, pickle.dumps(item))
        return item


class ProductPrice(models.Model):
    type = models.CharField(max_length=10)
    source = models.CharField(max_length=10, default='main')
    price = models.PositiveIntegerField()
    valid_string = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProductPriceManager()

    class Meta:
        db_table = 'item_product_price'
        verbose_name = 'Product Price'

    def __unicode__(self):
        return "Product price from %s" % (self.created_at)

    def __getattr__(self, name):
        if name == 'prices':
            return self.price.split('|')
        else:
            return self.__getattribute__(name)

    def save(self):
        # TODO: kasowanie cache'y
        super(ProductPrice, self).save()  # Call the "real" save() method


class CityProductManager(models.Manager):
    def get_by_city(self, city=None, city_id=None):
        if city is not None:
            key = 'city_product_%s' % city.id
        elif city_id is not None:
            key = 'city_product_%s' % city_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if city is not None:
                item = self.get(city=city)
            elif city_id is not None:
                item = self.get(city__id=city_id)
            else:
                logging.warning('CityProduct not found. CITY:%s, ID:%s' % (str(city), str(city_id)))
                return None

        except CityProduct.DoesNotExist:
            cp = CityProduct()
            cp.city = city or CityMap.objects.get(pk=city_id)
            cp.save()
            item = cp

        cache.set(key, pickle.dumps(item))
        return item


class CityProduct(models.Model):
    city = models.ForeignKey(CityMap)
    first = models.CharField(max_length=10)  # type
    second = models.CharField(max_length=10)  # type
    first_level = models.CharField(max_length=100)
    second_level = models.CharField(max_length=100)

    objects = CityProductManager()

    class Meta:
        db_table = 'city_product'
        verbose_name = 'City\'s Product'

    def __unicode__(self):
        return "%s's products" % (self.city)

    def __getattr__(self, name):
        if name == 'first_levels':
            return json.loads(self.first_level)
        elif name == 'second_levels':
            return json.loads(self.second_level)
        else:
            return self.__getattribute__(name)

    def save(self):
        super(CityProduct, self).save()  # Call the "real" save() method
        key = 'city_product_%s' % self.city.id
        cache.set(key, pickle.dumps(self))

    def set(self, what):
        if what not in settings.PRODUCT_TYPES: return None
        if self.first == '':
            self.first = what
        # elif self.second == '': self.second = what
        else:
            return None
        self.save()
        return True

    def set_force(self, what, which):
        self.__dict__[which] = what
        self.save()

    def upgrade(self, which='first'):
        if which == 'first':
            if self.first_level < settings.PRODUCT_MAX_UPGRADE_LEVEL:
                self.first_level += 1
        elif which == 'first':
            if self.second_level < settings.PRODUCT_MAX_UPGRADE_LEVEL:
                self.second_level += 1
        else:
            logging.error('Tried to upgrade %s' % str(which))
            return

        self.save()

    def clear_upgrades(self):
        self.first_level = 0
        self.second_level = 0
        self.save()


class CityProductProgressManager(models.Manager):
    def get_by_city(self, city=None, city_id=None):
        if city is not None:
            key = 'city_product_progress_%s' % city.id
        elif city_id is not None:
            key = 'city_product_progress_%s' % city_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if city is not None:
                item = self.get(city=city)
            elif city_id is not None:
                item = self.get(city__id=city_id)
            else:
                logging.warning('CityProductProgress not found. CITY:%s, ID:%s' % (str(city), str(city_id)))
                return None

        except CityProductProgress.DoesNotExist:
            cp = CityProductProgress()
            cp.city = city or CityMap.objects.get(pk=city_id)
            cp.save()
            item = cp

        cache.set(key, pickle.dumps(item))
        return item


class CityProductProgress(models.Model):
    city = models.ForeignKey(CityMap)
    item = models.TextField()

    next_at = models.DateTimeField(default=datetime.datetime.now())

    objects = CityProductProgressManager()

    class Meta:
        db_table = 'city_product_progress'
        verbose_name = 'City Product Build'
        verbose_name_plural = 'City Products Progress'

    def __unicode__(self):
        return "%s's city's products' builds" % self.city

    def save(self):
        super(CityProductProgress, self).save()  # Call the "real" save() method
        cache.delete('city_product_progress_%s' % (self.city_id))

    def __getattr__(self, name):
        if name == 'items':
            if self.item == '': return ()
            return json.loads(self.item)
        else:
            return self.__getattribute__(name)


class CityProductReqManager(models.Manager):
    def get_by_city(self, city=None, city_id=None):
        if city is not None:
            key = 'city_product_req_%s' % city.id
        elif city_id is not None:
            key = 'city_product_req_%s' % city_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if city is not None:
                item = self.get(city=city)
            elif city_id is not None:
                item = self.get(city__id=city_id)
            else:
                logging.warning('CityProductReq not found. CITY:%s, ID:%s' % (str(city), str(city_id)))
                return None

        except CityProductReq.DoesNotExist:
            cp = CityProductReq()
            cp.city = city or CityMap.objects.get_by_id(city_id)
            cp.save()
            item = cp

        cache.set(key, pickle.dumps(item))
        return item


class CityProductReq(models.Model):
    city = models.ForeignKey(CityMap)
    item = models.TextField()  # {'drug_1': 100, ...}

    objects = CityProductReqManager()

    class Meta:
        db_table = 'city_product_req'
        verbose_name = 'City\'s Product Need'

    def __unicode__(self):
        return "Needs for %s's products" % self.city

    def __getattr__(self, name):
        if name == 'items':
            return json.loads(self.item)
        else:
            return self.__getattribute__(name)

    def save(self):
        super(CityProductReq, self).save()  # Call the "real" save() method
        key = 'city_product_req_%s' % self.city.id
        cache.set(key, pickle.dumps(self))

    def increase(self, type, amt):
        items = self.items
        try:
            items[type] += amt
        except KeyError:
            logging.error('Cannot increase %s' % str(type))
            return

        self.item = json.dumps(items)
        self.save()

    def decrease(self, type, amt):
        items = self.items
        try:
            items[type] -= amt
        except KeyError:
            logging.error('Cannot decrease %s' % str(type))
            return

        self.item = json.dumps(items)
        self.save()


class UserProductManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_product_%s' % user.id
        elif user_id is not None:
            key = 'user_product_%s' % user_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user)
            elif user_id is not None:
                item = self.get(user__id=user_id)
            else:
                logging.warning('UserProduct not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except UserProduct.DoesNotExist:
            up = UserProduct()
            up.user = user or User.objects.get(pk=user_id)
            up.item = json.dumps({})
            up.save()
            item = up

        cache.set(key, pickle.dumps(item))
        return item


class UserProduct(models.Model):
    user = models.ForeignKey(User)
    item = models.TextField()  # {'drug_1': 100, ...}

    objects = UserProductManager()

    class Meta:
        db_table = 'user_product'
        verbose_name = 'User\'s Products'

    def __unicode__(self):
        return "Products of user %s" % self.user

    def __getattr__(self, name):
        if name == 'items':
            return json.loads(self.item)
        else:
            return self.__getattribute__(name)

    def save(self):
        super(UserProduct, self).save()  # Call the "real" save() method
        key = 'user_product_%s' % self.user.id
        cache.set(key, pickle.dumps(self))

    def has_enough(self, type, amt):
        items = self.items
        if items.has_key(type):
            if items[type] >= amt:
                return True
            else:
                return False
        else:
            logging.warning('%s not in product types' % str(type))
            return False

    def increase(self, type, amt):
        items = self.items
        try:
            items[type] += amt
        except KeyError:
            logging.error('Cannot increase %s' % str(type))
            return

        self.item = json.dumps(items)
        self.save()

    def decrease(self, type, amt):
        items = self.items
        try:
            items[type] -= amt
        except KeyError:
            logging.error('Cannot decrease %s' % str(type))
            return

        self.item = json.dumps(items)
        self.save()


class CityHookerManager(models.Manager):
    def get_by_city(self, city=None, city_id=None):
        if city is not None:
            key = 'city_hooker_%s' % city.id
        elif city_id is not None:
            key = 'city_hooker_%s' % city_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if city is not None:
                item = self.get(city=city)
            elif city_id is not None:
                item = self.get(city__id=city_id)
            else:
                logging.warning('CityHooker not found. CITY:%s, ID:%s' % (str(city), str(city_id)))
                return None

        except CityHooker.DoesNotExist:
            item = CityHooker()
            item.city = city or CityMap.objects.get_by_id(city_id)
            item.hooker = ''
            item.save()

        cache.set(key, pickle.dumps(item))
        return item


class CityHooker(models.Model):
    city = models.ForeignKey(CityMap)
    hooker = models.CharField(max_length=255)

    objects = CityHookerManager()

    class Meta:
        db_table = 'city_hooker'
        verbose_name = 'City Hooker'
        verbose_name_plural = 'City Hookers'

    def __unicode__(self):
        return "%s's hookers" % (self.city)

    def __getattr__(self, name):
        if name == 'hookers':
            return [x for x in self.hooker.split(',') if len(x) > 0]
        else:
            return self.__getattribute__(name)

    def save(self):
        super(CityHooker, self).save()  # Call the "real" save() method
        key = 'city_hooker_%s' % self.city.id
        cache.set(key, pickle.dumps(self))

    def buy_hooker(self, hooker):
        hookers = self.hookers[:]
        hookers.append(str(hooker.id))
        self.hooker = ','.join(hookers)
        self.save()

    def sell_hooker(self, hooker):
        hookers = self.hookers[:]
        del hookers[hookers.index(str(hooker.id))]
        self.hooker = ','.join(hookers)
        self.save()
