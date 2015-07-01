# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect  # , Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.conf import settings
import simplejson as json

import crims.common.logger as logging
from crims.job.models import Job
from crims.item.models import Item


@staff_member_required
def index(request, job_id=None):
    job = None
    if job_id:
        job = Job.objects.get(pk=job_id)

    if request.method == 'POST':

        if request.POST.has_key('job_id'):
            job = Job.objects.get(pk=request.POST['job_id'])
        else:
            job = Job()

        skills, loot = {}, {}
        for k, v in request.POST.iteritems():
            if v == '': continue

            if k.startswith('skill_') and not k.endswith('_lvl'):
                try:
                    skills[v] = int(request.POST['skill_%s_lvl' % k.replace('skill_', '')])
                except ValueError:
                    continue
                else:
                    continue

            if k.startswith('loot_') and not k.endswith('_item'):
                i = k.replace('loot_', '').replace('_chance', '')
                if int(request.POST['loot_' + i + '_chance']) > 0 and int(request.POST['loot_' + i + '_item']) > 0:
                    loot[str(request.POST['loot_' + i + '_item'])] = int(request.POST['loot_' + i + '_chance'])
                continue

            job.__setattr__(k, v)

        job.loot = json.dumps(loot)
        job.req = json.dumps({'skills': skills})
        job.save()
        return HttpResponseRedirect('/intranet/jobs/' + str(job.id))

    items = {}
    all_items = {}
    for item in Item.objects.filter(is_active=True).order_by('type', 'price'):
        if not items.has_key(item.type):
            items[item.type] = {}
        items[item.type][str(item.id)] = item
        all_items[str(item.id)] = item

    job_details = {'loot': [], 'loot_chance': [], 'skill': [], 'skill_lvl': []}
    if job_id:
        loot_keys, skill_keys = job.loots.keys(), job.reqs['skills'].keys()
        for i in xrange(0, 5):
            if len(loot_keys) >= i + 1:
                job_details['loot'].append(all_items[loot_keys[i]])
                job_details['loot_chance'].append(job.loots[loot_keys[i]])
            if len(skill_keys) >= i + 1:
                job_details['skill'].append(request.engine.settings.SKILLS[skill_keys[i]])
                job_details['skill_lvl'].append(job.reqs['skills'][skill_keys[i]])

    # print [[("%s|%s" % (x,a), b) for a,b in enumerate(z)] for x,z in enumerate(settings.ROBBERY_TABS)]
    return render_to_response(
        'intranet/jobs_index.html', {
            'robbery_tabs': [[("%s|%s" % (x, a), b) for a, b in enumerate(z)] for x, z in
                             enumerate(settings.ROBBERY_TABS)],
            'jobs': Job.objects.all().order_by('-is_active', 'level', 'is_premium', 'req_attack', 'name'),
            'job': job,
            'job_details': job_details,
            'items': items,
            'all_items': all_items,
            'iii': [0, 1, 2, 3, 4],
        }, context_instance=RequestContext(request)
    )
