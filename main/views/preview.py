# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect  # , HttpResponse, Http404
from django.template import RequestContext
import django.contrib.auth.views

import crims.common.logger as logging

# from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from crims.userprofile.models import UserProfile
from crims.main.forms import RegistrationForm, RegistrationShortForm
from django.utils.translation import ugettext as _
from crims.helpers.slughifi import slughifi

from django.conf import settings
# from crims.common.helpers.core import get_invite_cookie

def register(request):
    message = None
    form = RegistrationForm()

    if request.method == 'POST' and request.POST['action_type'] == 'login':
        username = slughifi(request.POST['username'])
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                response = HttpResponseRedirect(reverse('home'))
                # get_invite_cookie(request, response, user)
                return response
            else:
                message = _("Account inactive.")
        else:
            message = _("Entered nickname and password combination is not correct")

    if request.method == 'POST' and request.POST['action_type'] == 'register':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            profile = UserProfile()
            profile.user = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'],
                                                    form.cleaned_data['password1'])
            profile.username = form.cleaned_data['username']
            profile.add_log(log_type='register', log_type_id=profile.user.id, log='from web',
                            ip=request.META.get('REMOTE_ADDR'))

            # create city
            from crims.city.models import CityMap, Sector

            city = CityMap()
            city.owner_id = profile.user.id
            city.orig_owner_id = profile.user.id
            city.name = profile.username
            city.population = settings.DEFAULT_CITY_POPULATION
            city.sector, city.position = Sector.objects.next_cords()
            city.save()

            profile.default_city_id = city.id
            profile.active_city_id = city.id
            profile.save()

            # profile.user.is_active = False
            # profile.user.save()

            # refresh city task
            from crims.common.models import Task

            task = Task()
            task.source = 'city'
            task.user_id = profile.user.id
            task.task = city.id
            task.save()

            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)

            logging.info("%s registered on the web" % form.cleaned_data['username'])

            response = HttpResponseRedirect(reverse('home'))
            # get_invite_cookie(request, response, profile)
            return response

        # extra actions
        # message="Account created. Check your email and wait for link to activate your account."

    return render_to_response('main/preview.html', {
        'form': form,
        'message': message,
    }, context_instance=RequestContext(request))


def registered(request):
    # if has_keyrequest.META["HTTP_REFERER"].find("/rejestracja/") >= 0:
    return render_to_response('main/registered.html', {}, context_instance=RequestContext(request))


# else: return HttpResponseRedirect("/")


def activate(request, activation_key):
    activation_key = activation_key.lower()  # Normalize before trying anything with it.
    account = Accounts.objects.activate_user(activation_key)
    return render_to_response('main/activate.html', {
        'account': account,
        'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS}, context_instance=RequestContext(request))
