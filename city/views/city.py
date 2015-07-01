# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request):
    return render_to_response(
        'city/city.html', {
            'all_cities': request.engine.city.get_all_cities(),
        }, context_instance=RequestContext(request)
        )


@login_required
def enter_city(request, city_id):
    request.engine.city.enter_city(city_id)
    return request.engine.redirect(reverse('city_map'))


@login_required
def map_frame(request):
    request.engine.register('map')
    city = request.engine.city.city_map

    slots = []
    for i in xrange(0, 8):
        slots.append(city.slots[i * 25:(i + 1) * 25])

    return render_to_response(
        'city/city_frame.html', {
            'slots': slots,
            'map_details': request.engine.map.map,
        }, context_instance=RequestContext(request)
        )
