# -*- coding: UTF-8
import simplejson as json
from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

import crims.common.logger as logging
import datetime
import math
import cPickle as pickle


class UserProfileManager(models.Manager):
    def get_by_id(self, user_id=None, username=None):
        if user_id is not None:
            key = 'user_%s' % user_id

            item = cache.get(key)
            if item is not None:
                return pickle.loads(str(item))
        else:
            key = None

        try:
            if username is not None:
                item = self.get(username__iexact=username)
            elif user_id is not None:
                item = self.get(user__id=user_id)
            else:
                logging.error('UserProfile not found. USER:%s, ID:%s' % (str(user), str(user_id)))
                return None

        except UserProfile.DoesNotExist:
            return None

        cache.set(key or 'user_%s' % item.user.id, pickle.dumps(item))
        return item

    def get_many_by_user_ids(self, user_ids):
        ret = []
        for uid in user_ids:
            ret.append(self.get_by_id(uid))
        return ret

    def get_by_invite_key(self, inv_key):
        if len(str(inv_key)) != 8: return None

        try:
            return self.get(invite_key__iexact=inv_key)
        except UserProfile.DoesNotExist:
            return None


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, verbose_name='User', related_name='crims_user')
    username = models.CharField(max_length=30)
    activation_key = models.CharField(max_length=32)
    invite_key = models.CharField(max_length=8)
    status = models.CharField(max_length=10)
    pref_lang = models.CharField(max_length=2, default='en')
    nationality = models.CharField(max_length=2, default='')

    base_attack = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['attack'])
    base_defense = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['defense'])
    base_respect = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['respect'])
    total_attack = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['attack'])
    total_defense = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['defense'])
    total_respect = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['respect'])
    team_attack = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['attack'])
    team_defense = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['defense'])
    team_respect = models.DecimalField(max_digits=12, decimal_places=2, default=settings.DEFAULT_STATS['respect'])

    heat = models.IntegerField(default=settings.DEFAULT_STATS['heat'])
    max_heat = models.IntegerField(default=settings.DEFAULT_STATS['max_heat'])
    cash = models.IntegerField(default=settings.DEFAULT_STATS['cash'])
    cash_in_bank = models.IntegerField(default=0)
    credit = models.IntegerField(default=settings.DEFAULT_STATS['credits'])
    default_city_id = models.PositiveIntegerField(default=0)
    active_city_id = models.PositiveIntegerField(default=0)
    last_msg_id = models.PositiveIntegerField(default=0)

    max_trusted = models.IntegerField(default=settings.DEFAULT_TRUSTED_SLOTS)
    max_hookers = models.PositiveSmallIntegerField(default=10)
    max_cars = models.PositiveSmallIntegerField(default=6)

    attack_mod = models.DecimalField(max_digits=2, decimal_places=1, default="1.0")
    defense_mod = models.DecimalField(max_digits=2, decimal_places=1, default="1.0")
    respect_mod = models.DecimalField(max_digits=2, decimal_places=1, default="1.0")
    heat_mod = models.DecimalField(max_digits=2, decimal_places=1, default="1.0")
    cash_mod = models.DecimalField(max_digits=2, decimal_places=1, default="1.0")
    drug_req_mod = models.DecimalField(max_digits=2, decimal_places=1, default="1.0")
    time_mod = models.DecimalField(max_digits=2, decimal_places=1, default="1.0")

    daily_income = models.IntegerField(default=0)  # not used yet
    daily_outcome = models.IntegerField(default=0)  # not used yet
    special_jobs_count = models.PositiveIntegerField(default=0)
    invite_count = models.PositiveIntegerField(default=0)

    contact = models.TextField(default='{}')
    notify = models.TextField(default='{}')

    is_active = models.BooleanField(default=True)
    is_spammer = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_premium_until = models.DateTimeField(default=datetime.datetime.now())

    next_heat_at = models.DateTimeField(auto_now_add=True)
    next_city_at = models.DateTimeField(auto_now_add=True)
    next_tribute = models.BooleanField(default=True)
    next_stats_recalc = models.BooleanField(default=False)
    next_total_recalc = models.BooleanField(default=False)
    has_skills = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserProfileManager()

    class Meta:
        db_table = 'user'
        verbose_name = 'User profile'
        verbose_name_plural = 'User profiles'

    def __unicode__(self):
        return self.username

    def __getattr__(self, name):
        if name == 'attack':
            return self.total_attack
        elif name == 'defense':
            return self.total_defense
        elif name == 'respect':
            return self.total_respect
        elif name in ('twitter', 'msn', 'gg', 'aim', 'jabber', 'gtalk', 'mobile'):
            if self.contact == '':
                return {}
            else:
                return json.loads(self.contact).get(name)
        elif name == 'contacts':
            if self.contact == '':
                return {}
            else:
                return json.loads(self.contact)
        elif name == 'notifiers':
            if self.notify == '':
                return {}
            else:
                return json.loads(self.notify)
        else:
            return self.__getattribute__(name)

    def save(self, force_insert=False):
        try:
            super(UserProfile, self).save(force_insert=force_insert)  # Call the "real" save() method
        except Exception, e:
            logging.error('Error saving profile %s' % e)
        key = 'user_%s' % self.user.id
        cache.set(key, pickle.dumps(self))

    def delete(self):
        cache.delete('user_%s' % self.user.id)
        super(UserProfile, self).delete()  # Call the "real" delete() method

    # -- Methods

    def has_enough(self, type, num):
        """Czy user ma wystarczajaca ilosc danych obiektow"""
        if type in ('cash', 'credit', 'base_attack', 'base_respect', 'base_defense', 'total_attack', 'total_defense',
                    'total_respect', 'team_attack', 'team_defense', 'team_respect', 'bdp', 'bdp_level'):
            try:
                if int(self.__dict__[type]) >= int(num):
                    return True
                else:
                    return False
            except KeyError:
                logging.error('No attribute type: %s' % type)
                return False

                # elif type == 'respect':
                #	try:
                #		if int(self.base_respect) <= int(num) + int(self.base_respect):
                #			return True
                #		else:
                #			logging.debug('Respect too low')
                #			return False
                #	except ValueError:
                #		logging.debug('Respect value error')
                return False

        elif type == 'heat':
            try:
                if int(self.heat) <= int(num) + int(self.heat):
                    return True
                else:
                    return False
            except ValueError:
                logging.error('Heat value error')
                return False

        # elif type == 'level':
        #	logging.debug('Has not enough %s' % type)
        #	return True
        #
        # elif type == 'members':
        #	logging.debug('Has not enough %s' % type)
        #	return True

        else:
            logging.error('Unsupported type: %s' % type)
            raise NotImplementedError

    def has_credits(self):
        """Czy user ma jakies kredyty?"""
        if self.credit > 0:
            return True
        else:
            return False

    def spend(self, type, num, autosave=True):
        """Usuwa obiekty z profilu"""
        if type in ('cash', 'credit', 'heat'):
            try:
                # logging.debug('%s just spent %s %s' % (self.user, num, type))
                try:
                    self.__dict__[type] -= int(num)
                except TypeError:
                    logging.error('Blad przy przypisywaniu wartosci')
                    return False

                if autosave:
                    self.save()
                return True

            except KeyError:
                logging.error('No type: %s' % type)
                return False

        logging.error('Unsupported type: %s' % type)
        return False

    def earn(self, type, num, autosave=True):
        """Dodaje obiekty do profilu"""
        if type in ('cash', 'credit', 'heat'):
            try:
                # logging.debug('%s just earned %s %s' % (self.user, num, type))
                try:
                    self.__dict__[type] += int(num)
                except TypeError:
                    logging.error('Blad przy przypisywaniu wartosci')
                    return False

                if autosave:
                    self.save()
                return True

            except KeyError:
                logging.error('No type: %s' % type)
                return False

        logging.error('Unsupported type: %s' % type)
        return False

    def to_bank(self, amount, autosave=True):
        self.cash -= int(amount)
        self.cash_in_bank += int(amount)
        if autosave:
            self.save()

    def from_bank(self, amount, autosave=True):
        self.cash += int(amount)
        self.cash_in_bank -= int(amount)
        if autosave:
            self.save()

    def match_req(self, reqs):

        for name, req in reqs.iteritems():
            if name == 'skills':
                u = UserSkill.objects.get_by_user(user=self.user)
                for skill, lvl in req.iteritems():
                    if not u.skills.has_key(skill): return False
                    if int(u.skills[skill]) < int(lvl): return False
            elif name == 'car':
                from crims.item.models import Garage

                u = Garage.objects.get_by_user(user=self.user)
            elif name == 'member':
                from crims.family.models import UserFamily

                u = UserFamily.objects.get_by_user(user=self.user)
                if len(u.members) < int(req): return False
            elif name == 'lady':
                from crims.city.models import CityHooker

                u = CityHooker.objects.get_by_city(user=self.engine.user.profile.default_city_id)
                if len(u.hookers) < int(req): return False
            else:
                logging.warning('Cannot match %s req' % str(name))
                return False
        return True

    # ---

    def add_per_day(self, source, amount, source_id=None, is_limited=None, valid_until=None):
        """Dodaje wpis do tabeli z dziennymi zarobkami/wydatkami"""
        pay = UserPerDay()
        pay.user = self.user

        pay.source = source
        if source_id is not None:
            pay.source_id = source_id
        pay.amount = amount
        if is_limited is not None:
            pay.is_limited = is_limited
        if valid_until is not None:
            pay.valid_until = valid_until

        pay.save()
        logging.debug("%s: pay-per-day added from source: %s(id:%s) with amount: %s" % (
        pay.user, pay.source, pay.source_id, pay.amount))

    def remove_per_day(self, source, source_id):
        """Usuwa wpis z tabeli z dziennymi zarobkami/wydatkami"""
        try:
            UserPerDay.objects.filter(user=self.user, source=source, source_id=source_id)[0].delete()
        except UserPerDay.DoesNotExist:
            logging.warning("Nie udalo sie usunac pay-per-day z paremetrami: user_id:%s, source:%s, source_id:%s" % (
            self.user.id, source, source_id))
        except IndexError:
            logging.warning("Nie udalo sie usunac pay-per-day z paremetrami: user_id:%s, source:%s, source_id:%s" % (
            self.user.id, source, source_id))

    # ---

    def add_log(self, log_type='', log_type_id=0, log='', ip=''):
        from django.db import connection

        sql = """
			INSERT INTO
				archive.crims_user_log
			VALUES (
				'%s', '%s', '%s', '%s', '%s', '%s'
			)
		""" % (str(self.user.id), log_type, log_type_id, log, datetime.datetime.now(), str(ip))

        cursor = connection.cursor()
        cursor.execute(sql)


class UserPerDayManager(models.Manager):
    def get_sums(self):
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("SELECT user_id, SUM(amount) FROM user_per_day GROUP BY user_id")
        return cursor.fetchall()

    def get_sum_by_user(self, user):
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute(
            "SELECT SUM(amount) as total_amount FROM user_per_day WHERE user_id='%s' GROUP BY user_id" % str(user.id))
        row = cursor.fetchone()
        if type(row) is type(()):
            return row[0]
        else:
            return None


class UserPerDay(models.Model):
    """(UserPerDay description)"""
    user = models.ForeignKey(User)
    source = models.CharField(max_length=100)
    source_id = models.IntegerField(default=0)
    amount = models.IntegerField(default=0)

    is_limited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(auto_now_add=True)

    objects = UserPerDayManager()

    class Meta:
        db_table = 'user_per_day'
        verbose_name = 'User\'s per-day income'
        verbose_name_plural = 'User\'s per-day incomes'

    def __unicode__(self):
        return "%s's $%s from %s" % (self.user, str(self.amount), self.source)


class BonusManager(models.Manager):
    def get_by_id(self, bonus_id):
        key = 'bonus_id_%s' % str(bonus_id)

        all_bonuses = cache.get(key)
        if all_bonuses is not None:
            all_bonuses = pickle.loads(str(all_bonuses))

            try:
                return all_bonuses[str(bonus_id)]
            except KeyError:
                logging.warning('Bonus not found. ID:%s' % str(bonus_id))
                return None

        all_bonuses = {}
        for bonus in Bonus.objects.all():
            all_bonuses[str(bonus.id)] = bonus

        cache.set(key, pickle.dumps(all_bonuses))

        try:
            return all_bonuses[str(bonus_id)]
        except KeyError:
            logging.warning('Bonus not found. ID:%s' % str(bonus_id))
            return None

    def get_by_name(self, bonus_name):
        key = 'bonus_name_%s' % str(bonus_name)

        all_bonuses = cache.get(key)
        if all_bonuses is not None:
            all_bonuses = pickle.loads(str(all_bonuses))

            try:
                return all_bonuses[str(bonus_name)]
            except KeyError:
                logging.warning('Bonus not found. Name:%s' % str(bonus_name))
                return None

        all_bonuses = {}
        for bonus in Bonus.objects.all():
            all_bonuses[str(bonus.name)] = bonus

        cache.set(key, pickle.dumps(all_bonuses))

        try:
            return all_bonuses[str(bonus_name)]
        except KeyError:
            logging.warning('Bonus not found. Name:%s' % str(bonus_name))
            return None


class Bonus(models.Model):
    """(Bonus description)"""
    subject = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    mod = models.DecimalField(max_digits=2, decimal_places=1)
    period = models.PositiveIntegerField()

    objects = BonusManager()

    class Meta:
        db_table = 'bonus'
        verbose_name = 'Bonus'
        verbose_name_plural = 'Bonuses'

    def __unicode__(self):
        return self.name


class UserBonusManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is None:
            user = UserProfile.objects.get_by_id(user_id).user

        key = 'user_bonus_%s' % str(user.id)
        all_user_bonuses = cache.get(key)

        if all_user_bonuses is not None:
            return pickle.loads(str(all_user_bonuses))

        all_user_bonuses = {}
        for ub in self.filter(user=user):
            if not all_user_bonuses.has_key(ub.bonus_subject):
                all_user_bonuses[ub.bonus_subject] = []
            all_user_bonuses[ub.bonus_subject].append(ub)

        cache.set(key, pickle.dumps(all_user_bonuses))
        return all_user_bonuses


class UserBonus(models.Model):
    """(Bonus description)"""
    user = models.ForeignKey(User, verbose_name='User', related_name='bonus_user')
    bonus_subject = models.CharField(max_length=50)
    bonus_name = models.CharField(max_length=50)

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    objects = UserBonusManager()

    class Meta:
        db_table = 'user_bonus'
        verbose_name = 'User\'s Bonus'
        verbose_name_plural = 'User\'s Bonuses'

    def __unicode__(self):
        return "%s for %s" % (self.bonus_name, self.user)

    def save(self, force_insert=False):
        super(UserBonus, self).save(force_insert=force_insert)  # Call the "real" save() method
        key = 'user_bonus_%s' % self.user.id
        cache.delete(key)

    def delete(self):
        key = 'user_bonus_%s' % self.user.id
        cache.delete(key)
        super(UserBonus, self).delete()  # Call the "real" delete() method

    # --- Methods

    def activate(self, profile, bonus=None):
        if bonus is None:
            bonus = Bonus.objects.get_by_name(self.bonus_name)

        logging.debug("%s: activating %s" % (str(self.user), str(bonus.name)))

        self.start_at = datetime.datetime.now()
        self.end_at = datetime.datetime.now() + datetime.timedelta(hours=int(bonus.period))
        self.is_active = True
        self.save()

        profile.__dict__['%s_mod' % self.bonus_subject] = str(bonus.mod)
        profile.save()

    def deactivate(self):
        user_id = str(self.user.id)
        subject = str(self.bonus_subject)

        logging.debug("%s: deactivating %s" % (user_id, subject))

        profile = UserProfile.objects.get_by_id(self.user.id)
        profile.__dict__['%s_mod' % self.bonus_subject] = "1.0"
        profile.save()

        # archive bonus
        # from django.db import connection
        # sql = """INSERT INTO archive.crims_user_bonus_archive VALUES ('%s', '%s', '%s', '%s', '%s', '%s')""" % (str(self.user.id), str(self.bonus_subject), str(self.bonus_name), str(self.start_at), str(self.end_at), str(datetime.datetime.now())[:19])
        # cursor = connection.cursor()
        # cursor.execute(sql)

        # remove
        self.delete()

        # any bonuses left?
        user_bonuses = UserBonus.objects.get_by_user(user_id=user_id)
        if user_bonuses.has_key(subject) and len(user_bonuses[subject]) > 0:
            user_bonuses[subject][0].activate(profile)


class SkillManager(models.Manager):
    def get_all(self):
        key = 'skills'
        item = cache.get(key)

        if item is not None:
            return pickle.loads(str(item))

        item = self.filter(is_active=True).order_by('order', 'name')

        cache.set(key, pickle.dumps(item))
        return item


class Skill(models.Model):
    name = models.CharField(max_length=25)
    level = models.PositiveSmallIntegerField(default=0)
    time = models.PositiveSmallIntegerField(default=0)  # in minutes
    cost = models.PositiveIntegerField(default=0)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SkillManager()

    class Meta:
        db_table = 'skill'
        verbose_name = 'Skill'

    def __unicode__(self):
        return "Skill: %s @ lvl %d" % (self.name, self.level)


class UserSkillManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_skill_%s' % user.id
        elif user_id is not None:
            key = 'user_skill_%s' % user_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user)
            elif user_id is not None:
                item = self.get(user__id=user_id)

        except UserSkill.DoesNotExist:
            us = UserSkill()
            if user is not None:
                us.user = user
            elif user_id is not None:
                us.user = User.objects.get(pk=user_id)
            us.save()
            item = us

        cache.set(key, pickle.dumps(item))
        return item


class UserSkill(models.Model):
    user = models.ForeignKey(User)
    skill = models.TextField()
    queue = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserSkillManager()

    def __getattr__(self, name):
        if name == 'skills':
            if not self.skill: return {}
            return json.loads(self.skill)  # {name: curr_skill, ...}
        elif name == 'queues':
            if not self.queue: return {}
            return json.loads(self.queue)  # {id: finish_date, ...}
        else:
            return self.__getattribute__(name)

    class Meta:
        db_table = 'user_skill'
        verbose_name = 'User Skill'

    def save(self):
        super(UserSkill, self).save()  # Call the "real" save() method
        key = 'user_skill_%s' % self.user.id
        cache.set(key, pickle.dumps(self))

    def __unicode__(self):
        return "%s\' skills" % (self.user)


class UserStatManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_stat_%s_%s' % (str(datetime.date.today()), user.id)
        elif user_id is not None:
            key = 'user_stat_%s_%s' % (str(datetime.date.today()), user_id)

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user, created_at=datetime.date.today())
            elif user_id is not None:
                item = self.get(user__id=user_id, created_at=datetime.date.today())

        except UserStat.DoesNotExist:
            item = UserStat()
            if user is not None:
                item.user = user
            elif user_id is not None:
                item.user = User.objects.get(pk=user_id)
            item.save()

        cache.set(key, pickle.dumps(item))
        return item


class UserStat(models.Model):
    user = models.ForeignKey(User)
    stat = models.TextField()

    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserStatManager()

    def __getattr__(self, name):
        if name == 'stats':
            if not self.stat: return {}
            return json.loads(self.stat)
        else:
            return self.__getattribute__(name)

    class Meta:
        db_table = 'user_stat'
        verbose_name = 'User Stat'

    def save(self):
        super(UserStat, self).save()  # Call the "real" save() method
        key = 'user_stat_%s_%s' % (str(datetime.date.today()), self.user.id)
        cache.set(key, pickle.dumps(self))

    def __unicode__(self):
        return "%s\' stats" % (self.user)


class UserRelationManager(models.Manager):
    pass


class UserRelation(models.Model):
    user = models.ForeignKey(User)
    who = models.PositiveIntegerField(default=0)

    type = models.CharField(max_length=20)
    details = models.CharField(max_length=255)
    is_positive = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)

    objects = UserRelationManager()

    class Meta:
        db_table = 'user_stat'
        verbose_name = 'User Stat'

    def save(self):
        super(UserRelation, self).save()  # Call the "real" save() method

    def __unicode__(self):
        return "%s\' relations" % (self.user)
