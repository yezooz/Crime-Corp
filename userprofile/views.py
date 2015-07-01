# -*- coding: utf-8 -*-
import simplejson as json
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db import models
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings

import crims.common.logger as logging
import datetime
from crims.userprofile.forms import ChangePassForm, SetPassForm, SetUsernameForm, SetEmailForm, ImForm
from crims.main.models import UserStream
from crims.registration.models import Country


@login_required
def profile(request, username):
    from django.contrib.auth.models import User
    from crims.userprofile.models import UserProfile

    try:
        if username is None:
            profile = request.engine.user.profile
        else:
            user = User.objects.get(username__iexact=username)
            profile = UserProfile.objects.get_by_id(user.id)
    except User.DoesNotExist:
        return request.engine.redirect(reverse('home'))

    request.engine.register('item')
    if username is not None:
        request.engine.item.user = user
    request.engine.item.set_item_type('item')
    request.engine.item.set_item_type('vehicle')

    return render_to_response(
        'userprofile/profile.html', {
            'profile': profile,
            'inventory': request.engine.item.active_inventory,
            'garage': request.engine.item.garage,
        },
        context_instance=RequestContext(request)
    )


@login_required
def edit(request):
    form_pass = ChangePassForm()
    form_pass.user = request.engine.user.user

    if request.method == 'POST' and request.POST.get('action_type') == 'change_password':
        form_pass = ChangePassForm(request.POST)
        form_pass.user = request.engine.user.user

        if form_pass.is_valid():
            request.engine.user.user.set_password(request.POST['new_password1'])
            request.engine.user.user.save()
            request.engine.log.message(message=_('Password changed!'))
            return request.engine.redirect(reverse('profile_edit'))

    form_im = ImForm(request.engine.user.profile.contacts)
    if request.method == 'POST' and request.POST.get('action_type') == 'change_im':
        form_im = ImForm(request.POST)

        if form_im.is_valid():
            request.engine.user.profile.contact = json.dumps(form_im.cleaned_data)
            request.engine.user.profile.save()
            request.engine.log.message(message=_('Data changed!'))
            return request.engine.redirect(reverse('profile_edit'))

    if request.method == 'POST' and request.POST.get('nationality') not in ('0', None):
        request.engine.user.profile.nationality = request.POST['nationality']
        request.engine.user.profile.save()
        request.engine.log.message(message=_('Data changed!'))
        return request.engine.redirect(reverse('profile_edit'))

    return render_to_response(
        'userprofile/edit.html', {
            'form_im': form_im,
            'form_pass': form_pass,
            'nations': Country.objects.get_all(),
        },
        context_instance=RequestContext(request)
    )


@login_required
def stream_delete(request, stream_id):
    try:
        stream = UserStream.objects.get(pk=stream_id)
        if stream.user == request.engine.user.user:
            stream.delete()
        else:
            logging.warning('UserStream ID:%s not belong to %s!' % (str(stream_id), str(request.engine.user.user)))
    except UserStream.DoesNotExist:
        logging.warning('UserStream ID:%s not found!' % str(stream_id))
    return request.engine.redirect(reverse('home'))


@login_required
def wall_stream_delete(request, stream_id):
    from crims.city.models import CityWall, CityMap

    try:
        stream = CityWall.objects.get(pk=stream_id)
        if stream.city.owner_id == request.engine.user.user.id:
            stream.delete()
        else:
            logging.warning('UserStream ID:%s not belong to %s!' % (str(stream_id), str(request.engine.user.user)))
    except CityWall.DoesNotExist:
        logging.warning('UserStream ID:%s not found!' % str(stream_id))
    return request.engine.redirect(reverse('home'))


@login_required
def skills(request):
    request.engine.user.get_skills()

    return render_to_response(
        'userprofile/skills.html', {
            'items': request.engine.user.to_do_skill,
        },
        context_instance=RequestContext(request)
    )


@login_required
def do_skill(request, skill_type):
    request.engine.user.get_skills()
    request.engine.user.do_skill(skill_type)
    return request.engine.redirect(reverse('skills'))
