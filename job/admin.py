# -*- coding: utf-8 -*-
from django.contrib import admin

from crims.job.models import Job  # , Bounty, BountyOffer


class JobAdmin(admin.ModelAdmin):
    pass

# class BountyAdmin(admin.ModelAdmin):
# 	pass

admin.site.register(Job, JobAdmin)
# admin.site.register(Bounty, BountyAdmin)
