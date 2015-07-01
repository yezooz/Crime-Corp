# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request):
    request.engine.register('item')
    request.engine.item.set_item_type('vehicle')

    return render_to_response(
        'item/car/index.html', {
            'inventory': request.engine.item.sort_car(request.engine.item.garage),
        }, context_instance=RequestContext(request)
    )


@login_required
def details(request, item_id):
    request.engine.register('item')
    request.engine.item.set_item_type('vehicle')

    return render_to_response(
        'item/car/details.html', {

        }, context_instance=RequestContext(request)
    )


@login_required
def sell(request, item_id):
    request.engine.register('item')
    request.engine.item.set_item_type('vehicle')
    request.engine.item.sell_item(item_id)
    return request.engine.redirect(reverse('garage'))
