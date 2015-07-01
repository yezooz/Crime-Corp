# -*- coding: utf-8 -*-

from django.contrib import admin

from crims.userprofile.models import *


class UserProfileAdmin(admin.ModelAdmin):
    # prepopulated_fields = {'slug': ('firstname', 'lastname')}
    pass


class UserPerDayAdmin(admin.ModelAdmin):
    pass


class BonusAdmin(admin.ModelAdmin):
    pass


class UserBonusAdmin(admin.ModelAdmin):
    pass


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserPerDay, UserPerDayAdmin)
admin.site.register(Bonus, BonusAdmin)
admin.site.register(UserBonus, UserBonusAdmin)
