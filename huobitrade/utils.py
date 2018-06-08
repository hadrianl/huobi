#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/24 0024 14:12
# @Author  : Hadrianl 
# @File    : utils.py
# @Contact   : 137150224@qq.com

import logging
import sys
import base64
import datetime
import hashlib
import hmac
import json
import urllib
import urllib.parse
import urllib.request
import requests
from functools import wraps
import time

_format = "%(asctime)-15s [%(levelname)s] [%(name)s] %(message)s"
_datefmt = "%Y/%m/%d %H:%M:%S"
_level = logging.DEBUG

handlers = [logging.StreamHandler(sys.stdout), logging.FileHandler('huobi.log')]

logging.basicConfig(format=_format, datefmt=_datefmt, level=_level, handlers=handlers)
logger = logging.getLogger('HuoBi')
SYMBOL = {'ethbtc', 'ltcbtc', 'etcbtc', 'bchbtc'}
PERIOD = {'1min', '5min', '15min', '30min', '60min', '1day', '1mon', '1week', '1year'}
DEPTH = {0: 'step0', 1: 'step1', 2: 'step2', 3: 'step3', 4: 'step4', 5: 'step5'}
ORDER_TYPE = {'buy-market':'市价买', 'sell-market':'市价卖', 'buy-limit':'限价买', 'sell-limit':'限价卖', 'buy-ioc':'IOC买单', 'sell-ioc':'IOC卖单'}
ORDER_STATES = {'pre-submitted': '准备提交', 'submitted': '已提交', 'partial-filled': '部分成交',
                'partial-canceled': '部分成交撤销', 'filled': '完全成交', 'canceled': '已撤销'}
ACCESS_KEY = ""
SECRET_KEY = ""


# API 请求地址
MARKET_URL = 'https://api.huobi.br.com'
TRADE_URL = 'https://api.huobi.br.com'

ACCOUNT_ID = None

def setKey(access_key, secret_key):
    global ACCESS_KEY, SECRET_KEY
    ACCESS_KEY = access_key
    SECRET_KEY = secret_key

def setUrl(market_url, trade_url):
    global MARKET_URL, TRADE_URL
    MARKET_URL = market_url
    TRADE_URL = trade_url

def createSign(pParams, method, host_url, request_path, secret_key):  # from 火币demo, 构造签名
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


def http_get_request(url, params, add_to_headers=None):  # from 火币demo, get方法
    headers = {
        'Content-type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = urllib.parse.urlencode(params)
    response = requests.get(url, postdata, headers=headers, timeout=5)
    try:

        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        logger.exception(f'<GET>httpGet failed, detail is:{response.text},{e}')
        return


def http_post_request(url, params, add_to_headers=None):  # from 火币demo, post方法
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    response = requests.post(url, postdata, headers=headers, timeout=10)
    try:

        if response.status_code == 200:
            return response.json()
        else:
            return
    except BaseException as e:
        logger.exception(f'<POST>httpPost failed, detail is:{response.text},{e}')
        return


def api_key_get(params, request_path):  # from 火币demo, 构造get请求并调用get方法
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({'AccessKeyId': ACCESS_KEY,
                   'SignatureMethod': 'HmacSHA256',
                   'SignatureVersion': '2',
                   'Timestamp': timestamp})

    host_url = TRADE_URL
    host_name = urllib.parse.urlparse(host_url).hostname
    host_name = host_name.lower()
    params['Signature'] = createSign(params, method, host_name, request_path, SECRET_KEY)

    url = host_url + request_path
    return http_get_request(url, params)


def api_key_post(params, request_path):  # from 火币demo, 构造post请求并调用post方法
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {'AccessKeyId': ACCESS_KEY,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Timestamp': timestamp}

    host_url = TRADE_URL
    host_name = urllib.parse.urlparse(host_url).hostname
    host_name = host_name.lower()
    params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
    return http_post_request(url, params)

def handler_profiler(handle):
    @wraps(handle)
    def func(self, msg):
        t0 = time.time()
        handle(self, msg)
        t1 = time.time()
        print(f'{self.name}-handle运行时间:{t1 - t0}s')
    return func