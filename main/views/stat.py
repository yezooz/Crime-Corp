# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
import django.contrib.auth.views
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from crims.userprofile.models import UserProfile
from crims.common.paginator import DiggPaginator as Paginator


@login_required
def by_respect(request, page_no):
    paginator = Paginator(UserProfile.objects.filter(total_respect__gt="10.0").order_by('-total_respect'), 50, body=8,
                          padding=2)
    items = UserProfile.objects.filter(total_respect__gt="10.0").order_by('-total_respect')[
            (int(page_no) - 1) * 50:int(page_no) * 50]

    try:
        page = paginator.page(page_no)
    except Exception:
        return request.engine.redirect(reverse('stats_by_respect'))

    return render_to_response('main/stat/by_respect.html', {
        'page_no': int(page_no),
        'page': page,
        'items': items,
    }, context_instance=RequestContext(request))


@login_required
def by_population(request, page_no):
    paginator = Paginator(UserProfile.objects.filter(total_respect__gt="10.0").order_by('-city_population'), 50, body=8,
                          padding=2)
    items = UserProfile.objects.filter(total_respect__gt="10.0").order_by('-city_population')[
            (int(page_no) - 1) * 50:int(page_no) * 50]

    try:
        page = paginator.page(page_no)
    except Exception:
        return request.engine.redirect(reverse('stats_by_population'))

    return render_to_response('main/stat/by_population.html', {
        'page_no': int(page_no),
        'page': page,
        'items': items,
    }, context_instance=RequestContext(request))


@login_required
def search(request, page_no):
    if len(request.POST['username'].strip()) < 3:
        request.user.message_set.create(message="At least 3 chars.")
        return HttpResponseRedirect(reverse('stats_by_respect'))

    username = request.POST['username'].strip()

    paginator = Paginator(
        UserProfile.objects.filter(username__icontains=request.POST['username']).order_by('-total_respect'), 50, body=8,
        padding=2)
    items = UserProfile.objects.filter(username__icontains=request.POST['username']).order_by('-total_respect')[
            (int(page_no) - 1) * 50:int(page_no) * 50]

    try:
        page = paginator.page(page_no)
    except Exception:
        return request.engine.redirect(reverse('stat_search'))

    return render_to_response('main/stat/by_respect.html', {
        'page_no': int(page_no),
        'page': page,
        'items': items,
        'search_q': username,
    }, context_instance=RequestContext(request))
