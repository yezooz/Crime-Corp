# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request):
    request.engine.city.set_action_type('production')

    if not request.engine.city.can_see_city:
        return render_to_response('city/production/index_ro.html', {}, context_instance=RequestContext(request))

    if request.engine.city.city_product.first == '':
        return request.engine.redirect(reverse('production_set'))

    if request.method == 'POST' and request.POST.get('action_type') == 'produce' and request.POST.has_key(
            'item_type') and request.POST.has_key('item_name') and request.POST.has_key('amount'):
        request.engine.city.produce_item(request.POST['item_type'], request.POST['item_name'], request.POST['amount'])
        return request.engine.redirect(reverse('production'))

    return render_to_response(
        'city/production/index.html', {
            'items': request.engine.city.all_product[request.engine.city.city_product.first].values(),
            'queue': request.engine.city.build_queue,
        }, context_instance=RequestContext(request)
    )


@login_required
def set(request):
    request.engine.city.set_action_type('production')

    if request.method == 'POST' and request.POST.get('action_type') == 'set_product' and request.POST.has_key(
            'product'):
        request.engine.city.city_product.set(request.POST['product'])
        return request.engine.redirect(reverse('production'))

    return render_to_response(
        'city/production/set.html', {

        }, context_instance=RequestContext(request)
    )
