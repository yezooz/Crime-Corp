# -*- coding: utf-8 -*-
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db import connection
from django.core.cache import cache
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

import math
import crims.common.logger as logging
import cPickle as pickle
from crims.job.models import Job as JobModel, JobTribute, UserJob
from crims.item.models import Item, Inventory


class Job(object):
    def __init__(self, engine):
        self.engine = engine

    def set_job_type(self, job_type, tab='0|0'):

        if job_type == 'robbery':
            self.all_robbery = {}

            self.user_job = UserJob.objects.get_by_user(user=self.engine.user.user)
            for job in JobModel.objects.get_robberies(tab):
                mastery = self.user_job.mastery

                if not mastery.has_key(str(job.id)):
                    mastery[str(job.id)] = '1|0'
                job.mastery_lvl, job.mastery = mastery[str(job.id)].split('|')

                self.all_robbery[str(job.id)] = job

            self.ROBBERY = {
                'Homeless': _('Homeless'), 'Grandma': _('Grandma'), 'Kid & Lollipop': _('Kid & Lollipop'),
                'Sugar from restaurant': _('Sugar from restaurant'), 'Laptop': _('Laptop'),
                'Car break-in': _('Car Break-in'), 'Bar of chocolate': _('Bar of chocolate'),
                'Hubcaps from parking lot': _('Hubcaps from parking lot'), 'ATM': _('ATM Machine'),
                'Few beers from the shop': _('Few beers from the shop'), 'Money Exchange': _('Money Exchange'),
                'Jewelery': _('Jewelery'), 'Student': _('Student'), 'Mr. Postman': _('Mr. Postman'),
                'Tourist with camera': _('Tourist with camera'),
                'Alloy wheels from parking lot': _('Alloy wheels from parking lot'),
                'Silver tableware from restaurant': _('Silver tableware from restaurant'), 'Dorm Room': _('Dorm Room'),
                'Valuable package': _('Valuable package'),
                'Computer set from Apartment': _('Computer set from Apartment'), 'Gas Station': _('Gas Station'),
                'Pack of HD Movies': _('Pack of HD Movies'), 'Microwave': _('Microwave'),
                'Blu-ray player': _('Blu-ray player'), 'HD Cam': _('HD Cam'), '42" HDTV': _('42" HDTV'),
                '60" HDTV': _('60" HDTV'),
                }

            self.ROBBERY_REQ = {
                'skills': _('Skills'), 'members': _('Members'), 'cars': _('Cars'), 'ladies': _('Ladies')
            }

    def update_profile_with_result(self, result, job=None):
        profile = self.engine.user.profile

        if result['result'] is True:
            # multipliers
            result['attack'] = float(result['attack']) * float(profile.attack_mod)
            result['defense'] = float(result['defense']) * float(profile.defense_mod)
            result['respect'] = float(result['respect']) * float(profile.respect_mod)
            result['cash'] = float(result['cash']) * float(profile.cash_mod)

            profile.cash += int(result['cash'])
            profile.base_attack += Decimal(str(result['attack']))
            profile.total_attack += Decimal(str(result['attack']))
            profile.team_attack += Decimal(str(result['attack']))
            profile.base_defense += Decimal(str(result['defense']))
            profile.total_defense += Decimal(str(result['defense']))
            profile.team_defense += Decimal(str(result['defense']))
            profile.base_respect += Decimal(str(result['respect']))
            profile.total_respect += Decimal(str(result['respect']))
            profile.team_respect += Decimal(str(result['respect']))
            if job is not None:
                profile.heat += int(int(job.heat) * float(profile.heat_mod))

            # max_heat
            if profile.max_heat >= settings.MAX_HEAT:
                profile.max_heat = settings.MAX_HEAT
            else:
                max_should_be = int(profile.total_respect / 100) + 100
                if profile.max_heat < max_should_be:
                    profile.max_heat = max_should_be

                if profile.heat > profile.max_heat * 2:
                    profile.heat = profile.max_heat * 2

            # loot
            if result.has_key('loot') and result['loot'] is not None:
                result['loot_item'] = Item.objects.get_by_id(result['loot'])
                if settings.ALL_ITEM.has_key(int(result['loot'])):
                    result['loot_item'].name = settings.ALL_ITEM[int(result['loot'])][self.engine.pref_lang]

                inventory = Inventory.objects.get_by_user(user=profile.user)
                inventory.buy_item(str(result['loot']))
                inventory.activate(str(result['loot']))
                profile.total_attack += Decimal(str(result['loot_item'].attack))
                profile.total_defense += Decimal(str(result['loot_item'].defense))
                profile.total_respect += Decimal(str(result['loot_item'].respect))
                result['attack'] += result['loot_item'].attack
                result['defense'] += result['loot_item'].defense
                result['respect'] += result['loot_item'].respect

            # mastery
            if job and self.user_job.done_job(job.id, job.mastery_incr):
                # add some respect
                pass

            profile.save()

        elif result['result'] == 'JAIL':
            # failed / set up message
            profile.go_to_jail()

        elif result['result'] == 'NO_CHANCE':
            profile.heat += int(job.heat * 2 * float(profile.heat_mod))
            if profile.heat > profile.max_heat * 2:
                profile.heat = profile.max_heat * 2
            profile.save()

    def _do_job(self, job):
        profile = self.engine.user.profile
        result = job.do_job(profile)

        if result['result'] is True:
            self.update_profile_with_result(result, job)

            self.engine.stream.trigger('robbery_done')
            self.engine.stream.trigger('robbery_%d_done' % int(job.id))

            if profile.heat >= profile.max_heat:
                new_form = ''
            else:
                new_form = """<form action="%s" method="post"><input type="hidden" name="job_id" value="%s"/><input type="submit" value="%s" style="font-size: 13px"/></form>""" % (
                reverse('robbery', args=[job.level.split('|')[0], job.level.split('|')[1]]), job.id, _('Do it again'))

            if result['loot'] is not None:
                loot_info = '%s: %s<br/><img src="%s"/>' % (
                _('Loot'), result['loot_item'], ''.join((settings.MEDIA_URL, result['loot_item'].image_filename)))
            else:
                loot_info = ''

            self.engine.log.message(
                message="""<div %s>%s<br/><span class='attack'>&nbsp;</span>+%5.2f<br/><span class='defense'>&nbsp;</span>+%5.2f<br/><span class='respect'>&nbsp;</span>+%5.2f<br/><span class='cash'>&nbsp;</span>+$%5.2f<p>%s +%s%s</p><p>%s</p></div><div %s><p>%s</p></div>""" % (
                "style='width: 70%; float: left;'", _("You did it!"), result['attack'], result['defense'],
                result['respect'], result['cash'], _('Mastery'), job.mastery_incr, "%", loot_info,
                "style='width: 20%; float: left;'", new_form))

        elif result['result'] == 'JAIL':
            self.update_profile_with_result(result, job)

        elif result['result'] == 'NO_CHANCE':
            self.update_profile_with_result(result, job)
            self.engine.log.message(message=_("Failed! Be aware as police has now eye on you!"))

        elif result['result'] == 'NO_REQ':
            self.engine.log.message(message=_("You don't match all requirements"))

        elif result['result'] == 'NO_PREMIUM':
            self.engine.log.message(message=_(
                "This job is for supporters only. How to become a supporter <a href='%s'>read here</a>" % reverse(
                    'premium')))

    # --- job_type related

    def do_robbery(self, job_id):
        try:
            job = self.all_robbery[str(job_id)]
        except KeyError:
            return
        except ValueError:
            return

        self._do_job(job)

    def sort(self, to_sort_list):
        def sorter(a, b):
            if a.is_premium == b.is_premium:
                if a.req_respect > b.req_respect:
                    return 1
                elif a.req_respect == b.req_respect:
                    return 0
                else:
                    return -1
            else:
                if a.is_premium:
                    return 1
                else:
                    return -1

        to_sort_list.sort(sorter)
        return to_sort_list
