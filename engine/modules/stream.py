# -*- coding: utf-8 -*-
import simplejson as json
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.template.loader import render_to_string

import crims.common.logger as logging
from crims.city.models import CityWall, CityMap
from crims.main.models import News, UserStream, UserFBSpamQueue
from crims.userprofile.models import UserStat


class Stream(object):
    def __init__(self, engine):
        self.engine = engine

        self.general_news = []
        self.city_wall = []
        self.user_news = []  # TODO: later
        self.load_news()

        self.stat = UserStat.objects.get_by_user(user=engine.user.user)

        self.TXT = {
            'auction_won': _('You won auction of [[0]]. New car should be already in your garage.'),
            'auction_lost': _('You lost auction of [[0]]. Try your luck next time.'),
            'auction_sold': _('You sold [[0]] to [[1]] for $[[2]]'),
            'auction_not_sold': _('[[0]] was not sold due to lack of offers. Sorry.'),
            'auction_outbid': _('Someone outbidded you on auction of [[0]]. Rethink your offer before it\'s too late.'),
            'skill_done': _('Skill [[0]] learnt'),
            'credit_awarded': _('Received [[0]] free credit for your activity'),
            # City Wall
            'city_visit': _('[[0]] visited your city'),
            'city_new_owner': None,
            'city_new_bld_owner': _('[[1]] is not owned by [[2]] anymore. New owner is [[3]].'),
            'tribute_new': _('You got new buildings to extort as your city keep getting bigger and bigger.'),
            'daily_income': _('Your income for yesterday $[[0]].'),
            # TODO: new
            'city_attack_won': _('[[0]] lost fight with you. You took control over [[1]] [[2]] in the city [[3]].'),
            'city_attack_lost': _(
                'You lost a fight against [[0]] [[1]] over [[2]] in the city [[3]]. Get your shit together and try again later.'),
            'city_defense_won': _('Your people repulsed attack of [[0]] [[1]] on building [[2]] in the city [[3]].'),
            'city_defense_lost': _(
                'You lost a fight against [[0]] and [[1]] [[2]] is not in your hands anymore. We\'re loosing money, do something!'),
            'city_units_lost': _('Lost units: [[0]].'),
            'unit_hired': _('[[0]] hired in the city [[1]]'),
            'unit_moved': _('[[0]] arrived to [[1]]'),
        }

        self.STREAM = {
            # Auction
            'auction_won': {
                'notify': ('facebook', 'facebook_notify_random', 'email'),
                'catalog': 'other',
                'fb': _('won auction of [[0]]'),
            },
            'auction_lost': {
                'notify': None,
                'catalog': 'other',
            },
            'auction_sold': {
                'notify': ('facebook', 'facebook_notify_random', 'email'),
                'catalog': 'other',
                'fb': _('sold [[0]] on auction for $[[2]]'),
            },
            'auction_not_sold': {
                'notify': None,
                'catalog': 'other',
            },
            'auction_outbid': {
                'notify': None,
                'catalog': 'other',
            },

            # City
            'city_entered': {
                'notify': None,
                'catalog': 'city',
            },
            'city_new_biz': {
                'notify': None,
                'catalog': 'city',
                'fb': _('got new buildings to extort'),
            },
            'city_unit_hired': {
                'notify': None,
                'catalog': 'city',
            },
            'city_unit_moved': {
                'notify': None,
                'catalog': 'city',
            },
            'city_attack_won': {
                'notify': ('im'),
                'catalog': 'city',
                'fb': _('[[0]] lost fight with you. You took control over [[1]] [[2]] in the city [[3]].'),
            },
            'city_attack_lost': {
                'notify': ('im',),
                'catalog': 'city',
                'fb': _(
                    'You lost a fight against [[0]] [[1]] over [[2]] in the city [[3]]. Get your shit together and try again later.'),
            },
            'city_defense_won': {
                'notify': ('im'),
                'catalog': 'city',
                'fb': _('Your people repulsed attack of [[0]] [[1]] on building [[2]] in the city [[3]].'),
            },
            'city_defense_lost': {
                'notify': ('im',),
                'catalog': 'city',
                'fb': _(
                    'You lost a fight against [[0]] and [[1]] [[2]] is not in your hands anymore. We\'re loosing money, do something!'),
            },
            'city_units_lost': {
                'notify': ('im',),
                'catalog': 'city',
            },
            'city_new_bld_owner': {
                'notify': ('im',),
                'catalog': 'city',
            },

            # Gang
            'gang_invite_sent': {
                'notify': None,
                'catalog': 'gang',
            },
            'gang_invite_accepted': {
                'notify': None,
                'catalog': 'gang',
            },
            'gang_invite_refused': {
                'notify': None,
                'catalog': 'gang',
            },
            'gang_member_promoted': {
                'notify': None,
                'catalog': 'gang',
            },
            'gang_member_demoted': {
                'notify': None,
                'catalog': 'gang',
            },

            # Item
            'item_received': {
                'notify': None,
                'catalog': 'gift',
            },

            # Job
            'robbery_done': {
                'notify': None,
                'catalog': 'other',
            },
            'robbery_failed': {
                'notify': None,
                'catalog': 'other',
            },
            'special_done': {
                'notify': None,
                'catalog': 'other',
            },
            'special_failed': {
                'notify': None,
                'catalog': 'other',
            },

            # Msg
            'msg_received': {
                'notify': None,
                'catalog': 'msg',
            },
            'msg_gang_received': {
                'notify': None,
                'catalog': 'gang',
            },
            'msg_spam_received': {
                'notify': None,
                'catalog': 'msg',
            },

            # Others
            'bank_deposited': {
                'catalog': 'other',
            },
            'bank_withdrawed': {
                'catalog': 'other',
            },
            'skill_learnt': {
                'notify': ('im', 'facebook_notify_random'),
                'catalog': 'other',
                'fb': _('learnt skill [[0]]'),
            },
            'daily_income': {
                'notify': None,
                'catalog': 'other',
            },
            'credit_awarded': {
                'notify': None,
                'catalog': 'other',
            },

        }

    def load_news(self):
        city = CityMap.objects.get_by_id(self.engine.user.profile.active_city_id, self.engine.user.user.id)
        if city.owner_id == self.engine.user.user.id:
            public = False
        else:
            public = True

        self._general_news()
        self._user_news()
        self._city_wall(public)

    def _general_news(self):
        news = News.objects.get_latest()
        if news is not None:
            self.general_news = news

    def _city_wall(self, public=True):
        news = CityWall.objects.get_latest(city_id=self.engine.user.profile.active_city_id, is_public=public)
        if news is not None:
            self.city_wall = news

    def _user_news(self):
        news = UserStream.objects.get_latest(user=self.engine.user.user)
        if news is not None:
            self.user_news = news

    def trigger(self, name, log_val=None, stat_val=1, user=None):
        if user is None:
            stat = self.stat
        else:
            stat = UserStat.objects.get_by_user(user=user)

        stats = stat.stats
        if not stats.has_key(name):
            stats[name] = stat_val
        else:
            stats[name] += 1

        stat.stat = json.dumps(stats)
        stat.save()

    def post(self, action_type, title_replace='', content_replace='', fb='', user=None, user_id=None):
        un = UserStream()
        if user_id is None and user is None:
            un.user = self.engine.user.user
        elif user_id is not None:
            un.user = User.objects.get(pk=user_id)
        elif user is not None:
            un.user = user
        un.source = action_type
        un.title = title_replace
        un.content = content_replace
        un.save()

        if user is None and user_id is None:
            self.notify(self.engine.user.profile, action_type, title_replace, content_replace, fb)
        else:
            self.notify(self.engine.user.get_by_id(un.user.id), action_type, title_replace, content_replace, fb)

    def post_to_city_wall(self, action_type, title_replace='', content_replace='', fb='', user=None, user_id=None,
                          city_id=None, is_public=True):
        cw = CityWall()
        cw.city = CityMap.objects.get_by_id(city_id, self.engine.user.user.id)
        if user_id is None and user is None:
            cw.user = self.engine.user.user
        elif user_id is not None:
            cw.user = User.objects.get(pk=user_id)
        elif user is not None:
            cw.user = user
        cw.source = action_type
        cw.title = title_replace
        cw.content = content_replace
        cw.is_public = is_public
        cw.save()

        if user is None and user_id is None:
            self.notify(self.engine.user.profile, action_type, title_replace, content_replace, fb)
        else:
            self.notify(self.engine.user.get_by_id(user_id=un.user.id), action_type, title_replace, content_replace, fb)

    def translate(self, txt, trans_part):
        if len(trans_part) == 0 or txt.find('[[') < 0: return txt

        i = 0
        for text in trans_part.split('|'):
            try:
                text = text[:text.index('/') - 1]  # remove / from auction name
            except:
                pass
            txt = txt.replace('[[%d]]' % i, text)
            i = i + 1
        return txt

    # wstepny concept!
    def notify(self, profile, action_type, title_replace, content_replace, fb):
        """Email, facebook, gg, jabber, etc"""

        return  # temp

        if self.STREAM.has_key(action_type):
            for target in self.STREAM[action_type]['notify']:
                if target == 'email':
                    email = render_to_string('email/%s.html' % action_type, {
                        'username': profile.username,
                    })

                    rcp = profile.user.email
                    print 'send to %s' % rcp
                    print email

                elif target == 'facebook' and int(profile.fb_id) > 0:
                    # dodaje informacje do kolejki, a pozniej sesja fb wrzuca
                    fbq = UserFBSpamQueue()
                    fbq.user_id = profile.user.id
                    fbq.type = action_type
                    fbq.message = self.translate(self.STREAM[action_type]['fb'], title_replace)
                    if fb != '': fbq.details = fb
                    fbq.save()

                # elif target == 'jabber' and profile.jabber != '':
                # 	from crims.common.im.jabber import Jabber
                # 	j = Jabber()
                # 	j.message(profile.jabber, self.translate(self.TXT[action_type], title_replace) + ' http://www.crimecorp.com')

                # elif target == 'facebook_notify_random' and self.engine.settings.IS_FB and int(profile.fb_id) > 0:
                # 	message = "<a href='%s'>%s</a> %s" % (reverse('profile', args=[profile.user]), profile.user, self.translate(self.TXT_FB[action_type], title_replace))
                #
                # 	self.engine.facebook.send_notifications(self.engine.facebook.get_random_friends(5), message)
                # 	continue

                else:
                    pass
