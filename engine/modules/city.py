# -*- coding: utf-8 -*-
import simplejson as json
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

import crims.common.logger as logging
import time
import datetime
from crims.common.helpers.core import copy_model_instance
from crims.city.models import CityUnit, CityMap, CityBuilding, MapMove, MapMoveGroup


class City(object):
    def __init__(self, engine):
        self.engine = engine
        self.id = None

        self.TRIBUTE_ORDER = ['transport_company', 'gas_station', 'club', 'hotel', 'restaurant', 'pub', 'cafe',
                              'liquor']
        self.other_cities = None

    def set_id(self):
        self.id = self.engine.user.profile.active_city_id

        self.city_map = CityMap.objects.get_by_id(self.id, self.engine.user.user.id)
        self.city_building = CityBuilding.objects.get_by_city_id(self.id, self.engine.user.user.id)
        self.city_unit = CityUnit.objects.get_by_user(city_id=self.id, user=self.engine.user.user)

        if self.city_map.owner_id == self.engine.user.user.id or self.engine.user.user.is_superuser:
            self.can_built_units = True
            self.can_move_units_here = True
            self.can_see_city = True
            self.in_my_city = True
        else:
            self.in_my_city = False
            if self.city_building is None:
                self.can_built_units = False
            else:
                self.can_built_units = sum(
                    [len(y.get(str(self.engine.user.user))) for x, y in self.city_building.items.items() if
                     y.get(str(self.engine.user.user)) is not None]) >= 10

            self.can_move_units_here = self.city_map.is_secured
            self.can_see_city = len(self.city_unit.units) > 0 and not self.city_map.is_secured

    def enter_city(self, cid):
        self.engine.user.profile.active_city_id = cid
        self.engine.user.profile.save()

        city = CityMap.objects.get_by_id(cid)
        if city.owner_id != self.engine.user.profile.user_id:
            self.engine.stream.post_to_city_wall('city_visit', '<a href="%s">%s</a>' % (
            reverse('city_enter', args=[self.engine.user.profile.default_city_id]), self.engine.user.profile.user),
                                                 city_id=cid, is_public=False)
            self.in_my_city = False
            logging.debug('%s entered foreign city (%s)' % (self.engine.user.user, cid))
        else:
            self.in_my_city = True
            logging.debug('%s entered his city' % self.engine.user.user)

    def set_action_type(self, action_type):

        if action_type == 'map':
            pass

        elif action_type == 'unit':
            from crims.city.models import Unit, CityUnitProgress

            if self.id is None: logging.error('city_id not set up')

            self.UNIT = {
                'bum': _('Bum'), 'student': _('Student'), 'karate_kid': _('Karate Kid'), 'wrestler': _('Wrestler'),
            'rookie': _('Rookie'), 'soldier': _('Soldier'), 'navy_seals': _('Navy Seals'),
            'chuck_norris': _('Chuck Norris')
            }

            self.all_unit = {}
            for item in Unit.objects.get_all():
                self.all_unit[str(item.id)] = item

            self.city_unit = CityUnit.objects.get_by_user(city_id=self.id, user=self.engine.user.user)
            self.city_unit_progress = CityUnitProgress.objects.get_by_user(city_id=self.id, user=self.engine.user.user)
            self.build_queue = []
            for unit in self.city_unit_progress.units:
                u = copy_model_instance(self.all_unit[str(unit[0])])
                u.ready_at = datetime.datetime.fromtimestamp(unit[1])
                self.build_queue.append(u)

        elif action_type == 'tribute':
            from crims.job.models import JobTribute

            if self.id is None: logging.error('city_id not set up')

            self.TRIBUTE = {
                'cafe': _('Cafe'), 'club': _('Club'), 'gas_station': _('Gas Station'), 'hotel': _('Hotel'),
            'liquor': _('Liquor Store'), 'pub': _('Pub'), 'restaurant': _('Restaurant'),
            'transport_company': _('Transport Company')
            }

            self.all_tribute = JobTribute.objects.get_all()

            user = str(self.engine.user.user)
            self.user_tribute = {}
            for bld_type, bld_owners in self.city_building.items.iteritems():
                self.user_tribute[bld_type] = []
                total_blds = float(sum([len(x) for x in bld_owners.itervalues()]))

                if bld_owners.has_key('0'):
                    self.user_tribute[bld_type].append(
                        ['0', len(bld_owners['0']), "%3.2f" % (len(bld_owners['0']) / total_blds * 100)])
                    del bld_owners['0']
                if bld_owners.has_key(user):
                    self.user_tribute[bld_type].append(
                        ['me', len(bld_owners[user]), "%3.2f" % (len(bld_owners[user]) / total_blds * 100)])
                    del bld_owners[user]

                if len(bld_owners.keys()) == 0: continue

                backitems = [[len(y), x] for x, y in bld_owners.items()]
                backitems.reverse()
                sorted_bld_owners = [backitems[i] for i in range(0, len(backitems))]

                for blds, bld_owner in sorted_bld_owners:
                    self.user_tribute[bld_type].append([bld_owner, blds, "%3.2f" % ((blds / total_blds) * 100)])

        elif action_type == 'production':
            from crims.city.models import Product, CityProduct, CityProductProgress, UserProduct

            if self.id is None: logging.error('city_id not set up')

            self.user_product = UserProduct.objects.get_by_user(user=self.engine.user.user)
            self.city_product = CityProduct.objects.get_by_city(city_id=self.id)

            self.all_product = {}
            for item in Product.objects.get_by_type(self.city_product.first):
                if not self.all_product.has_key(item.type): self.all_product[item.type] = {}
                self.all_product[item.type][item.name] = item

            if (self.city_product.second != ''):
                for item in Product.objects.get_by_type(self.city_product.second):
                    if not self.all_product.has_key(item.type): self.all_product[item.type] = {}
                    self.all_product[item.type][item.name] = item

            self.city_product_progress = CityProductProgress.objects.get_by_city(city_id=self.id)
            self.build_queue = []
            for item in self.city_product_progress.items:
                u = self.all_product[str(item[0])][str(item[1])]
                u.amount = int(item[2])
                u.ready_at = datetime.datetime.fromtimestamp(item[3])
                self.build_queue.append(u)

    # --- City

    def get_city(self, city_id):
        return CityMap.objects.get_by_id(city_id)

    # --- Units

    def hire_unit(self, unit_id):
        try:
            unit = self.all_unit[str(unit_id)]
        except KeyError:
            logging.warning("Unit with ID=%s NOT FOUND" % str(unit_id))

        if len(self.city_unit_progress.units) >= self.engine.settings.MAX_SECURITY_BUILD_QUEUE:
            self.engine.log.message(message=_('Maximum length of the queue reached'))
            return

        if not self.engine.user.profile.has_enough('cash', unit.price):
            self.engine.log.message(message=_('Not enough cash'))
            return

        if unit.credit > 0 and not self.engine.user.profile.has_enough('credit', unit.credit):
            self.engine.log.message(message=_('Not enough credits. Add some first.'))
            return

        if len(self.city_unit_progress.units) == 0:
            self.city_unit_progress.unit = "[[%d,%d]]" % (int(unit_id), int(time.time()) + int(unit.time_to_build) * 60)
            self.city_unit_progress.next_at = datetime.datetime.fromtimestamp(
                int(time.time()) + int(unit.time_to_build) * 60)
        else:
            units = self.city_unit_progress.units
            last_unit = self.city_unit_progress.units.pop()

            units.append([int(unit_id), int(last_unit[1]) + int(unit.time_to_build) * 60])
            self.city_unit_progress.unit = json.dumps(units)
        # self.city_unit_progress.next_at = datetime.datetime.fromtimestamp(self.city_unit_progress.units[0][1])

        self.engine.user.profile.spend('cash', unit.price)
        if unit.credit > 0: self.engine.user.profile.spend('credit', unit.credit)
        self.city_unit_progress.save()

        self.engine.log.message(message=_("Unit hiring process started"))

    def cancel_build_unit(self, unit_order_id):
        units = self.city_unit_progress.units

        try:
            unit_order_id = int(unit_order_id)
            del units[unit_order_id]
        except KeyError, ValueError:
            return

        if len(units) == 0:
            self.city_unit_progress.unit = ''
        else:
            new_units = []
            if unit_order_id == 0:
                # usuwamy pierwszy - przeliczamy reszte bez nadkladania
                last = int(time.time())
                for unit in units:
                    last += self.all_unit[str(unit[0])].time_to_build * 60
                    new_units.append([unit[0], last])
            else:
                # usuwamy kolejny - kolejne czasy od pierwszego
                new_units.append(units[0])

                last = units[0][1]
                for unit in units[1:]:
                    last += self.all_unit[str(unit[0])].time_to_build * 60
                    new_units.append([unit[0], last])

            self.city_unit_progress.unit = json.dumps(new_units)

            next_at = units.pop()[1]
            for unit in units:
                if unit[1] < next_at: next_at = unit[1]
            self.city_unit_progress.next_at = datetime.datetime.fromtimestamp(next_at)

        self.city_unit_progress.save()

    def cancel_move_unit(self, move_id):
        from crims.city.models import CityUnit, MapMove, MapMoveGroup

        current_queue = MapMove.objects.get_by_user(user=self.engine.user.user)
        units = current_queue.units

        to_del = units[int(move_id)]
        to_del_grp = MapMoveGroup.objects.get(pk=to_del[2])

        # give units back
        city = CityUnit.objects.get(user=self.engine.user.user, city_id=int(to_del[0]))
        city_units = city.units
        for k, v in to_del_grp.units.iteritems():
            if not city_units.has_key(k): city_units[k] = 0
            city_units[k] += v

        city.unit = json.dumps(city_units)
        city.save()

        # delete
        del units[int(move_id)]
        to_del_grp.delete()

        current_queue.unit = json.dumps(units)
        current_queue.save()

    def get_sums(self, user_id=None, username=None):
        if user_id is not None:
            cu = CityUnit.objects.get_by_user(self.id, user_id=user_id)
            u = self.engine.user.get_by_id(user_id=user_id)
        elif username is not None:
            cu = CityUnit.objects.get_by_user(self.id, username=username)
            u = self.engine.user.get_by_id(username=username)
        else:
            cu = self.city_unit
            u = self.engine.user.profile

        sums = cu.get_sums()

        if u.default_city_id == self.id:
            sums[0] += int(u.total_attack)
            sums[1] += int(u.total_defense)

        return sums

    def move_units(self, post):
        from crims.city.models import MapMove, MapMoveGroup

        # Queue limitation check
        current_queue = MapMove.objects.get_by_user(user=self.engine.user.user)
        if self.engine.user.profile.is_premium:
            limit = settings.MAP_MOVE_QUEUE_LIMIT_PREMIUM
        else:
            limit = settings.MAP_MOVE_QUEUE_LIMIT
        if len(current_queue.units) >= limit:
            self.engine.log.message(message=_('Limit of moving units is %d' % limit))
            return

        # Start city validation
        try:
            s_city_id = int(post['city_id'])
        except (ValueError, KeyError):
            logging.warning('Start city id:%s is not valid integer' % str(post['city_id']))
            self.engine.log.message(message=_('Request is invalid'))
            return

        s_city = CityMap.objects.get_by_id(s_city_id)
        if s_city is None:
            logging.warning('Start city is not valid with ID:%d' % s_city_id)
            self.engine.log.message(message=_('Request is invalid'))
            return

        e_city = CityMap.objects.get_by_id(self.id)

        # Units validation
        try:
            req_units = {}
            for k, v in post.items():
                if k.find('unit_') != 0 or int(v) <= 0: continue
                req_units[int(k.replace('unit_', ''))] = int(v)
        except ValueError:
            logging.warning('POST is not valid')
            self.engine.log.message(message=_('Request is invalid'))
            return

        if len(req_units) == 0:
            self.engine.log.message(message=_('No unit selected'))
            return

        # Validate if user has units of each kind
        city_units = self.get_units(city_id=s_city_id)
        my_units = city_units.units

        for k, v in req_units.iteritems():
            if not my_units.has_key(str(k)) or int(my_units[str(k)]) < int(v):
                self.engine.log.message(message=_('Has not enough units to select'))
                return

        # MOVE...
        from crims.common.helpers._crims import calc_route

        transport_type = 'default'  # TODO: wprowadzic pozniej inne
        arrival_date = int(time.time() + int(
            calc_route(s_city.sector, s_city.position, e_city.sector, e_city.position) * 60.0 *
            settings.MOVE_TIME_PER_KM[transport_type]))

        # Take units
        for unit_id, unit_amount in req_units.iteritems():
            my_units[str(unit_id)] -= int(unit_amount)
            if my_units[str(unit_id)] == 0: del my_units[str(unit_id)]
        city_units.unit = json.dumps(my_units)
        city_units.save()

        # Make a move
        mvg = MapMoveGroup()
        mvg.unit = json.dumps(req_units)
        mvg.save()

        current_units = current_queue.units
        if len(current_units) == 0:
            current_queue.next_at = datetime.datetime.fromtimestamp(arrival_date)
        else:
            current_queue.next_at = datetime.datetime.fromtimestamp(min([x[3] for x in current_queue.units]))

        current_units.append([s_city_id, self.id, mvg.id, arrival_date])
        current_queue.unit = json.dumps(current_units)
        current_queue.save()

        self.engine.log.message(message=_('Units are moving'))
        return True

    def get_all_cities(self):
        from crims.city.models import CityUnit

        units = CityUnit.objects.get_all_cities(user=self.engine.user.user)
        cities = CityMap.objects.get_names_list([x.city_id for x in units])

        active_city_id = self.engine.user.profile.active_city_id
        data = []
        for unit in units:
            if unit.city_id == active_city_id: continue
            total = sum(unit.units.values())
            if total == 0: continue

            data.append((int(unit.city_id), cities[long(unit.city_id)].name, total))

        return data

    def get_units(self, city_id=None, user=None):
        city_id = city_id or self.engine.user.profile.active_city_id
        user = user or self.engine.user.user
        return CityUnit.objects.get_by_user(city_id=city_id, user=user)

    def city_units_list(self, city_id=None):
        units_list = {}
        if city_id is None:
            city_unit = self.city_unit
        else:
            city_unit = self.get_units(city_id)

        for unit_id, unit_count in city_unit.units.iteritems():
            units_list[unit_id] = (
            self.UNIT[self.all_unit[unit_id].name], self.all_unit[unit_id].attack, self.all_unit[unit_id].defense,
            unit_count)
        return units_list

    # --- Tribute

    def do_tribute(self, bld_type, bld_owner):
        import random
        from crims.city.models import CityUnit
        from crims.common.helpers._crims import fight

        if self.engine.city.city_unit.next_tribute_at > datetime.datetime.now():
            self.engine.log.message(message=_("Can do this right now"))
            return

        try:
            ids = self.city_building.items[bld_type][bld_owner]
        except KeyError:
            logging.error('No bld_type:%s or bld_owner:%s in city_building.items' % (str(bld_type), str(bld_owner)))
            self.engine.log.message(message=_("Error"))
            return

        try:
            job = self.all_tribute[str(random.choice(ids))]
        except KeyError, ValueError:
            logging.error('No tribute_id')
            self.engine.log.message(message=_("Error"))
            return

        self.engine.register('job')

        attacker = self.city_unit
        attacker_sums = self.get_sums()

        if bld_owner == '0':
            defender_sums = (settings.BIZ_DETAILS[bld_type]['attack'], settings.BIZ_DETAILS[bld_type]['defense'], 0)
        else:
            defender = CityUnit.objects.get_by_user(self.id, username=bld_owner)
            defender_sums = self.get_sums(username=bld_owner)

        result = fight(attacker_sums[0], attacker_sums[1], attacker_sums[2], defender_sums[0], defender_sums[1],
                       defender_sums[2])

        # local gang
        if bld_owner == '0':
            if result[0] == 1:  # won with local
                self.engine.log.message(
                    message=_("This building is now yours. Local gang may not be very happy about it, but who cares!"))
                self.engine.user.profile.add_per_day('tribute', job.base_per_day_cash, job.id)
            else:  # lost with local
                self.engine.log.message(message=_(
                    "Local gang is too strong for you. Build more units and try again later or choose someone else!"))
        # opponent
        else:
            if result[0] == 1:  # won with opponent
                self.engine.log.message(message=_(
                    "This building is now yours. %(bld_owner)s may not be very happy about it, but who cares!") % {
                                                'bld_owner': bld_owner})

                self.engine.user.get_by_id(username=bld_owner).remove_per_day('tribute', job.id)
                self.engine.user.profile.add_per_day('tribute', job.base_per_day_cash, job.id)

            else:  # lost with opponent
                self.engine.log.message(message=_(
                    "%(bld_owner)s is too strong for you. Build more units and try again later or choose someone else!") % {
                                                'bld_owner': bld_owner})

        if int(result[1]) > 0 or int(result[2]) > 0:
            self.engine.log.message(message=_("Lost units: %(died)d") % {'died': result[1]})

        # show stat updates
        if result[0] == 1:
            if bld_owner == '0':
                multiply = 1.0
            else:
                multiply = 2.0  # bonus for beating other players

            plus_stats = job.get_new_stats(multiply)
            self.engine.job.update_profile_with_result(plus_stats)
            self.engine.log.message(
                message="""<br/><div %s>%s:<br/><span class='attack'>&nbsp;</span>+%5.2f<br/><span class='defense'>&nbsp;</span>+%5.2f<br/><span class='respect'>&nbsp;</span>+%5.2f</div>""" % (
                "style='width: 70%; float: left;'", _("Your stats increased"), plus_stats['attack'],
                plus_stats['defense'], plus_stats['respect']))

        # Streams + triggers
        if result[0] == 1:
            if self.city_building.move_owner(bld_type, job.id, bld_owner, self.engine.user.user):
                self.engine.stream.trigger('building_attack_done')
                if bld_owner == '0':
                    self.engine.stream.post('city_attack_won', 'Local gang|%s|%s|<a href="%s">%s</a>' % (
                    bld_type, job.name, reverse('city_enter', args=[self.id, ]), self.city_map.name))
                    # self.engine.stream.post('city_defense_lost', '')
                    self.engine.stream.post_to_city_wall('city_new_bld_owner',
                                                         '%s|%s|Local gang|<a href="%s">%s</a>' % (bld_type, job.name,
                                                                                                   reverse('profile',
                                                                                                           args=[
                                                                                                               self.engine.user.user, ]),
                                                                                                   self.engine.user.user),
                                                         city_id=self.id, is_public=True)

                else:
                    bld_owner_name = self.engine.user.get_by_id(username=bld_owner).user

                    self.engine.stream.post('city_attack_won', '<a href="%s">%s</a>|%s|%s|<a href="%s">%s</a>' % (
                    reverse('profile', args=[bld_owner, ]), bld_owner, bld_type, job.name,
                    reverse('city_enter', args=[self.id, ]), self.city_map.name))
                    # self.engine.stream.post('city_defense_lost', '')
                    self.engine.stream.post_to_city_wall('city_new_bld_owner',
                                                         '%s|%s|<a href="%s">%s</a>|<a href="%s">%s</a>' % (
                                                         bld_type, job.name,
                                                         reverse('profile', args=[bld_owner_name, ]), bld_owner_name,
                                                         reverse('profile', args=[self.engine.user.user, ]),
                                                         self.engine.user.user), city_id=self.id, is_public=True)
                    self.engine.stream.trigger('building_defense_failed', user=bld_owner_name)

                attacker.next_tribute_at = datetime.datetime.now() + datetime.timedelta(hours=2)
                attacker.save()

            else:
                logging.error('Problem with moving building owner...')  # TODO: more info
                self.engine.log.message(message=_("Error"))

        else:
            self.engine.stream.trigger('building_attack_failed')
            if bld_owner != '0':
                self.engine.stream.trigger('building_defense_done',
                                           user=self.engine.user.get_by_id(username=bld_owner).user)

        if result[1] > 0:
            attacker.kill_units(result[1])
            self.engine.stream.trigger('city_units_lost', result[1])
        if result[2] > 0 and bld_owner != '0':
            defender.kill_units(result[2])
            self.engine.stream.trigger('city_units_lost', result[2],
                                       user=self.engine.user.get_by_id(username=bld_owner).user)

    # --- Production

    def produce_item(self, type, name, amount):
        try:
            item = self.all_product[type][name]
        except KeyError:
            logging.warning("Product with TYPE=%s and NAME=%s NOT FOUND" % (str(type), str(name)))
            return

        try:
            amount = int(amount)
            price = int(item.base_price)  # * level
            speed = int(item.base_speed)  # * level
        except ValueError:
            logging.warning("One of provided values incorrect")
            return

        # if len(self.city_unit_progress.units) >= self.engine.settings.MAX_SECURITY_BUILD_QUEUE:
        # 	self.engine.log.message(message=_('Maximum length of the queue reached'))
        # 	return

        if not self.engine.user.profile.has_enough('cash', price * amount):
            self.engine.log.message(message=_('Not enough cash'))
            return

        if len(self.city_product_progress.items) == 0:
            self.city_product_progress.item = "[[\"%s\",\"%s\",%d,%d]]" % (
            str(item.type), str(item.name), amount, int(time.time()) + speed * amount)
            self.city_product_progress.next_at = datetime.datetime.fromtimestamp(int(time.time()) + speed * amount)
        else:
            last_item = self.city_product_progress.items.pop()
            if last_item[2] < int(time.time()): last_item[2] = int(time.time())

            self.city_product_progress.item = self.city_product_progress.item[:-2] + "],[\"%s\",\"%s\",%d,%d]]" % (
            str(item.type), str(item.name), int(amount), int(last_item[2]) + speed * amount)

        self.engine.user.profile.spend('cash', price * amount)
        self.city_product_progress.save()

        self.engine.log.message(message=_("Production started"))

    # --- Bank

    def bank_deposit(self, amount):
        try:
            amount = int(amount)
            if amount < 0:
                self.engine.log.message(message=_("You're funny"))
                return
        except ValueError:
            return

        if int(self.engine.user.profile.cash) < amount:
            self.engine.log.message(message=_("You don't have $%(amount)d") % {'amount': amount})
            return

        self.engine.user.profile.to_bank(amount)
        self.engine.log.message(message=_("$%(amount)d deposited") % {'amount': amount})
        self.engine.stream.trigger('bank_deposit')

    def bank_withdraw(self, amount):
        try:
            amount = int(amount)
            if amount < 0:
                self.engine.log.message(message=_("You're funny"))
                return
        except ValueError:
            return

        if int(self.engine.user.profile.cash_in_bank) < amount:
            self.engine.log.message(message=_("You don't have $%(amount)d in deposit!") % {'amount': amount})
            return

        self.engine.user.profile.from_bank(amount)
        self.engine.log.message(message=_("$%(amount)d withdrawed") % {'amount': amount})
        self.engine.stream.trigger('bank_withdraw')

    # --- Prison

    def prison_service(self, action_type, amount=None):
        profile = self.engine.user.profile

        if action_type == 'low_heat':
            if not profile.has_enough('credit', settings.LOW_HEAT_CREDITS):
                self.engine.log.message(message=_(
                    "You need %(credits)s credits to do this. <a href='%(link)s'>Add more credits</a>." % {
                    'credits': settings.LOW_HEAT_CREDITS, 'link': reverse('payment')}))
                return

            profile.spend('credit', settings.LOW_HEAT_CREDITS)
            profile.heat = 0
            profile.save()

            self.engine.log.message(message=_("Heat lowed down to 0!"))
            self.engine.stream.trigger('bribe')
            return

            profile.spend('credit', settings.RELEASE_FROM_JAIL_CREDITS)
            profile.release_from_jail()

        self.engine.log.message(message=_("Greetings from warden. You've got released from prison!"))

    def prison_bribe(self, amount):
        try:
            value = int(amount)
            if value <= 0:
                self.engine.log.message(message=_("I only accept cash"))
                return
        except ValueError:
            self.engine.log.message(message=_("I only accept cash"))
            return

        if self.prison_is_enough_bribe(amount):  # success
            profile.spend('cash', amount)
            profile.heat = 0
            profile.release_from_jail()

            self.engine.log.message(message=_("Okey buddy, you're free. Move quickly."))
        else:  # epic fail
            profile.spend('cash', amount)
            profile.save()

            self.engine.log.message(message=_("Are you kidding me? Get lost!"))

    def prison_is_enough_bribe(self, amount):
        if int(amount) >= int(self.engine.user.profile.respect) / 10:
            return True
        else:
            return False

    # --- Others

    def get_other_cities(self):
        if self.other_cities is None:
            self.other_cities = CityUnit.objects.get_all_cities(user=self.engine.user.user)
        return self.other_cities

    # --- Sort

    def sort_unit(self, to_sort_list):
        def sorter(a, b):
            if a.attack > b.attack:
                return 1
            elif a.attack == b.attack:
                return 0
            else:
                return -1

        to_sort_list.sort(sorter)
        return to_sort_list

    def sort_tribute(self, to_sort_list):
        def sorter(a, b):
            if self.TRIBUTE_ORDER.index(a.type) > self.TRIBUTE_ORDER.index(b.type):
                return 1
            elif self.TRIBUTE_ORDER.index(a.type) == self.TRIBUTE_ORDER.index(b.type):
                return 0
            else:
                return -1

        to_sort_list.sort(sorter)
        return to_sort_list
