#!/usr/bin/env python3
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/app")

from wsgi import application

