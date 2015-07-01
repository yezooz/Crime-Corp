#!/usr/bin/python
import Image
import ImageFont
import ImageDraw
import os
import getopt

import sys
import datetime

sys.path.append("/home/marek/")
os.environ["DJANGO_SETTINGS_MODULE"] = 'crims.settings'

PROJECT_DIR = '/home/marek/crims/'
# from django.conf import settings
from crims.userprofile.models import UserProfile

from django.utils.encoding import force_unicode
from crims.helpers.humanize import intcomma


def start():
    for profile in UserProfile.objects.filter(
            updated_at__gte=datetime.datetime(datetime.date.today().year, datetime.date.today().month,
                                              datetime.date.today().day, 0, 0, 0)):
        for_user(profile)


def for_user(profile):
    # English
    im = Image.open(os.path.join(MEDIA_URL, "images/", "banner_stats.jpg"))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(os.path.join(PROJECT_DIR, "common/fonts/", "Times New Roman.ttf"), 12)

    draw.text((70, 37), force_unicode(profile.username), font=font, fill="#000000")  # nickname
    draw.text((60, 55), intcomma(int(profile.total_respect)), font=font, fill="#000000")  # respect
    # draw.text((220, 55), intcomma(int(profile.city_population)), font=font, fill="#000000") # population

    im.save(os.path.join(MEDIA_URL, "images/badges/", "%s.jpg" % profile.user.id), "JPEG")

    # Polish
    im = Image.open(os.path.join(MEDIA_URL, "images/", "banner_stats_pl.jpg"))
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(os.path.join(PROJECT_DIR, "common/fonts/", "Times New Roman.ttf"), 12)

    draw.text((43, 37), force_unicode(profile.username), font=font, fill="#000000")  # nickname
    draw.text((60, 55), intcomma(int(profile.total_respect)), font=font, fill="#000000")  # respect
    # draw.text((220, 55), intcomma(int(profile.city_population)), font=font, fill="#000000") # population

    im.save(os.path.join(MEDIA_URL, "images/badges/", "%s_pl.jpg" % profile.user.id), "JPEG")


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], "clstu")
    start()
