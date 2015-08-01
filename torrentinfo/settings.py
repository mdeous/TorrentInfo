# -*- coding: utf-8 -*-

DEBUG = True
SECRET_KEY = 'CHANGEME'
MAX_FILES = 10

try:
    from prod_settings import *
except ImportError:
    pass
