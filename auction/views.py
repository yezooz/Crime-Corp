# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db import models
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.conf import settings

import crims.common.logger as logging
import datetime
from crims.auction.forms import SellForm
from crims.common.paginator import DiggPaginator as Paginator


@login_required
def index(request, tab, page_no):
    request.engine.register('auction', tab)
    template_tab = 'auction'

    if tab == 'auction':
        paginator = Paginator(request.engine.auction.items, settings.DEFAULT_AUCTIONS_PER_PAGE, body=8, padding=2)
        selected = request.engine.auction.items[
                   (int(page_no) - 1) * settings.DEFAULT_AUCTIONS_PER_PAGE:int(
                       page_no) * settings.DEFAULT_AUCTIONS_PER_PAGE
                   ]

    elif tab == 'watch':
        pass

    elif tab in ('bidding', 'bidded'):
        paginator = Paginator(request.engine.auction.items, settings.DEFAULT_AUCTIONS_PER_PAGE, body=8, padding=2)
        selected = request.engine.auction.items[
                   (int(page_no) - 1) * settings.DEFAULT_AUCTIONS_PER_PAGE:int(
                       page_no) * settings.DEFAULT_AUCTIONS_PER_PAGE
                   ]
        template_tab = 'status'

    else:
        return request.engine.redirect(reverse('auction'))

    try:
        current_page = paginator.page(page_no)
    except:
        raise Http404

    return render_to_response(
        'auction/index_%s.html' % template_tab, {
            'tab': tab,
            'page_no': int(page_no),
            'page': current_page,
            'selected': selected,
            'items_count': len(request.engine.auction.items),
        },
        context_instance=RequestContext(request)
    )


@login_required
def details(request, auction_id):
    request.engine.register('auction')

    item = request.engine.auction.get_auction(auction_id)
    if item is None:
        return request.engine.redirect(reverse('auction'))

    if datetime.datetime.now() > request.engine.auction.auction.end_at:
        return render_to_response(
            'auction/details_fin.html', {
                'item': request.engine.auction,
            },
            context_instance=RequestContext(request)
        )
    else:
        return render_to_response(
            'auction/details.html', {
                'item': request.engine.auction,
            },
            context_instance=RequestContext(request)
        )


@login_required
def bid(request):
    request.engine.register('auction')
    request.engine.auction.bid(request.POST.get('item_id'), request.POST.get('amount'))

    return request.engine.redirect(reverse('auction_details', args=[request.POST.get('item_id')]))


@login_required
def sell(request, item_type, item_id):
    import simplejson as json
    from crims.auction.models import Auction
    from crims.item.models import Item, Garage

    item = Item.objects.get_by_id(item_id)
    garage = Garage.objects.get_by_user(user=request.engine.user.user)

    if item is None or str(item.id) not in garage.items:
        return request.engine.redirect(reverse('garage'))

    details = json.loads(item.details)
    details['product_id'] = item.id
    item.details = json.dumps(details)

    form = SellForm()
    if request.method == 'POST' and request.POST.has_key('duration'):
        form = SellForm(request.POST)

        if form.is_valid():
            a = Auction()
            a.title = "%s / %s" % (item.name, request.engine.user.user)
            a.details = item.details
            a.respect = item.respect
            a.image_filename = item.image_filename
            a.seller = request.engine.user.user
            a.start_price = form.cleaned_data['start_price']
            a.current_price = form.cleaned_data['start_price']
            a.image_filename = item.image_filename
            a.is_for_credits = False
            a.is_refunded = False
            a.start_at = datetime.datetime.now()
            a.end_at = datetime.datetime.now() + datetime.timedelta(days=int(form.cleaned_data['duration']))
            a.save()

            garage.sell_item(item.id)
            request.engine.user.recalculate_total()

            return request.engine.redirect(reverse('auction'))

    return render_to_response(
        'auction/sell.html', {
            'item_type': item_type,
            'item_id': item_id,
            'item': item,
            'details': json.loads(item.details),
            'form': form,
        },
        context_instance=RequestContext(request)
    )
