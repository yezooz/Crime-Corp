#!/usr/bin/python
from decimal import Decimal
import urllib
import re
import os
import getopt
import random

import sys
import datetime
import math

sys.path.append(os.path.dirname(__file__) + "../../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'crims.settings'
import crims.common.logger as logging

import simplejson as json
import cPickle as pickle
from django.conf import settings
from django.db import models
from crims.userprofile.models import UserProfile
from crims.city.models import CityMap, WorldMap, WorldMapSource, Sector
from crims.job.models import UserTribute
from django.db import connection

from crims.common.helpers._crims import _get_x, _get_y, _get_xy, _get_slot


def query(sql):
    cursor = connection.cursor()
    cursor.execute(sql)
    connection.connection.commit()


def assign_slot(profile):
    sector = random.choice(Sector.objects.filter(density__lte="0.60"))
    slot = _free_slot_in_sector(sector)

    # City
    cm = CityMap.objects.get_by_cords(_get_x(slot), _get_y(slot))
    cm.is_secured = False
    cm.save()

    # World
    wm = WorldMapSource.objects.get_by_sector(sector.id)
    city = wm.cities
    city[slot] = int(cm.id)
    wm.city = json.dumps(city)
    wm.sector = sector.id
    wm.save()

    sector.density += Decimal("0.01")
    sector.save()

    assign_buildings(profile, cm)


def assign_buildings(profile, city):
    ut = UserTribute.objects.get_by_user(profile.user)

    c = city.slots
    for biz in ut.todos + ut.dones:
        slot = _free_slot_in_city(c)
        c[slot] = int(biz)
    city.slot = json.dumps(c)
    city.save()


def _free_slot_in_city(city):
    while True:
        key = random.randint(0, 99)
        if city[key] == 0: return key
        continue


def _free_slot_in_sector(sector):
    wm = WorldMapSource.objects.get_by_sector(sector.id)
    while True:
        key = random.randint(0, 99)
        if wm.cities[key] == 0: return key
        continue


def _enough_sectors():
    citizens = UserProfile.objects.filter(is_active=True).count()
    while True:
        if (float(citizens) / (Sector.objects.all().count() * 100)) > 0.60:
            Sector.objects.add_sectors()
            continue
        break


def start():
    _enough_sectors()

    for profile in UserProfile.objects.filter(is_active=True):
        assign_slot(profile)


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "clstu")
    start()
