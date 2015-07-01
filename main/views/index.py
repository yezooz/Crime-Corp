# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect  # , Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

# from crims.common.helpers.core import get_invite_cookie

@login_required
def index(request):
    request.engine.register('stream')

    response = render_to_response(
        'index.html', {

        }, context_instance=RequestContext(request)
    )

    # get_invite_cookie(request, response, request.user)
    return response


def logout(request):
    from django.contrib.auth import logout

    logout(request)
    return HttpResponseRedirect(reverse('home'))


def maintance(request):
    return render_to_response('666.html')


def ping_on_install(request):
    import datetime
    from django.db import connection

    try:
        ip = request.META['REMOTE_ADDR']
    except:
        ip = ''

    sql = """
		INSERT INTO
			archive.crims_user_log
		VALUES (
			'0', 'install', '0', '0', '%s', '%s'
		)
	""" % (datetime.datetime.now(), ip)

    cursor = connection.cursor()
    cursor.execute(sql)
    return HttpResponse("")


def ping_on_uninstall(request):
    import datetime
    from django.db import connection

    try:
        ip = request.META['REMOTE_ADDR']
    except:
        ip = ''

    sql = """
		INSERT INTO
			archive.crims_user_log
		VALUES (
			'0', 'uninstall', '0', '0', '%s', '%s'
		)
	""" % (datetime.datetime.now(), ip)

    cursor = connection.cursor()
    cursor.execute(sql)
    return HttpResponse("")


@staff_member_required
def login_as_someone(request):
    from crims.common.forms import LoginAsForm

    data = request.POST or None
    form = LoginAsForm(data, request=request)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('home'))
    return render_to_response('admin/login_as_someone.html', {'form': form})
