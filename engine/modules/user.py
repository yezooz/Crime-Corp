# -*- coding: utf-8 -*-
import random

import simplejson as json
from django.conf import settings
from django.utils.translation import ugettext as _

import crims.common.logger as logging
import datetime
import time

# from django.db import models
# from django.db import connection
from crims.userprofile.models import UserProfile, Bonus, UserBonus, Skill, UserSkill
# from django.core.cache import cache

class User(object):
    def __init__(self, engine):
        self.engine = engine

        if self.engine.source == 'fb':
            from django.contrib.auth.models import User

            try:
                self.profile = UserProfile.objects.get(fb_id=self.engine.request.facebook.uid)
            except UserProfile.DoesNotExist:
                profile = UserProfile()
                profile.user = User.objects.create_user("fb_%s" % self.engine.request.facebook.uid,
                                                        "fb_%s@madfb.com" % self.engine.request.facebook.uid,
                                                        User.objects.make_random_password(length=10,
                                                                                          allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'))
                profile.username = "fb_%s" % self.engine.request.facebook.uid
                profile.fb_id = self.engine.request.facebook.uid
                profile.save()
                self.profile = profile

                # extra actions
                self.profile.add_log(log_type='register', log_type_id=self.profile.user.id, log='from facebook',
                                     ip=self.engine.request.META.get('REMOTE_ADDR'))

        else:
            self.profile = UserProfile.objects.get_by_id(self.engine.request.user.id)
            if self.profile is None:
                from django.contrib.auth import logout

                logout(self.engine.request)

        self.user = self.profile.user

        # username bug workaround
        if self.profile.username == '':
            self.profile.username = self.user.username
            self.profile.save()
            logging.warning('fixed username of %s' % self.user.username)

        self.SKILL = {
            'driving': _('Driving'),
            'shooting': _('Shooting'),
            'stealing': _('Stealing'),
            'security_breaking': _('Security breaking'),
            'negotiating': _('Negotiating'),
            'marketing': _('Marketing'),
            'business': _('Business running'),
            'smuggling': _('Smuggling'),
            'hacking': _('Hacking'),
            'natural_resources': _('Natural resource management'),
        }

    def __getattr__(self, name):
        if name == 'skills':
            self.skills = UserSkill.objects.get_by_user(user=self.user)
            return self.skills
        else:
            return self.__getattribute__(name)

    def cron_actions(self):

        # --- CRON-like
        self.heat_progress()
        self.city_progress()

        if self.profile.next_total_recalc:
            self.recalculate_total()
            self.profile.next_total_recalc = False
            self.profile.save()

        if self.profile.next_stats_recalc:
            self.recalculate_team(True)
            self.profile.next_stats_recalc = False
            self.profile.save()

        if self.profile.has_skills:
            self.execute_skills()

    def set_members(self):
        from crims.family.models import UserFamily

        self.members = UserFamily.objects.get_by_user(user=self.profile.user)

    def get_by_id(self, user_id=None, username=None):
        return UserProfile.objects.get_by_id(user_id=user_id, username=username)

    # --- Heat

    def heat_progress(self):
        if self.profile.next_heat_at > datetime.datetime.now(): return

        delta = (datetime.datetime.now() - self.profile.next_heat_at)

        diff = delta.seconds + delta.days * 3600 * 24
        diff = int(diff / int(self.engine.settings.LOW_HEAT_EVERY_SECONDS * float(self.profile.time_mod))) + 1

        self.profile.heat -= diff
        if self.profile.heat < 0:
            self.profile.heat = 0
        self.profile.next_heat_at = datetime.datetime.now() + datetime.timedelta(
            seconds=int(self.engine.settings.LOW_HEAT_EVERY_SECONDS * float(self.profile.time_mod)))
        self.profile.save()

    # --- City

    def city_progress(self):
        if self.profile.next_city_at > datetime.datetime.now(): return
        diff = (datetime.datetime.now() - self.profile.next_city_at).seconds / int(
            self.engine.settings.CITY_POP_EVERY_SECONDS)
        diff = int(diff) + 1

        for x in xrange(0, diff):
            self.engine.city.city_map.population += self.city_calc_change()
            if int(self.engine.city.city_map.population) < settings.MINIMUM_CITY_POPULATION:
                self.engine.city.city_map.population = settings.MINIMUM_CITY_POPULATION

        self.engine.city.city_map.save()
        self.profile.next_city_at = datetime.datetime.now() + datetime.timedelta(
            seconds=self.engine.settings.CITY_POP_EVERY_SECONDS)
        self.profile.save()

    def city_calc_change(self):
        change = self.engine.settings.DEFAULT_CITY_MOOD_DAILY_INCREASE['5'] / 24  # daily amount / 24
        change = int(int(change) * random.uniform(0.8, 1.2))

        # logging.debug("%s city_pop +%s" % (str(self.profile.user), str(change)))
        return change

    # --- Stats

    def recalculate_team(self, recalc_strengths=False):
        """Przelicza calkowita moc calego teamu"""
        logging.debug("recalculate_team() for %s" % self.profile.user)

        self.set_members()
        uf = self.members

        if recalc_strengths:
            uf._calculate_strengths()
            uf.save()

        self.profile.team_attack = int(uf.attack) + int(self.profile.total_attack)
        self.profile.team_defense = int(uf.defense) + int(self.profile.total_defense)
        self.profile.team_respect = int(uf.respect) + int(self.profile.total_respect)

        self.profile.save()

    def recalculate_total(self):
        """Przelicza calkowita moc wlasnych ludzi"""
        logging.debug("recalculate_total() for %s" % self.profile.user)

        totals = [int(self.profile.base_attack), int(self.profile.base_defense), int(self.profile.base_respect)]

        # myself + inventory
        if not hasattr(self.engine, 'item'):
            self.engine.register('item')
        self.engine.item.set_item_type('item')

        items_list = []
        [items_list.extend(x) for x in self.engine.item.active_inventory.itervalues()]
        for item in items_list:
            totals[0] += item.attack
            totals[1] += item.defense
            totals[2] += item.respect

        # garage
        self.engine.item.set_item_type('vehicle')
        for car in self.engine.item.garage[:int(self.engine.user.profile.max_cars)]:
            totals[2] += car.respect

        # minus
        self.profile.team_attack -= self.profile.total_attack
        self.profile.team_defense -= self.profile.total_defense
        self.profile.team_respect -= self.profile.total_respect

        # new values
        self.profile.total_attack = totals[0]
        self.profile.total_defense = totals[1]
        self.profile.total_respect = totals[2]
        self.profile.team_attack += self.profile.total_attack
        self.profile.team_defense += self.profile.total_defense
        self.profile.team_respect += self.profile.total_respect

        # max_heat
        max_should_be = int(self.profile.total_respect / 100) + 100
        if self.profile.max_heat < max_should_be:
            self.profile.max_heat = max_should_be

        self.profile.pref_lang = self.engine.pref_lang
        self.profile.save()

    # --- City

    def switch_city(self, city_id):
        self.profile.active_city(city_id)
        self.profile.save()

    # --- Bonus

    def add_bonus(self, bonus_id):
        bonus = Bonus.objects.get_by_id(bonus_id)
        my_bonuses = UserBonus.objects.get_by_user(self.user)

        self.engine.stream.trigger('bonus_added')
        self.engine.stream.trigger('bonus_%d_added' % int(bonus.id))

        if str(bonus.subject) not in my_bonuses.keys():  # has no this bonus subject
            ub = UserBonus()
            ub.user = self.user
            ub.bonus_subject = bonus.subject
            ub.bonus_name = bonus.name
            # activate
            ub.activate(self.profile, bonus)
            return

        for ub in my_bonuses[str(bonus.subject)]:
            if ub.bonus_name == bonus.name:
                ub.end_at = ub.end_at + datetime.timedelta(hours=int(bonus.period))
                ub.save()
                return
            else:
                ub = UserBonus()
                ub.user = self.user
                ub.bonus_subject = bonus.subject
                ub.bonus_name = bonus.name
                ub.start_at = datetime.datetime.now()
                ub.end_at = datetime.datetime.now()
                ub.save()

    # --- Skill

    def get_skills(self):
        self.all_skill = {}
        for skill in Skill.objects.get_all():
            if not self.all_skill.has_key(str(skill.name)): self.all_skill[str(skill.name)] = {}
            # if self.all_skill[str(skill.name)] is None: self.all_skill[str(skill.name)] = {}
            self.all_skill[str(skill.name)][str(skill.level)] = skill

        self.to_do_skill = {}
        for key, val in self.all_skill.iteritems():
            if key not in self.skills.skills:
                self.to_do_skill[key] = self.all_skill[str(key)]['1']
            elif key in self.skills.skills and self.skills.skills[key] < 10:
                self.to_do_skill[key] = val[str(int(self.skills.skills[key]) + 1)]

        return self.to_do_skill

    def do_skill(self, skill_type):
        try:
            skill = self.to_do_skill[skill_type]
        except KeyError:
            logging.warning('skill_type:%s does not exist' % skill_type)
            return

        if len(self.skills.queues) > 0:  # one queue for everyone?
            self.engine.log.message(message=_('You can\'t learn two things at the same time'))
            return

        if not self.profile.has_enough('cash', skill.cost):
            self.engine.log.message(message=_('Not enough cash'))
            return

        self.skills.queue = json.dumps(
            {skill.name: str(datetime.datetime.now() + datetime.timedelta(minutes=skill.time))[:19]})
        self.skills.save()
        self.profile.cash -= skill.cost
        self.profile.has_skills = True
        self.profile.save()

        logging.debug('%s: learning %s skill at lvl %s' % (self.user, skill.name, skill.level))
        self.engine.stream.trigger('skill_learn_start')
        self.engine.stream.trigger('skill_%d_learn_start' % int(skill.id))
        self.engine.log.message(message=_('Learning right now, come back later.'))

        return True

    def cancel_do_skill(self, skill_type):
        pass

    def execute_skills(self):
        self.get_skills()

        did = False
        for skill_type, day in self.skills.queues.iteritems():
            if datetime.datetime(*time.strptime(day, "%Y-%m-%d %H:%M:%S")[:6]) > datetime.datetime.now(): continue
            skill = self.to_do_skill[skill_type]
            skills = self.skills.skills
            skills[skill_type] = skill.level
            self.skills.skill = json.dumps(skills)
            did = True

            self.engine.stream.trigger('skill_learned')
            self.engine.stream.trigger('skill_%d_learned' % int(skill.id))

        if not did: return

        self.skills.queue = ''
        self.skills.save()
        self.profile.has_skills = False
        self.profile.save()
