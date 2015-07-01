# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request):
    request.engine.register('item')
    request.engine.item.set_item_type('hooker')

    if request.method == 'POST' and request.engine.city.in_my_city:
        if request.POST.has_key('action_type') and request.POST['action_type'] == 'buy':
            request.engine.item.buy_hooker(request.POST['hooker_id'])
        elif request.POST.has_key('action_type') and request.POST['action_type'] == 'sell':
            request.engine.item.sell_hooker(request.POST['hooker_id'])

        return request.engine.redirect(reverse('hooker'))

    return render_to_response(
        'item/hooker/index.html', {
            'items': request.engine.item.sort_hooker(request.engine.item.all_hooker.values()),
            'inventory': request.engine.item.sort_hooker(request.engine.item.hooker_inventory),
        }, context_instance=RequestContext(request)
    )
