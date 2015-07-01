# -*- coding: utf-8 -*-
import urllib
import urlparse
import os
import shutil
from PIL import Image

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect  # , Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.conf import settings
import simplejson as json

import crims.common.logger as logging
from crims.item.models import Item


@staff_member_required
def index(request):
    if request.GET.has_key('rebuild'):
        rethumbnail()
        return HttpResponse('rebuilded all thumbnails!')

    if request.method == 'POST':
        action = request.POST['action']

        if action == 'delete':
            item = Item.objects.get(pk=request.POST['id'])
            item.delete()
            return HttpResponse('deleted!')

        if action == 'update':
            item = Item.objects.get(pk=request.POST['id'])

            if request.POST['field'].strip().startswith('is_'):
                value = int(request.POST['value'])
            elif request.POST['field'].strip() == 'image_filename':
                url = request.POST['value'].strip()
                if url.startswith('http://'):
                    value = download_and_save(url, str(item.pk))
                elif url.startswith('like '):
                    img_id = url.replace('like ', '')
                    img_id = img_id[img_id.rfind('/') + 1:]

                    f_from = os.path.join(settings.MEDIA_ROOT, url.replace('like ', ''))
                    f_to = os.path.join(settings.MEDIA_ROOT, 'images', 'items') + '/' + str(item.pk) + '.jpg'
                    shutil.copyfile(f_from, f_to)
                    shutil.copyfile(f_from.replace('.jpg', '_l.jpg'), f_to.replace('.jpg', '_l.jpg'))
                    shutil.copyfile(f_from.replace('.jpg', '_m.jpg'), f_to.replace('.jpg', '_m.jpg'))
                    shutil.copyfile(f_from.replace('.jpg', '_s.jpg'), f_to.replace('.jpg', '_s.jpg'))

                    value = url.replace('like ', '').replace(img_id, str(item.pk) + '.jpg')
                else:
                    rethumbnail(str(item.pk) + '.jpg')
                    return HttpResponse('updated!')
            else:
                value = request.POST['value'].strip()

            item.__setattr__(request.POST['field'], value)
            item.save()

            return HttpResponse('updated!')

        if action == 'add':
            item = Item()
            for k, v in request.POST.iteritems():
                item.__setattr__(k, v)
            item.in_shop = False
            item.is_active = True
            item.save()
            return HttpResponseRedirect(reverse('intranet_items') + '?type=' + item.type)

    items = Item.objects.all()
    if request.GET.has_key('type'):
        items = items.filter(type=request.GET['type'])

    return render_to_response(
        'intranet/items_index.html', {
            'items': items.order_by('-type', 'attack', 'name'),
            'groups': settings.INVENTORY_TYPES,
            'tiers': (1, 2, 3, 4, 5, 6),
        }, context_instance=RequestContext(request)
    )


# @staff_member_required
# def cars(request):
# 
# 	if request.GET.has_key('rebuild'):
# 		rethumbnail()
# 		return HttpResponse('rebuilded all thumbnails!')
# 
# 	if request.method == 'POST' and request.POST['type'] == 'job':
# 		action = request.POST['action']
# 		job = Job.objects.get(pk=request.POST['id'])
# 
# 		if action == 'delete':
# 			job.delete()
# 			return HttpResponse('deleted!')
# 
# 		if action == 'update':
# 			if request.POST['field'].strip().startswith('is_'):
# 				value = int(request.POST['value'])
# 			elif request.POST['field'].strip() == 'img':
# 				url = request.POST['value'].strip()
# 				if url.startswith('http://'):
# 					value = download_and_save(url, str(job.pk))
# 				elif url.startswith('like '):
# 					img_id = url.replace('like ', '')
# 					img_id = img_id[img_id.rfind('/')+1:]
# 
# 					f_from = os.path.join(settings.MEDIA_ROOT, url.replace('like ', ''))
# 					f_to = os.path.join(settings.MEDIA_ROOT, 'images', 'cars') + '/' + str(job.pk) + '.jpg'
# 					shutil.copyfile(f_from, f_to)
# 					shutil.copyfile(f_from.replace('.jpg', '_l.jpg'), f_to.replace('.jpg', '_l.jpg'))
# 					shutil.copyfile(f_from.replace('.jpg', '_m.jpg'), f_to.replace('.jpg', '_m.jpg'))
# 					shutil.copyfile(f_from.replace('.jpg', '_s.jpg'), f_to.replace('.jpg', '_s.jpg'))
# 
# 					value = url.replace('like ', '').replace(img_id, str(job.pk) + '.jpg')
# 				else:
# 					rethumbnail(str(job.pk) + '.jpg')
# 					return HttpResponse('updated!')
# 			else:
# 				value = request.POST['value'].strip()
# 
# 			job.__setattr__(request.POST['field'], value)
# 			job.save()
# 
# 			if request.POST['car_also'] == 'true':
# 				if request.POST['field'] == 'sprint':
# 					job.car.__setattr__('sprint_0_80', value)
# 					job.car.__setattr__('sprint_0_100', value)
# 				else:
# 					job.car.__setattr__(request.POST['field'], value)
# 				job.car.save()
# 
# 			return HttpResponse('updated!')
# 
# 	if request.method == 'POST' and request.POST['type'] == 'car':
# 		action = request.POST['action']
# 		car = Car.objects.get(pk=int(request.POST['id']))
# 
# 		if action == 'hide':
# 			car.is_active = False
# 			car.save()
# 			return HttpResponse('disabled!')
# 
# 		if action == 'save_as_job':
# 			car.save_as_job()
# 			return HttpResponse('saved as job!')
# 
# 		if action == 'update':
# 			if request.POST['field'].strip().startswith('is_'):
# 				value = int(request.POST['value'])
# 			else:
# 				value = request.POST['value'].strip()
# 
# 			car.__setattr__(request.POST['field'], value)
# 			car.save()
# 
# 			return HttpResponse('updated!')
# 
# 	gta = None
# 	manufs = None
# 	if request.GET.has_key('search'):
# 		gta = Car.objects.filter_with_params(request.GET)
# 		manufs = gta.values_list('manuf', flat=True).order_by('manuf').distinct()
# 		if len(request.GET['manuf']) > 0:
# 			gta = gta.order_by('manuf', 'model', 'year')
# 		else:
# 			gta = gta.order_by('manuf', '-year', 'model')[:100]
# 
# 	jobs = Job.objects.filter_with_params(request.GET)
# 	if jobs:
# 		jobs = jobs.order_by('is_active', 'tier', 'manuf', 'name')
# 
# 	return render_to_response(
# 		'intranet/job_index.html', {
# 			'get': request.GET,
# 			'manufs': manufs or Car.objects.values_list('manuf', flat=True).order_by('manuf').distinct(),
# 			'groups': settings.CAR_GROUPS,
# 			'jobs': jobs,
# 			'results': gta,
# 		}, context_instance=RequestContext(request)
# 	)


def do_thumbnails(path):
    path_dir = path[:path.rfind('.')]

    im = Image.open(path)
    im.thumbnail((250, 350), Image.ANTIALIAS)
    im.save(path_dir + '_l.jpg', "JPEG")

    im = Image.open(path)
    im.thumbnail((150, 250), Image.ANTIALIAS)
    im.save(path_dir + '_m.jpg', "JPEG")

    im = Image.open(path)
    im.thumbnail((90, 90), Image.ANTIALIAS)
    im.save(path_dir + '_s.jpg', "JPEG")


def download_and_save(url, name):
    data = urllib.urlretrieve(url.strip())
    filename = urlparse.urlparse(url)[2]

    path = os.path.join(settings.MEDIA_ROOT, 'images', 'items', name)
    shutil.move(data[0], path)

    # org image
    im = Image.open(path)
    im.thumbnail((1600, 1200), Image.ANTIALIAS)
    im.save(path + '.jpg', "JPEG")

    # thumbnails
    do_thumbnails(path + '.jpg')

    os.remove(path)

    return os.path.join('images', 'items', name + '.jpg')


def rethumbnail(filename=None):
    # refresh all
    if filename is None:
        for filename in os.listdir(os.path.join(settings.MEDIA_ROOT, 'images', 'items')):
            if not filename[filename.rfind('/') + 1:filename.rfind('.')].isdigit(): continue

            do_thumbnails(os.path.join(settings.MEDIA_ROOT, 'images', 'items', filename))
    else:
        do_thumbnails(os.path.join(settings.MEDIA_ROOT, 'images', 'items', filename))
