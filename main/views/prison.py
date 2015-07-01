# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect  # , HttpResponse, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from django.conf import settings


@login_required
def index(request):
    request.engine.register('city')

    if request.method == 'POST' and request.POST.has_key('action_type'):
        if request.POST['action_type'] == 'bribe':
            request.engine.city.prison_bribe(request.POST['amount'])
        else:
            request.engine.city.prison_service(request.POST['action_type'], request.POST.get('amount'))
        return HttpResponseRedirect(reverse('prison'))

    return render_to_response(
        'main/prison.html', {
            'settings': settings,
        }, context_instance=RequestContext(request)
    )
