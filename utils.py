#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/24 0024 14:12
# @Author  : Hadrianl 
# @File    : utils.py
# @Contact   : 137150224@qq.com

import logging
import sys
import pymongo as pmo
import base64
import datetime
import hashlib
import hmac
import json
import urllib
import urllib.parse
import urllib.request
import requests

_format = "%(asctime)-15s [%(levelname)s] [%(name)s] %(message)s"
_datefmt = "%Y/%m/%d %H:%M:%S"
_level = logging.DEBUG

handlers = [logging.StreamHandler(sys.stdout)]

logging.basicConfig(format=_format, datefmt=_datefmt, level=_level, handlers=handlers)
logger = logging.getLogger('HuoBi')
SYMBOL = {'ethbtc', 'ltcbtc', 'etcbtc', 'bchbtc'}
PERIOD = {'1min', '5min', '15min', '30min', '60min', '1day', '1mon', '1week', '1year'}
DEPTH = {0: 'step0', 1: 'step1', 2: 'step2', 3: 'step3', 4: 'step4', 5: 'step5'}

def createSign(pParams, method, host_url, request_path, secret_key):
    sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = '\n'.join(payload)
    payload = payload.encode(encoding='UTF8')
    secret_key = secret_key.encode(encoding='UTF8')

    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature