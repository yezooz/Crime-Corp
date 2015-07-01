# -*- coding: UTF-8 -*-
# ==============================================================================================================
#									G A M E    S E T T I N G S
# ==============================================================================================================

MAX_BUILDINGS = 200
MAX_BUILDINGS_PER_SECTOR = 25
MAX_SLOTS = 8
MAX_TILE = 14
MAX_SECTOR_DENSITY = 0.5
MAX_SECURITY_BUILD_QUEUE = 3
WARN_CITIES_PER_SECTOR = 85
MAX_CITIES_PER_SECTOR = 85
MAX_HEAT = 999
MAX_MASTERY_LVL = 3

DEFAULT_RELATION_SCORE = 50

USER_PROTECTION = 1000  # respect

DEFAULT_STATS = {
    'attack': 10,
    'defense': 10,
    'respect': 10,
    'heat': 0.0,
    'cash': 0,
    'max_heat': 100,
    'credits': 10,
}

INVENTORY_TYPES = (
    'weapon',
    'armor',
    'gadget',
    'vehicle',
)

MAX_ACTIVE_INVENTORY_TYPES = {
    'weapon': 2,
    'armor': 2,
    'gadget': 99,
    'vehicle': 99,
}

DEFAULT_TRUSTED_SLOTS = 8
DEFAULT_MEMBERS_PER_PAGE = 10
DEFAULT_AUCTIONS_PER_PAGE = 20
DEFAULT_PRODUCTS_PER_PAGE = 20
DEFAULT_MSGS_PER_PAGE = 20
LOW_HEAT_EVERY_SECONDS = 240

SKILLS = {'driving': 'Driving', 'hacking': 'Hacking', 'security_breaking': 'Security', 'shooting': 'Shooting',
          'smuggling': 'Smuggling', 'stealing': 'Stealing'}

# --- Job

ROBBERY_TABS = (
    ('Lame', 'Not-So-Lame', 'Shoplifter', 'Homegrown Burglar'),
    # ('Burglar'),
)

ROBBERY_TABS_TRANS = {
    'Lame': {'en': 'Lame', 'pl': 'Lamer'},
    'Not-So-Lame': {'en': 'Not-So-Lame', 'pl': 'Mniejszy lamer'},
    'Shoplifter': {'en': 'Shoplifter', 'pl': 'Złodziej sklepowy'},
    'Homegrown Burglar': {'en': 'Homegrown Burglar', 'pl': 'Włamywacz amator'},
    'Burglar': {'en': 'Burglar', 'pl': 'Włamywacz'},
}

# --- City
CITY_POP_EVERY_SECONDS = 3600
MINIMUM_CITY_POPULATION = 40000  # 40k
DEFAULT_CITY_POPULATION = 50000  # 50k
DEFAULT_CITY_MOOD = 100
DEFAULT_CITY_MOOD_DAILY_INCREASE = {  # daily values
                                      '-5': -5000,
                                      '-4': -3500,
                                      '-3': -2500,
                                      '-2': -2000,
                                      '-1': 500,
                                      '0': 1000,
                                      '1': 2500,
                                      '2': 3500,
                                      '3': 5000,
                                      '4': 7500,
                                      '5': 10000,
                                      }
CITY_MOOD_DECREASE_PROTECTION = 2000  # if less than X respect, your city_mood won't decrease

MAP_MOVE_QUEUE_LIMIT = 10
MAP_MOVE_QUEUE_LIMIT_PREMIUM = 25

MOVE_TIME_PER_KM = {
    'default': 2.0,
    # examples
    'foot': 4.0,
    'bicycyle': 2.0,
    'car': 0.5,
    'plane': 0.05,
}

BUILDING = {  # lvl => ((BLD_ID, POP), ...)
              '1': ((2, 1000), (3, 2000)),
              '2': ((4, 10000), (5, 15000)),
              '3': ((6, 20000), (7, 30000)),
              '4': ((8, 40000), (9, 50000)),
              }

BIZ_BUILDING = {
    'liquor': 1,
    'cafe': 2,
    'pub': 3,
    'restaurant': 4,
    'hotel': 5,
    'club': 6,
    'gas_station': 7,
    'transport_company': 8,
}

# --- Business
BIZ_DETAILS = {
    'liquor': {'order': 1, 'heat': 50, 'cash': 300, 'attack': 500, 'defense': 750},
    'cafe': {'order': 2, 'heat': 55, 'cash': 500, 'attack': 2200, 'defense': 2800},
    'pub': {'order': 3, 'heat': 60, 'cash': 900, 'attack': 6000, 'defense': 7500},
    'restaurant': {'order': 4, 'heat': 65, 'cash': 1500, 'attack': 14000, 'defense': 16200},
    'hotel': {'order': 5, 'heat': 70, 'cash': 2400, 'attack': 16800, 'defense': 18500},
    'club': {'order': 6, 'heat': 80, 'cash': 3000, 'attack': 21000, 'defense': 22500},
    'gas_station': {'order': 7, 'heat': 90, 'cash': 5400, 'attack': 50000, 'defense': 56000},
    'transport_company': {'order': 8, 'heat': 100, 'cash': 9000, 'attack': 65000, 'defense': 75000},
}
FAMILY_COUNT = {
    '1': 11,
    '2': 16,
    '3': 18,
    '4': 18,
    '5': 12,
}
BIZ_COUNT = {
    'liquor': (0, 0, 0, 8, 7),
    'cafe': (0, 0, 8, 6, 3),
    'pub': (0, 4, 4, 4, 2),
    'restaurant': (0, 2, 4, 0, 0),
    'hotel': (0, 4, 2, 0, 0),
    'club': (2, 3, 0, 0, 0),
    'gas_station': (6, 2, 0, 0, 0),
    'transport_company': (3, 1, 0, 0, 0),
}
BIZ_PER_CAPITA = {
    'liquor': 5000,
    'cafe': 10000,
    'pub': 25000,
    'restaurant': 50000,
    'hotel': 60000,
    'club': 80000,
    'gas_station': 120000,
    'transport_company': 200000,
}

# --- Product
PRODUCT_TYPES = (
    'drug',
    'explosives',
    'pimp',
    'moonshine',
    'movie',
    'cloath',
)

PRODUCT_NEED_PER_CAPITA = {  # per 1k capita
                             'drug_1': 100, 'drug_2': 75, 'drug_3': 50, 'drug_4': 25,
                             'explosives_1': 40, 'explosives_2': 30, 'explosives_3': 20, 'explosives_4': 10,
                             'pimp_1': 40, 'pimp_2': 30, 'pimp_3': 20, 'pimp_4': 10,
                             'moonshine_1': 100, 'moonshine_2': 80, 'moonshine_3': 60, 'moonshine_4': 40,
                             'movie_1': 400, 'movie_2': 300, 'movie_3': 200, 'movie_4': 100,
                             'cloath_1': 200, 'cloath_2': 150, 'cloath_3': 100, 'cloath_4': 50,
                             }

PRODUCT_TYPE_ACTION_NAMES = {
    'drug': 'produce',
    'explosives': 'produce',
    'pimp': 'hire',
    'moonshine': 'produce',
    'movie': 'import',
    'cloath': 'import',
}

PRODUCT_MAX_UPGRADE_LEVEL = 5

# --- Item
ALL_ITEM = {
    1: {'en': 'Knife', 'pl': 'N&#243;&#380;'},
    2: {'en': 'Pistol', 'pl': 'Pistolet'},
    3: {'en': 'Leather Jacket', 'pl': 'Kurta sk&#243;rzana'},
    4: {'en': 'Anti-RIOT Shield', 'pl': 'Tarcza policyjna'},
    10: {'en': 'Grenades', 'pl': 'Granaty'},
    13: {'en': 'Sniper Rifle', 'pl': 'Karabin snajperski'},
    15: {'en': 'Rocket Launcher', 'pl': 'Wyrzutnia rakiet'},
    18: {'en': 'Kevlar Vest', 'pl': 'Kamizelka kewlarowa'},
    19: {'en': 'SWAT Shield', 'pl': 'Tarcza SWAT'},
}

# --- C R E D I T S
RELEASE_FROM_JAIL_CREDITS = 5
LOW_HEAT_CREDITS = 5
