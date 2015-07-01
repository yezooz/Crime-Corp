# -*- coding: utf-8 -*-
from django.contrib import admin

from crims.item.models import Item, Inventory, Hooker


class ItemAdmin(admin.ModelAdmin):
    pass


class InventoryAdmin(admin.ModelAdmin):
    pass


class HookerAdmin(admin.ModelAdmin):
    pass


admin.site.register(Item, ItemAdmin)
admin.site.register(Inventory, InventoryAdmin)
admin.site.register(Hooker, HookerAdmin)
