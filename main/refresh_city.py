# -*- coding: utf-8 -*-
import os
import getopt

import sys
import time
import datetime

sys.path.append(os.path.dirname(__file__) + "../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'crims.settings'

import simplejson as json
# from django.db import connection
from django.conf import settings
from django.core.cache import cache
import crims.common.logger as logging

import random, datetime, math
from crims.job.models import JobTribute
from crims.city.models import CityMap, CityBuilding


class CityRefresh(object):
    def __init__(self, profile, city_id=None):
        self.profile = profile
        self.city_id = city_id or profile.default_city_id

        self.city_map = CityMap.objects.get_by_id(self.city_id)
        self.city_building = CityBuilding.objects.get_by_city_id(self.city_id)

    def do_refresh(self):
        (self.report, notify) = self.calc_tribute()

        # print 'report:', self.report, ' notify', notify
        # print '------------------------------------'

        self.calc_building()

        self.city_building.save()
        self.profile.save()

        cache.delete('city_building_%s' % self.profile.user.id)
        # cache.delete('city_')

        # if in_blds is not None and int(in_blds) > 0:
        # 	self.engine.stream.trigger('new_tributes')
        # 	self.engine.stream.post('city_new_biz')
        # 	logging.debug('%s: %d new tributes' % (self.user, int(in_blds)))

        # Notify
        # ...

        return

    def calc_tribute(self):
        tribute_groups = {}
        for job in JobTribute.objects.all():
            if not tribute_groups.has_key(job.type): tribute_groups[job.type] = []
            tribute_groups[job.type].append(int(job.id))

        logging.debug("%s tributes being recalculated" % (str(self.profile.user)))

        user_tribute_groups = {}
        for group_type, group_items in tribute_groups.iteritems():
            user_tribute_groups[group_type] = {}
            user_tribute_groups[group_type]['todo'] = []
            user_tribute_groups[group_type]['done'] = []

            done_group = self.city_building.items.get(group_type)
            if done_group is None:
                user_tribute_groups[group_type]['todo'] = group_items
                continue

            done = []
            [done.extend(x) for x in done_group.values()]
            for item in group_items:
                if str(item) in done:
                    user_tribute_groups[group_type]['done'].append(str(item))
                else:
                    user_tribute_groups[group_type]['todo'].append(str(item))

        in_list_count = 0
        in_list_notify = []
        out_list_count = 0
        out_list_notify = []
        list_report = {}
        for group_type, group_items in user_tribute_groups.iteritems():
            total = len(group_items['done'])

            try:
                ratio = float(self.city_map.population) / (total * settings.BIZ_PER_CAPITA[group_type])
            except ZeroDivisionError:
                ratio = float(self.city_map.population) / (1 * settings.BIZ_PER_CAPITA[group_type])

            # print '--->', group_type, '<---'
            # print 'GOT:', total, group_items['done']
            # print 'RATIO:', ratio, '(1 per capita',settings.BIZ_PER_CAPITA[group_type],')'

            if ratio < 0.8:  # remove tributes
                to_out = total - int(math.floor(float(self.city_map.population) / settings.BIZ_PER_CAPITA[group_type]))
                if len(group_items['done']) == 0 or to_out == 0: continue

                out_list = []
                for i in xrange(0, to_out):
                    choice = random.choice(group_items['done'])
                    if choice not in out_list: out_list.append(choice)
                # specjalnie nie ponawiamy randoma
                out_list_notify.append(self.city_building.remove(group_type, out_list))
                out_list_count += len(out_list)
                list_report[group_type] = -(len(out_list))
            # print 'out:', out_list

            elif ratio > 1.0:  # add tributes
                to_in = int(math.floor(float(self.city_map.population) / settings.BIZ_PER_CAPITA[group_type])) - total
                in_list = []

                if to_in == 0 or len(group_items['todo']) == 0: continue

                if to_in >= len(tribute_groups[group_type]):
                    in_list = [str(x) for x in tribute_groups[group_type]]
                    in_list_count += len(in_list)
                    list_report[group_type] = len(in_list)

                    self.city_building.add(group_type, in_list)
                    continue

                for i in xrange(0, to_in):
                    choice = str(random.choice(group_items['todo']))
                    if choice not in in_list: in_list.append(choice)
                    # specjalnie nie ponawiamy randoma
                    if len(group_items['done']) + len(in_list) >= len(tribute_groups[group_type]): break
                self.city_building.add(group_type, in_list)

                in_list_count += len(in_list)
                list_report[group_type] = len(in_list)
            # print 'in:', in_list
            else:
                continue

        if in_list_count != 0: in_list_notify.append(str(self.profile.user))
        return (list_report, set(in_list_notify))

    def calc_building(self):
        self.all_slots = [[] for x in xrange(0, settings.MAX_SLOTS)]
        self.all_blds = []
        self.db_density = self.city_map.densities

        self.all_blds = ['1', '1', '3', '4', '4', '8', '8', '8', '8', '9', '1', '1', '3', '4', '4', '8', '8', '8', '8',
                         '9', '1', '1', '3', '4', '4', '8', '8', '8', '8', '9', '1', '1', '3', '4', '4', '8', '8', '8',
                         '8', '9', '1', '1', '3', '4', '4', '8', '8', '8', '8', '9']  # TEMP

        # Industry
        for bld_type, bld_count in self.report.iteritems():
            for i in xrange(0, bld_count):
                self.all_blds.append(settings.BIZ_BUILDING[bld_type])

        # print 'Industry'

        # Living
        self.pop_to_put = self.city_map.used_population - self.city_map.population
        self.pop_density = float(self.city_map.used_population) / float(self.city_map.population)
        self.pop_lvl = self._get_density_lvl([self.pop_density, ])

        # print 'Living'

        # print self.all_blds

        # Density
        self.order = [4, 3, 5, 2, 6, 1, 7, 8]
        self.sec_order = [((sec - 1) * settings.MAX_BUILDINGS_PER_SECTOR, sec * settings.MAX_BUILDINGS_PER_SECTOR) for
                          sec in self.order]

        slots = self.city_map.slots
        self.density = [0.0 for x in xrange(0, settings.MAX_SLOTS)]

        i = 0
        for (a, b) in self.sec_order:
            # obliczamy ile budynkow na ile trawy przypada na jeden boks
            c = 0
            for x in slots[a:b]:
                self.all_slots[self.order[i] - 1].append(x)
                if int(x) == 0: continue
                c += 1
            self.density[self.order[i] - 1] = (float(c) / settings.MAX_BUILDINGS_PER_SECTOR)
            i += 1

        self._put_buildings()

        del self.all_blds

        new_slots = []
        for i in xrange(0, settings.MAX_SLOTS):
            new_slots.extend(self.all_slots[self.order[i] - 1])

        self.city_map.slot = json.dumps(new_slots)
        self.city_map.density = json.dumps([float("%.2f" % round(density, 2)) for density in self.density])
        self.city_map.save()

    def _put_buildings(self):

        # Allocate
        lvl = self._get_density_lvl(self.density)
        while True:
            break
        slot_no = self.density.index(min(self.density))

        for bld in self.all_blds:
            # print '------------------------------'
            # print 'bld', bld

            slot = self.all_slots[slot_no]

            if 0 in slot:
                to_alloc = slot.index(0)
            elif lvl - 1 in slot:
                to_alloc = slot.index(lvl - 1)
            elif lvl in slot:
                to_alloc = slot.index(lvl)
            else:
                # logging.warning('Cannot find proper field to replace. %s / %s' % (self.profile.user, self.city_id))
                continue

            # print 'slot', slot_no, 'lvl', lvl, 'to_alloc', to_alloc

            # new density
            c = 0
            for x in self.all_slots[slot_no]:
                if int(x) == 0: continue
                c += 1
            self.density[slot_no] = (float(c) / settings.MAX_BUILDINGS_PER_SECTOR)

            self.all_slots[slot_no][to_alloc] = int(bld)

            # new slot_no based on new density
            lvl = self._get_density_lvl(self.density, self.density[slot_no])

            if lvl > self._get_density_lvl(self.density) + 1:
                slot_no = self.density.index(min(self.density))

    def _get_density_lvl(self, density, for_min=None):
        curr_min = for_min or min(density)
        if curr_min < .6:         return 1
        if .6 <= curr_min < .7:  return 2
        if .7 <= curr_min < .85: return 3
        return 4


if __name__ == '__main__':
    from django.contrib.auth.models import User
    from crims.userprofile.models import UserProfile

    for user in User.objects.filter(is_active=True):
        profile = UserProfile.objects.get_by_id(user_id=user.id)
        if profile is not None:
            r = CityRefresh(profile)
            r.do_refresh()
        else:
            logging.error('Disabling %s due to no profile' % user)
            user.is_active = False
            user.save()
