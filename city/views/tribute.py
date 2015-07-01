# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

import datetime


@login_required
def index(request):
    request.engine.city.set_action_type('tribute')

    if not request.engine.city.can_see_city:
        return render_to_response('city/tribute/index_ro.html', {}, context_instance=RequestContext(request))

    if request.method == 'POST' and request.POST.has_key('bld_owner'):
        request.engine.city.do_tribute(request.POST['bld_type'], request.POST['bld_owner'])
        return request.engine.redirect(reverse('tribute'))

    if request.engine.city.city_unit.next_tribute_at > datetime.datetime.now():
        next_tribute_at = request.engine.city.city_unit.next_tribute_at
    else:
        next_tribute_at = None

    return render_to_response(
        'city/tribute/index.html', {
            'profile': request.engine.user.profile,
            'user_tribute': request.engine.city.user_tribute,
            'tributes': request.engine.city.user_tribute,
            'tribute_names': request.engine.city.TRIBUTE,
            'sums': request.engine.city.get_sums(),
            'next_tribute_at': next_tribute_at,
        }, context_instance=RequestContext(request)
    )
