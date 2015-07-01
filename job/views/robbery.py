# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse


@login_required
def index(request, page, tab):
    request.engine.register('job')
    request.engine.job.set_job_type('robbery', '%s|%s' % (page or 0, tab or 0))

    if request.method == 'POST' and request.POST.has_key('job_id'):
        request.engine.job.do_robbery(request.POST['job_id'])
        return request.engine.redirect(reverse('robbery', args=[page, tab]))

    return render_to_response(
        'jobs/robbery.html', {
            'page': int(page),
            'tab': tab or 0,
            'items': request.engine.job.sort(request.engine.job.all_robbery.values()),
            'profile': request.engine.user.profile,
            'my_skills': request.engine.user.skills.skills,
        }, context_instance=RequestContext(request)
    )
