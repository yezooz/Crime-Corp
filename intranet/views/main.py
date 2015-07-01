# -*- coding: utf-8 -*-=
import simplejson as json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import connection
from django.conf import settings

import crims.common.logger as logging
from crims.userprofile.models import UserProfile
from crims.main.models import PaymentPromoCode


@staff_member_required
def index(request):
    def query(query, one=True):
        cursor = connection.cursor()
        c = cursor.execute(query)
        if one:
            return cursor.fetchone()[0]
        return cursor.fetchall()

    data = {}
    data['user_all'] = query('SELECT COUNT(*) FROM user WHERE total_respect > 10')
    data['user_all_t'] = query('SELECT COUNT(*) FROM user')

    data['user_by_day_www'] = query(
        'SELECT FROM_DAYS(TO_DAYS(created_at)) as day, COUNT(*) as sum FROM user where fb_id = 0 AND total_respect > 10 GROUP BY day ORDER BY created_at DESC LIMIT 7',
        False)
    data['user_by_day_fb'] = query(
        'SELECT FROM_DAYS(TO_DAYS(created_at)) as day, COUNT(*) as sum FROM user where fb_id > 0 AND total_respect > 10 GROUP BY day ORDER BY created_at DESC LIMIT 7',
        False)
    data['user_by_day_www_t'] = query(
        'SELECT FROM_DAYS(TO_DAYS(created_at)) as day, COUNT(*) as sum FROM user where fb_id = 0 GROUP BY day ORDER BY created_at DESC LIMIT 7',
        False)
    data['user_by_day_fb_t'] = query(
        'SELECT FROM_DAYS(TO_DAYS(created_at)) as day, COUNT(*) as sum FROM user where fb_id > 0 GROUP BY day ORDER BY created_at DESC LIMIT 7',
        False)

    data['pay_1day'] = query('SELECT SUM(credits) FROM payment WHERE created_at >= NOW() - INTERVAL 1 DAY')
    data['pay_7day'] = query('SELECT SUM(credits) FROM payment WHERE created_at >= NOW() - INTERVAL 7 DAY')
    data['pay_30day'] = query('SELECT SUM(credits) FROM payment WHERE created_at >= NOW() - INTERVAL 30 DAY')

    data['auction_pending_dealer'] = query('SELECT COUNT(*) FROM auction WHERE is_refunded=0 AND seller_id=1187')
    data['auction_pending_not_dealer'] = query('SELECT COUNT(*) FROM auction WHERE is_refunded=0 AND seller_id!=1187')

    data['auction_end_3day_dealer'] = query(
        'SELECT COUNT(*) FROM auction WHERE is_refunded=0 AND end_at >= NOW() - INTERVAL 3 DAY AND seller_id=1187')
    data['auction_end_3day_not_dealer'] = query(
        'SELECT COUNT(*) FROM auction WHERE is_refunded=0 AND end_at >= NOW() - INTERVAL 3 DAY AND seller_id!=1187')

    codes = request.session.get('last_generated_codes')
    if codes:
        del request.session['last_generated_codes']

    return render_to_response(
        'intranet/index.html', {
            'data': data,
            'last_generated_codes': codes,
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def add_cars(request):
    from crims.item.models import Item, Garage

    cars = Item.objects.filter(in_shop=False, is_active=True, type='vehicle').order_by('respect', 'name')

    if request.method == 'POST':
        add_list = {}
        for k, v in request.POST.iteritems():
            if not k.startswith('car_') or int(v) <= 0: continue
            car_id = k.replace('car_', '')

            add_list[car_id] = int(v)

        if len(add_list) == 0:
            request.user.message_set.create(message="Nic nie dodano!")
            return HttpResponseRedirect('/intranet/add_cars/')

        garage = Garage.objects.get_by_user(user_id=1187)
        items = garage.items[:]
        for k, v in add_list.iteritems():
            for x in xrange(int(v)):
                items.append(str(k))
        garage.item = ','.join(items)
        garage.save()

        request.user.message_set.create(message="Dodano %d różnych aut!" % len(add_list))
        return HttpResponseRedirect('/intranet/add_cars/')

    return render_to_response(
        'intranet/add_cars.html', {
            'items': cars
        },
        context_instance=RequestContext(request)
    )


@staff_member_required
def social_notify(request):
    from common.im.twitter import Twitter
    from common.im.blip import Blip
    from django.contrib.auth.models import User
    from msg.models import Msg

    if request.POST.has_key('msg'):
        msg = request.POST['msg'].strip()
        if request.POST.has_key('to_blip'):
            b = Blip()
            b.send(msg)
        if request.POST.has_key('to_twitter'):
            t = Twitter()
            t.send(msg)
        if request.POST.has_key('to_users_pl') or request.POST.has_key('to_users_en'):
            if request.POST.has_key('to_users_pl'):
                users = UserProfile.objects.filter(pref_lang='pl')
            else:
                users = UserProfile.objects.filter(pref_lang='en')

            for user in users:
                m = Msg()
                m.sender = request.user
                m.receiver = user.user
                m.content = msg
                m.is_public = False
                m.is_gang = False
                m.save()
            request.user.message_set.create(message="PM x%d" % len(users))

    request.user.message_set.create(message="Wysłano wiadomości")
    return HttpResponseRedirect('/intranet/')


@staff_member_required
def code(request):
    def gen_code():
        import hashlib

        sha = hashlib.sha1()
        sha.update(str(datetime.datetime.now()))
        sha_code = sha.hexdigest()
        return sha_code

    def get_code(value, valid_for_days):
        start = 0
        while True:
            try:
                code = gen_code()[start + 2:start + 22]

                PaymentPromoCode.objects.get(code=code)
                start += 1
            except PaymentPromoCode.DoesNotExist:
                pc = PaymentPromoCode()
                pc.code = code
                pc.value = value
                pc.valid_until = datetime.datetime.now() + datetime.timedelta(days=valid_for_days)
                pc.save()
                return pc

            if start > 10: return None

    try:
        if request.method != 'POST' or \
                                0 > int(request.POST['how_many']) > 100 or \
                                0 > int(request.POST['value']) > 101 or \
                        int(request.POST['valid_for_days']) <= 0:
            return HttpResponseRedirect('/intranet/')
    except KeyError:
        return HttpResponseRedirect('/intranet/')
    except ValueError:
        return HttpResponseRedirect('/intranet/')

    codes = []
    for i in xrange(int(request.POST['how_many'])):
        codes.append(get_code(int(request.POST['value']), int(request.POST['valid_for_days'])).code)

    if len(codes) > 0:
        request.user.message_set.create(message="Dodano kody!")
        request.session['last_generated_codes'] = "<br/>".join(codes)

    return HttpResponseRedirect('/intranet/')


@staff_member_required
def import_cars_from_gta(self):
    from crims.item.models import Item
    from crims.common.models import Car

    for car in Car.objects.filter(is_active=True, in_gta=True, in_crims=False):
        i = Item()
        i.type = 'vehicle'
        i.name = "%s %s" % (car.manuf, car.model)
        i.details = json.dumps(
            {'product_type': 'vehicle', 'product_id': int(car.id), 'year': car.year, 'engine': car.engine_up,
             'bhp': int(car.power_bhp)})
        i.image_filename = car.img
        i.is_active = False
        i.save()

        car.is_in_crims = True
        car.is_active_in_crims = i.is_active
        car.save()

    return HttpResponseRedirect('/intranet/')
