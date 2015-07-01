import os, sys
sys.stdout = sys.stderr

sys.path.append('/home/marek/')
sys.path.append('/home/marek/crims/')
# sys.path.append('/usr/lib/python2.5/site-packages/')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
