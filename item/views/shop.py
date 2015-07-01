# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings

import crims.common.logger as logging


@login_required
def index(request, tab):
    if tab not in settings.INVENTORY_TYPES:
        logging.warning("%s is not known inventory type" % tab)
        return request.engine.redirect(reverse('shop', args=['weapon']))

    request.engine.register('item')
    request.engine.item.set_item_tab(tab)  # before set_item_type
    request.engine.item.set_item_type('item')
    if tab == 'vehicle':
        request.engine.item.set_item_type('vehicle')

    if request.method == 'POST' and request.POST.has_key('action_type') and request.POST['action_type'] == 'buy':
        request.engine.item.buy_item(request.POST['item_id'])
        return request.engine.redirect(reverse('shop', args=[tab]))
    elif request.method == 'POST' and request.POST.has_key('action_type') and request.POST['action_type'] == 'sell':
        request.engine.item.sell_item(request.POST['item_id'])
        return request.engine.redirect(reverse('shop', args=[tab]))

    return render_to_response(
        'item/shop/index.html', {
            'items': request.engine.item.sort_item(request.engine.item.all_item.values()),
            'inventory': request.engine.item.sort_item(request.engine.item.item_inventory[str(tab)]),
            'active_inventory': request.engine.item.sort_item(request.engine.item.active_inventory[str(tab)]),
            'tab': tab,
        }, context_instance=RequestContext(request)
    )


# @login_required
# def details(request, item_type, item_id):
# 	if item_type not in settings.INVENTORY_TYPES:
# 		logging.warning("%s is not known inventory type" % item_type)
# 		return request.engine.redirect(reverse('shop', args=['weapon']))
# 		
# 	request.engine.register('item')
# 	request.engine.item.set_item_tab(item_type) # before set_item_type
# 	request.engine.item.set_item_type('item')
# 	
# 	return render_to_response(
# 		'item/shop/details_vehicle.html', {
# 			'item': request.engine.item.all_item[item_id],
# 			'tab': item_type,
# 		}, context_instance=RequestContext(request)
# 	)


@login_required
def activate(request, item_id):
    request.engine.register('item')
    request.engine.item.set_item_type('item')
    item = request.engine.item.activate_item(item_id)
    if item is None: return request.engine.redirect(reverse('home'))
    return request.engine.redirect(reverse('shop', args=[str(item.type)]))


@login_required
def deactivate(request, item_id):
    request.engine.register('item')
    request.engine.item.set_item_type('item')
    item = request.engine.item.deactivate_item(item_id)
    if item is None: return request.engine.redirect(reverse('home'))
    return request.engine.redirect(reverse('shop', args=[str(item.type)]))
