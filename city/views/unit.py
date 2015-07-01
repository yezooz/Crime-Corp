# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request):
    request.engine.city.set_action_type('unit')

    if not request.engine.city.can_see_city or not request.engine.city.can_built_units:
        return render_to_response('city/unit/index_ro.html', {'my_units': request.engine.city.city_units_list()},
                                  context_instance=RequestContext(request))

    if request.method == 'POST' and request.POST.has_key('action_type'):
        if request.POST['action_type'] == 'hire' and request.POST.has_key('action_id'):
            request.engine.city.hire_unit(request.POST['action_id'])
            return request.engine.redirect(reverse('city_units'))

    return render_to_response(
        'city/unit/index.html', {
            'queue': request.engine.city.build_queue,
            'all_units': request.engine.city.sort_unit(request.engine.city.all_unit.values()),
            'my_units': request.engine.city.city_units_list(),
        }, context_instance=RequestContext(request)
        )


@login_required
def move(request, city_id=None):
    request.engine.city.set_action_type('unit')
    if request.method == 'POST' and city_id is not None and request.POST.get('action_type') == 'move_units':
        request.engine.city.move_units(request.POST)
        return request.engine.redirect(reverse('city_map'))

    if city_id is None:
        return render_to_response(
            'city/unit/move_ajax_list.html', {
                'units': request.engine.city.get_all_cities(),
            }, context_instance=RequestContext(request)
            )
    else:
        return render_to_response(
            'city/unit/move_ajax_city.html', {
                'city': request.engine.city.get_city(city_id),
                'units': request.engine.city.city_units_list(city_id=city_id),
            }, context_instance=RequestContext(request)
            )


@login_required
def cancel(request, order_id):
    request.engine.city.set_action_type('unit')
    request.engine.city.cancel_build_unit(order_id)
    return request.engine.redirect(reverse('city_units'))


@login_required
def move_cancel(request, move_id):
    request.engine.city.cancel_move_unit(move_id)
    return request.engine.redirect(reverse('home'))
