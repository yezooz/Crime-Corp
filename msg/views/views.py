# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from crims.msg.models import Msg


@login_required
def inbox(request, page=0):
    if request.GET.has_key('ajax') and request.GET['ajax'] == '1':
        return render_to_response(
            'msg/list_ajax.html', {
                'msgs': request.engine.msg.get_inbox(page),
            }, context_instance=RequestContext(request)
        )

    request.engine.msg.mark_unread_as_read()
    return render_to_response(
        'msg/list.html', {
            'msgs': request.engine.msg.get_inbox(page),
            'selected_tab': 'inbox',
        }, context_instance=RequestContext(request)
    )


@login_required
def outbox(request, page=0):
    if request.GET.has_key('ajax') and request.GET['ajax'] == '1':
        return render_to_response(
            'msg/list_ajax.html', {
                'msgs': request.engine.msg.get_outbox(page),
            }, context_instance=RequestContext(request)
        )

    return render_to_response(
        'msg/list.html', {
            'msgs': request.engine.msg.get_outbox(page),
            'selected_tab': 'outbox',
        }, context_instance=RequestContext(request)
    )


@login_required
def form(request):
    usernames = []
    for string in request.POST['text'].split(' '):
        if string.startswith('@'): usernames.append(string)

    if len(usernames) > 0:
        for user in set(usernames):
            Msg.send.send_to(request.engine.user.user, user[1:], request.POST['text'])

        return render_to_response('msg/send_success.html')
    else:
        return render_to_response('msg/send_failure.html')
