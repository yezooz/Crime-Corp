# coding=utf-8

from crims.city.models import Map as MainMap


class Map(object):
    def __init__(self, engine):
        self.engine = engine
        self.map = MainMap.objects.get(is_default=True)
