# -*- coding: UTF-8
import random
from decimal import *

import simplejson as json
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache

import crims.common.logger as logging
import datetime
import cPickle as pickle
from crims.common.helpers._crims import get_chance


class JobManager(models.Manager):
    def get_by_id(self, item_id):
        key = 'job_%s' % str(item_id)

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            item = self.get(pk=item_id)
        except Job.DoesNotExist:
            return None

        cache.set(key, pickle.dumps(item))
        return item

    def get_list(self, item_list):
        # TODO: z czasem pomyslec o optymalizacji, poki co starczy
        items = []

        for item in item_list:
            items.append(self.get_by_id(item))

        return items

    def get_robberies(self, tab):
        key = 'job_robbery_%s' % tab

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        item = self.filter(level=tab, is_active=True)

        cache.set(key, pickle.dumps(item))
        return item


class Job(models.Model):
    name = models.CharField(max_length=100)

    level = models.CharField(max_length=7)
    heat = models.IntegerField()
    mastery_incr = models.IntegerField(default=10)
    base_instant_cash = models.IntegerField(default=0)
    base_per_day_cash = models.IntegerField(default=0)
    base_instant_cost = models.IntegerField(default=0)
    base_per_day_cost = models.IntegerField(default=0)

    req_attack = models.IntegerField(default=0)
    req_respect = models.IntegerField(default=0)
    min_respect = models.IntegerField(default=0)

    base_attack = models.IntegerField(default=0)
    attack_modifier_min = models.DecimalField(max_digits=3, decimal_places=2, default='1.0')
    attack_modifier_max = models.DecimalField(max_digits=3, decimal_places=2, default='1.0')
    base_respect = models.IntegerField(default=0)
    respect_modifier_min = models.DecimalField(max_digits=3, decimal_places=2, default='1.0')
    respect_modifier_max = models.DecimalField(max_digits=3, decimal_places=2, default='1.0')

    req = models.TextField()
    loot = models.TextField()
    image_url = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    is_respawned = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(auto_now_add=True)

    objects = JobManager()

    class Meta:
        db_table = 'job'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __unicode__(self):
        return "%s (%s/%s) Heat:%s" % (self.name, self.req_attack, self.req_respect, self.heat)

    def __getattr__(self, name):
        if name == 'reqs':
            if not self.req: return {}
            return json.loads(self.req)
        if name == 'loots':
            if not self.loot: return {}
            return json.loads(self.loot)
        else:
            return self.__getattribute__(name)

    def do_job(self, user):
        import math

        res = {}

        if self.is_premium and not user.is_premium:
            res['result'] = 'NO_PREMIUM'
            return res

        # Job req
        if not user.match_req(self.reqs):
            res['result'] = 'NO_REQ'
            return res

        chance = get_chance(user.total_attack, \
                            user.total_respect, \
                            self.req_attack, \
                            self.req_respect, \
                            0, \
                            user.heat, \
                            user.max_heat, \
                            self.heat)
        rand_chance = random.randint(1, 100)
        if chance < rand_chance:
            logging.debug("%s failed job %s" % (str(user.user), str(self.id)))

            res['result'] = 'NO_CHANCE'
            return res

        res['result'] = True
        res['cash'] = int(math.ceil(int(self.base_instant_cash) * random.uniform(0.8, 1.2)))
        res['attack'] = int(self.base_attack) * random.uniform(float(self.attack_modifier_min),
                                                               float(self.attack_modifier_max))
        res['defense'] = int(self.base_attack) * random.uniform(float(self.attack_modifier_min),
                                                                float(self.attack_modifier_max))
        res['respect'] = int(self.base_respect) * random.uniform(float(self.respect_modifier_min),
                                                                 float(self.respect_modifier_max))

        res['attack'] = round(res['attack'], 2)
        res['defense'] = round(res['defense'], 2)
        res['respect'] = round(res['respect'], 2)

        res['loot'] = self.draw_loot()

        logging.debug("%s done job %s" % (str(user.user), str(self.id)))

        return res

    def draw_loot(self):
        rand_chance = random.randint(1, 100)

        loot_arr = []
        last_loot = 0
        for item_id, chance in self.loots.iteritems():
            for i in xrange(last_loot, last_loot + int(chance)):
                loot_arr.append(int(item_id))
                last_loot += 1

        if last_loot == 0: return
        if len(loot_arr) < rand_chance: return
        try:
            won = loot_arr[rand_chance]
        except IndexError:
            return

        logging.debug("won loot %s" % won)
        return won


class JobTributeManager(models.Manager):
    def get_by_id(self, item_id):
        key = 'job_tribute_%s' % str(item_id)

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            item = self.get(pk=item_id)
        except JobTribute.DoesNotExist:
            return None

        cache.set(key, pickle.dumps(item))
        return item

    def get_all(self):
        key = 'tributes'

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        jobs = {}
        for job in self.filter(is_active=True):
            jobs[str(job.id)] = job

        cache.set(key, pickle.dumps(jobs))
        return jobs


class JobTribute(models.Model):
    """(Job description)"""

    TYPES = (
        ('bakery', 'Bakery'),
        ('liquor', 'Liquor Shop'),
        ('cafe', 'Cafe'),
        ('pub', 'Pub'),
        ('restaurant', 'Restaurant'),
        ('hotel', 'Hotel'),
        ('club', 'Club'),
        ('gas_station', 'Gas Station'),
        ('warehouse', 'Warehouse'),
    )

    type = models.CharField(max_length=10, choices=TYPES)  # building types
    owner_id = models.IntegerField(default=0)  # default owner (family)
    owner_name = models.CharField(max_length=20)

    name = models.CharField(max_length=100)
    req = models.TextField()
    heat = models.IntegerField()
    base_instant_cash = models.IntegerField(default=0)
    base_per_day_cash = models.IntegerField(default=0)
    base_instant_cost = models.IntegerField(default=0)
    base_per_day_cost = models.IntegerField(default=0)

    req_attack = models.IntegerField(default=0)
    req_respect = models.IntegerField(default=0)

    base_attack = models.IntegerField(default=0)
    attack_modifier_min = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    attack_modifier_max = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    base_respect = models.IntegerField(default=0)
    respect_modifier_min = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    respect_modifier_max = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)

    image_url = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(auto_now_add=True)

    objects = JobTributeManager()

    class Meta:
        db_table = 'job_tribute'
        verbose_name = 'Job Tribute'
        verbose_name_plural = 'Job Tributes'

    def __unicode__(self):
        return "Tribute > %s (%s/%s) IN:%s" % (self.name, self.req_attack, self.req_respect, self.base_per_day_cash)

    def __getattr__(self, name):
        if name == 'reqs':
            if not self.req: return {}
            return json.loads(self.req)
        else:
            return self.__getattribute__(name)

    def do_job(self, user):
        res = {}

        # Job req
        if not user.match_req(self.reqs):
            res['result'] = 'NO_REQ'
            return res

        # Check!
        chance = get_chance(user.team_attack, \
                            user.team_respect, \
                            self.req_attack, \
                            self.req_respect, \
                            0, \
                            user.heat, \
                            user.max_heat, \
                            self.heat)
        rand_chance = random.randint(1, 100)
        if chance < rand_chance:
            res['result'] = 'NO_CHANCE'
            return res

        res['result'] = True
        res['cash'] = int(self.base_instant_cash) * random.uniform(0.8, 1.2)
        res['attack'] = int(self.base_attack) * random.uniform(float(self.attack_modifier_min),
                                                               float(self.attack_modifier_max))
        res['defense'] = int(self.base_attack) * random.uniform(float(self.attack_modifier_min),
                                                                float(self.attack_modifier_max))
        res['respect'] = int(self.base_respect) * random.uniform(float(self.respect_modifier_min),
                                                                 float(self.respect_modifier_max))
        # TODO: bonus! 1/100

        return res

    def get_new_stats(self, multiply=1.0):
        res = {'result': True, 'cash': 0}
        res['attack'] = (int(self.base_attack) * random.uniform(float(self.attack_modifier_min),
                                                                float(self.attack_modifier_max))) * multiply
        res['defense'] = (int(self.base_attack) * random.uniform(float(self.attack_modifier_min),
                                                                 float(self.attack_modifier_max))) * multiply
        res['respect'] = (int(self.base_respect) * random.uniform(float(self.respect_modifier_min),
                                                                  float(self.respect_modifier_max))) * multiply
        return res


class UserJobManager(models.Manager):
    def get_by_user(self, user=None, user_id=None):
        if user is not None:
            key = 'user_job_%s' % user.id
        elif user_id is not None:
            key = 'user_job_%s' % user_id

        item = cache.get(key)
        if item is not None:
            return pickle.loads(str(item))

        try:
            if user is not None:
                item = self.get(user=user)
            elif user_id is not None:
                item = self.get(user__id=user_id)

        except UserJob.DoesNotExist:
            uj = UserJob()
            if user is not None:
                uj.user = user
            elif user_id is not None:
                uj.user = User.objects.get(pk=user_id)
            uj.save()
            item = uj

        cache.set(key, pickle.dumps(item))
        return item

    def get_related_by_user(self, user=None, user_id=None, which_list='todos'):
        uj = self.get_by_user(user, user_id)

        jobs = uj.__getattr__(which_list)
        return Job.objects.get_list(jobs)


class UserJob(models.Model):
    user = models.ForeignKey(User)
    master = models.TextField()

    objects = UserJobManager()

    class Meta:
        db_table = 'user_job'
        verbose_name = 'User\'s job'
        verbose_name_plural = 'User\'s jobs'

    def __unicode__(self):
        return "%s's individual jobs" % (self.user)

    def __getattr__(self, name):
        if name == 'mastery':
            if not self.master: return {}
            return json.loads(self.master)
        else:
            return self.__getattribute__(name)

    def save(self):
        super(UserJob, self).save()  # Call the "real" save() method
        key = 'user_job_%s' % self.user.id
        cache.set(key, pickle.dumps(self))

    def done_job(self, job_id, add):
        job_id = str(job_id)
        add = int(add)
        mastery = self.mastery
        lvl_up = False

        if not mastery.has_key(job_id): mastery[job_id] = '1|0'
        lvl, m = mastery[job_id].split('|')
        lvl, m = int(lvl), int(m)

        if lvl == settings.MAX_MASTERY_LVL and m == 100: return False

        m += add
        if m >= 100 and lvl < settings.MAX_MASTERY_LVL:
            m -= 100
            lvl += 1
            lvl_up = True
        if m > 100 and lvl == settings.MAX_MASTERY_LVL:
            m = 100

        mastery[job_id] = '%d|%d' % (lvl, m)
        self.master = json.dumps(mastery)
        self.save()
        return lvl_up

# class UserTribute(models.Model):
# 	user = models.ForeignKey(User)
# 	todo = models.TextField(blank=False, default='')
# 	done = models.TextField(blank=False, default='')
# 	hide = models.TextField(blank=False, default='')
# 
# 	def __getattr__(self, name):
# 		if name == 'todos':
# 			return [x for x in self.todo.split(',') if len(x) > 0]
# 		elif name == 'dones':
# 			return [x for x in self.done.split(',') if len(x) > 0]
# 		elif name == 'hides':
# 			return [x for x in self.hide.split(',') if len(x) > 0]
# 		else:
# 			return self.__getattribute__(name)
# 
# 	class Meta:
# 		db_table = 'user_tribute'
# 		verbose_name = 'User\'s tribute'
# 		verbose_name_plural = 'User\'s tributes'
# 
# 	def __unicode__(self):
# 		return "%s's extort jobs" % (self.user)	
# 
# 	def save(self):
# 		super(UserTribute, self).save() # Call the "real" save() method
# 		key = 'user_tribute_%s' % self.user.id
# 		cache.set(key, pickle.dumps(self))
# 
# 	def done_job(self, job_id):
# 		todo = self.todos[:]
# 		del todo[todo.index(str(job_id))]
# 		self.todo = ','.join(todo)
# 
# 		done = self.dones[:]
# 		done.append(str(job_id))
# 		self.done = ','.join(done)
# 
# 		self.save()
# 		
# 		logging.debug("%s done tribute %s" % (str(self.user), str(job_id)))
# 		
# 	def add(self, id_list):
# 		if len(id_list) == 0: return
# 		
# 		new_list = self.todos[:]
# 		new_list.extend(id_list)
# 		dones = self.dones
# 		for jid in new_list:
# 			if jid in dones:
# 				new_list.remove(jid)
# 		if len(new_list) == 0: return
# 		
# 		self.todo = ','.join(set(new_list))
# 		self.save()
# 	
# 	def remove(self, id_list):
# 		if len(id_list) == 0: return
# 		
# 		for item in id_list:
# 			if str(item) in self.dones:
# 				new_list = self.dones[:]
# 				del new_list[new_list.index(item)]
# 				self.done = ','.join(new_list)
# 				self.save()
# 				
# 				from django.db import connection
# 				cursor = connection.cursor()
# 				cursor.execute("DELETE FROM user_per_day WHERE user_id=%s and source='tribute' and source_id=%s" % (self.user.id, item))
# 				connection.connection.commit()
# 				
# 			elif str(item) in self.todos:
# 				new_list = self.todos[:]
# 				del new_list[new_list.index(str(item))]
# 				self.todo = ','.join(new_list)
# 				self.save()
