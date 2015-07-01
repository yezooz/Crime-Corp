# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse  # , Http404
from django.template import RequestContext
import django.contrib.auth.views
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings

import crims.common.logger as logging
from crims.main.models import PaymentCode
from crims.registration.models import Country


@login_required
def index(request):
    if request.method == 'POST' and request.POST.has_key('code'):
        code = PaymentCode.codes.check_code(request.POST['code'])
        if code is None: return request.engine.redirect(reverse('payment'))

        # redeem code -> temporary location :)
        if code.is_used:
            request.engine.log.message(message="Ten kod już został użyty")
            return request.engine.redirect(reverse('payment'))

        code.used_by = request.engine.user.user.id
        code.is_used = True
        code.save()

        profile = request.engine.user.profile
        try:
            value = int(code.value)
        except ValueError:
            request.engine.log.message(
                message="Błąd. Musimy sprawdzić co się stało, ale nie martw się otrzymasz swoje kredyty najszybciej jak to będzie możliwe")
            return request.engine.redirect(reverse('payment'))

        if value == 1098:
            profile.earn('credit', 25)
            request.engine.log.message(message="Dodano 25 kredytów")
        elif value == 2318:
            profile.earn('credit', 55)
            request.engine.log.message(message="Dodano 55 kredytów")
        elif value == 3050:
            profile.earn('credit', 85)
            request.engine.log.message(message="Dodano 85 kredytów")
        else:
            request.engine.log.message(
                message="Błąd. Musimy sprawdzić co się stało, ale nie martw się otrzymasz swoje kredyty najszybciej jak to będzie możliwe")

        return request.engine.redirect(reverse('payment'))

    return render_to_response(
        'main/payment.html', {
            'profile': request.engine.user.profile,
            # 'countries': Country.objects.get_all(),
            'pref_lang': request.engine.pref_lang.upper(),
        }, context_instance=RequestContext(request)
    )


@login_required
def premium(request):
    return render_to_response(
        'main/payment_premium.html', {}, context_instance=RequestContext(request)
    )


def country_payment_part(request):
    return render_to_response(
        'main/payment_country_part.html', {

        }, context_instance=RequestContext(request)
    )


def srpoints(request, site):
    """
    On the postback, we send the following query arguments:
    new - user earned by filling out offer 'oid'
    total - total amount of accumulated by this user
    uid - the site's user uid (facebook, myspace, etc)
    oid - SuperRewards offer identifier
    You must reply:
    1 - if you updated your system successfully
    0 - if there is a problem on your end (we'll wait and resend the postback again)
    The reply should be just 1 digit (no xml, no tags, just 1 byte reply)
    Example:
    http://www.domain.com/postback.cgi?app=mygreatapp&new=25&total=1000&uid=1234567&oid=123
    Important
    1. 'oid' + 'uid' is not a unique cominbation. There are offers that users can fill out several times and get credited for them.
    2. Please always rely on total value in your calculations.
    """
    import md5

    valid = md5.new(
        request.GET['id'] + ':' + request.GET['new'] + ':' + request.GET['uid'] + ':' + settings.SRPOINTS_SECRET[
            str(site)]).hexdigest()

    from crims.main.models import Payment
    from crims.userprofile.models import UserProfile
    from django.core.mail import send_mail

    pay = Payment()
    pay.user_id = request.GET['uid']
    pay.site = site
    pay.provider = 'srpoints'
    pay.details = str(request.GET)
    pay.credits = request.GET['new']
    pay.total_credits = request.GET['total']

    if valid != request.GET['sig']:
        pay.status = 'invalid_transaction'
        pay.save()
        send_mail("Payment failure: invalid_transaction by %s" % request.GET['uid'], '',
                  'Crime Corp <robot@crimecorp.com>', ("crimecorp@crimecorp.com",), fail_silently=True)
        return HttpResponse(0)

    if site == 'fb':
        profile = UserProfile.objects.get_by_fb_id(request.GET['uid'])
    else:
        profile = UserProfile.objects.get_by_id(request.GET['uid'])
    if profile is None:
        pay.status = 'user_not_found'
        pay.save()
        send_mail("Payment failure: user_not_found: %s" % request.GET['uid'], '', 'Crime Corp <robot@crimecorp.com>',
                  ("crimecorp@crimecorp.com",), fail_silently=True)
        return HttpResponse(0)

    profile.earn('credit', request.GET['new'])
    pay.status = 'ok'
    pay.save()

    logging.info("Dodano %s kredytów" % str(pay.credits))
    if int(pay.credits) > 3:
        send_mail("Payment success at %s by %s" % (pay.site, str(pay.user_id)),
                  "%s credits added. %s do far payed by him" % (str(pay.credits), str(pay.total_credits)),
                  'Crime Corp <robot@crimecorp.com>', ("crimecorp@crimecorp.com",), fail_silently=True)
    return HttpResponse(1)


def offerpal(request, site):
    """The callback server URL is how our servers ping your servers on offer completions.

    Notes: The callback URL format you will receive from our servers is as shown below:

    http://www.yourserver.com/anypath/reward.php?snuid=[Facebook	 user ID]&currency=[currency credit to user]
    snuid is the users id value of the Facebook	 user ID
    currency is the positive whole number
    Security: For security you can optionally white list Offerpal Media server IPs:

    74.205.58.114
    99.132.162.242
    99.132.162.243
    99.132.162.244
    99.132.162.245
    """

    from crims.main.models import Payment
    from crims.userprofile.models import UserProfile
    from django.core.mail import send_mail

    pay = Payment()
    pay.user_id = request.GET['snuid']
    pay.site = site
    pay.provider = 'offerpal'
    pay.details = str(request.GET)
    pay.credits = request.GET['currency']
    pay.total_credits = 0

    if site == 'fb':
        profile = UserProfile.objects.get_by_fb_id(request.GET['snuid'])
    else:
        profile = UserProfile.objects.get_by_id(request.GET['snuid'])
    if profile is None:
        pay.status = 'user_not_found'
        pay.save()
        send_mail("Payment failure: user_not_found: %s" % request.GET['snuid'], '', 'Crime Corp <robot@crimecorp.com>',
                  ("crimecorp@crimecorp.com",), fail_silently=True)
        return HttpResponse(0)

    profile.earn('credit', request.GET['currency'])
    pay.status = 'ok'
    pay.save()

    logging.info("Dodano %s kredytów" % str(pay.credits))
    if int(pay.credits) > 3:
        send_mail("Payment success at %s by %s" % (pay.site, str(pay.user_id)),
                  "%s credits added. %s do far payed by him" % (str(pay.credits), str(pay.total_credits)),
                  'Crime Corp <robot@crimecorp.com>', ("crimecorp@crimecorp.com",), fail_silently=True)
    return HttpResponse(1)


def webtopay(request):
    """https://www.webtopay.com/specification_sms.html"""
    from crims.main.models import Payment, PaymentCode
    from crims.userprofile.models import UserProfile
    from django.core.mail import send_mail

    pay = Payment()
    pay.user_id = 0
    pay.site = 'sms'
    pay.provider = 'webtopay'
    pay.details = str(request.GET)
    pay.credits = 0
    pay.total_credits = 0
    pay.status = 'ok'
    pay.save()

    send_mail("SMS Payment success by %s" % (pay.provider), "%s PLN" % str(request.GET['amount']),
              'Crime Corp <robot@crimecorp.com>', ("crimecorp@crimecorp.com",), fail_silently=True)

    code = PaymentCode.codes.gen_new_code(value=request.GET['amount'])
    return HttpResponse('Crime Corp: %s' % code)


def furtumo(request):
    """http://fortumo.com/main/about_premium
    81.20.151.38
    81.20.148.122
    """
    from crims.main.models import Payment, PaymentCode
    from crims.userprofile.models import UserProfile
    from django.core.mail import send_mail

    pay = Payment()
    pay.user_id = 0
    pay.site = 'sms'
    pay.provider = 'furtumo'
    pay.details = str(request.GET)
    pay.credits = 0
    pay.total_credits = 0
    pay.status = 'ok'
    pay.save()

    send_mail("SMS Payment success by %s" % (pay.provider), "%s PLN" % str(request.GET['price']),
              'Crime Corp <robot@crimecorp.com>', ("crimecorp@crimecorp.com",), fail_silently=True)

    code = PaymentCode.codes.gen_new_code(value=request.GET['price'])
    return HttpResponse('Crime Corp: %s' % code)
