# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request):
    request.engine.register('city')

    if request.method == 'POST' and request.POST.has_key('action_type') and request.POST.has_key('amount'):
        if request.POST['action_type'] == 'deposit':
            request.engine.city.bank_deposit(request.POST['amount'])
        elif request.POST['action_type'] == 'withdraw':
            request.engine.city.bank_withdraw(request.POST['amount'])

        return request.engine.redirect(reverse('bank'))

    return render_to_response(
        'main/bank.html', {
            'profile': request.engine.user.profile,
        }, context_instance=RequestContext(request)
    )
