#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/24 0024 14:12
# @Author  : Hadrianl
# @File    : utils.py
# @Contact   : 137150224@qq.com


from requests_futures.sessions import FuturesSession
import logging
import sys
import base64
import datetime
import hashlib
import hmac
from ecdsa import SigningKey
import json
import urllib
import urllib.parse
import urllib.request
import requests
from functools import wraps
import time
import zmq

_format = "%(asctime)-15s [%(levelname)s] [%(name)s] %(message)s"
_datefmt = "%Y/%m/%d %H:%M:%S"
_level = logging.INFO

handlers = [
    logging.StreamHandler(sys.stdout),
    logging.FileHandler('huobi.log')
]

logging.basicConfig(
    format=_format, datefmt=_datefmt, level=_level, handlers=handlers)
logging.addLevelName(60, 'WeChatLog')
logger = logging.getLogger('HuoBi')

SYMBOL = {'ethbtc', 'ltcbtc', 'etcbtc', 'bchbtc'}
PERIOD = {
    '1min', '5min', '15min', '30min', '60min', '1day', '1mon', '1week', '1year'
}
DEPTH = {
    0: 'step0',
    1: 'step1',
    2: 'step2',
    3: 'step3',
    4: 'step4',
    5: 'step5'
}

DerivativesDEPTH = {
    0: 'step0',
    1: 'step1',
    2: 'step2',
    3: 'step3',
    4: 'step4',
    5: 'step5',
    6: 'step6',
    7: 'step7',
    8: 'step8',
    9: 'step9',
    10: 'step10',
    11: 'step11',
}

class Depth:
    Step0 = 'step0'
    Step1 = 'step1'
    Step2 = 'step2'
    Step3 = 'step3'
    Step4 = 'step4'
    Step5 = 'step5'

class OrderType:
    BuyMarket = 'buy-market'  # '市价买'
    SellMarket = 'sell-market'  # '市价卖'
    BuyLimit = 'buy-limit' #'限价买'
    SellLimit = 'sell-limit' # '限价卖'
    BuyIoc = 'buy-ioc'  #'IOC买单'
    SellIoc = 'sell-ioc'  #'IOC卖单

class OrserStatus:
    PreSumitted = 'pre-submitted' # '准备提交'
    Submitted = 'submitted' # '已提交'
    PartialFilled = 'partial-filled' # '部分成交'
    PartialCanceled = 'partial-canceled'  # '部分成交撤销'
    Filled = 'filled'  # '完全成交'
    Canceled = 'canceled'  # '已撤销'


ORDER_TYPE = {
    'buy-market': '市价买',
    'sell-market': '市价卖',
    'buy-limit': '限价买',
    'sell-limit': '限价卖',
    'buy-ioc': 'IOC买单',
    'sell-ioc': 'IOC卖单',
    'buy-limit-maker': '限价买入做市',
    'sell-limit-maker': '限价卖出做市'
}
ORDER_STATES = {
    'pre-submitted': '准备提交',
    'submitted': '已提交',
    'partial-filled': '部分成交',
    'partial-canceled': '部分成交撤销',
    'filled': '完全成交',
    'canceled': '已撤销'
}

ORDER_SOURCE = {
'spot-web':	'现货 Web 交易单',
'spot-api':	'现货 Api 交易单',
'spot-app':	'现货 App 交易单',
'margin-web': '借贷 Web 交易单',
'margin-api': '借贷 Api 交易单',
'margin-app': '借贷 App 交易单',
'fl-sys': '借贷强制平仓单（爆仓单）'
}




ACCESS_KEY = ""
SECRET_KEY = ""
PRIVATE_KEY = ""

ETF_SWAP_CODE = {200: '正常',
                 10404: '基金代码不正确或不存在',
                 13403: '账户余额不足',
                 13404: '基金调整中,不能换入换出',
                 13405: '因配置项问题基金不可换入换出',
                 13406: '非API调用,请求被拒绝',
                 13410: 'API签名错误',
                 13500: '系统错误',
                 13601: '调仓期:暂停换入换出',
                 13603: '其他原因:暂停换入和换出',
                 13604: '暂停换入',
                 13605: '暂停换出',
                 13606: '换入或换出的基金份额超过规定范围'}

zmq_ctx = zmq.Context()
async_session = FuturesSession(max_workers=8)

# API 请求地址
MARKET_URL = 'https://api.huobi.br.com'
TRADE_URL = 'https://api.huobi.br.com'

ACCOUNT_ID = None


def setKey(access_key, secret_key, private_key=None):
    global ACCESS_KEY, SECRET_KEY, PRIVATE_KEY
    ACCESS_KEY = access_key
    SECRET_KEY = secret_key
    PRIVATE_KEY = private_key

def setUrl(market_url, trade_url):
    global MARKET_URL, TRADE_URL
    MARKET_URL = market_url
    TRADE_URL = trade_url

def createSign(pParams, method, host_url, request_path, secret_key):
    """
    from 火币demo, 构造签名
    :param pParams:
    :param method:
    :param host_url:
    :param request_path:
    :param secret_key:
    :return:
    """
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

def createPrivateSign(secret_sign, private_key):
    signingkey = SigningKey.from_pem(private_key, hashfunc=hashlib.sha256)
    secret_sign = secret_sign.encode(encoding='UTF8')

    privateSignature = signingkey.sign(secret_sign)
    privateSignature = base64.b64encode(privateSignature)
    return privateSignature

def http_get_request(url, params, add_to_headers=None, _async=False):
    """
    from 火币demo, get方法
    :param url:
    :param params:
    :param add_to_headers:
    :return:
    """
    headers = {
        'Content-type':
        'application/x-www-form-urlencoded',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = urllib.parse.urlencode(params)
    if _async:
        response = async_session.get(url, params=postdata, headers=headers, timeout=5)
        return response
    else:
        response = requests.get(url, postdata, headers=headers, timeout=5)
        try:
            if response.status_code == 200:
                return response.json()
            else:
                logger.debug(
                    f'<GET>error_code:{response.status_code}  reason:{response.reason} detail:{response.text}')
                return
        except BaseException as e:
            logger.exception(f'<GET>httpGet failed, detail is:{response.text},{e}')
            return


def http_post_request(url, params, add_to_headers=None, _async=False):
    """
    from 火币demo, post方法
    :param url:
    :param params:
    :param add_to_headers:
    :return:
    """
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    if _async:
        response = async_session.post(url, postdata, headers=headers, timeout=10)
        return response
    else:
        response = requests.post(url, postdata, headers=headers, timeout=10)
        try:

            if response.status_code == 200:
                return response.json()
            else:
                logger.debug(f'<POST>error_code:{response.status_code}  reason:{response.reason} detail:{response.text}')
                return
        except BaseException as e:
            logger.exception(
                f'<POST>httpPost failed, detail is:{response.text},{e}')
            return


def api_key_get(params, request_path, _async=False):
    """
    from 火币demo, 构造get请求并调用get方法
    :param params:
    :param request_path:
    :return:
    """
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({
        'AccessKeyId': ACCESS_KEY,
        'SignatureMethod': 'HmacSHA256',
        'SignatureVersion': '2',
        'Timestamp': timestamp
    })

    host_url = TRADE_URL
    host_name = urllib.parse.urlparse(host_url).hostname
    host_name = host_name.lower()
    secret_sign = createSign(params, method, host_name, request_path,
                                     SECRET_KEY)
    params['Signature'] = secret_sign
    if PRIVATE_KEY:
        params['PrivateSignature'] = createPrivateSign(secret_sign, PRIVATE_KEY)
    url = host_url + request_path
    return http_get_request(url, params, _async=_async)


def api_key_post(params, request_path, _async=False):
    """
    from 火币demo, 构造post请求并调用post方法
    :param params:
    :param request_path:
    :return:
    """
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {
        'AccessKeyId': ACCESS_KEY,
        'SignatureMethod': 'HmacSHA256',
        'SignatureVersion': '2',
        'Timestamp': timestamp
    }

    host_url = TRADE_URL
    host_name = urllib.parse.urlparse(host_url).hostname
    host_name = host_name.lower()
    secret_sign = createSign(params_to_sign, method, host_name,
                                             request_path, SECRET_KEY)
    params_to_sign['Signature'] = secret_sign
    if PRIVATE_KEY:
        params_to_sign['PrivateSignature'] = createPrivateSign(secret_sign, PRIVATE_KEY)
    url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
    return http_post_request(url, params, _async=_async)


def handler_profiler(filename=None):
    """
    handler的性能测试装饰器
    :param filename:
    :return:
    """
    if filename == None:
        f = sys.stdout
    else:
        f = open(filename, 'w')
    def _callfunc(handle):
        @wraps(handle)
        def func(self, topic, msg):
            t0 = time.time()
            handle(self, topic, msg)
            t1 = time.time()
            print(f'{self.name}-handle运行时间:{t1 - t0}s', file=f)

        return func
    return _callfunc

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]