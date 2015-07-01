# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request):
    request.engine.register('job')
    request.engine.job.set_job_type('special')

    if request.method == 'POST' and request.POST.has_key('job_id'):
        request.engine.job.do_special(request.POST['job_id'])
        return request.engine.redirect(reverse('special_job'))

    return render_to_response(
        'jobs/special.html', {
            'items': request.engine.job.sort(request.engine.job.all_special.values()),
            'profile': request.engine.user.profile,
        }, context_instance=RequestContext(request)
    )
