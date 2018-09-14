#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/8 0008 13:47
# @Author  : Hadrianl 
# @File    : example.py
# @Contact   : 137150224@qq.com
from huobitrade.service import HBWebsocket, HBRestAPI
from huobitrade.handler import DBHandler
from huobitrade import setKey, logger
import time
logger.setLevel('DEBUG')
# setKey('access_key', 'secret_key')

hb = HBWebsocket()
hb.run()
time.sleep(1)  # run之后连接需要一丢丢时间，sleep一下再订阅
# hb.sub_kline('ethbtc', '1min')
# hb.req_kline('ethbtc', '1min')
handler = DBHandler()
hb.register_handler(handler)

# @hb.register_handle_func('market.ethbtc.kline.1min')
# def handle(msg):
#     print('handle:', msg)

# api = HBRestAPI()
# print(api.get_timestamp())