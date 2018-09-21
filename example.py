#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/8 0008 13:47
# @Author  : Hadrianl 
# @File    : example.py
# @Contact   : 137150224@qq.com
from huobitrade.service import HBWebsocket, HBRestAPI
from huobitrade.handler import BaseHandler
from huobitrade import setKey, logger
from functools import partial
import time
# logger.setLevel('DEBUG')
setKey('access_key', 'secret_key')

class MyHandler(BaseHandler):
    def __init__(self, topic, *args, **kwargs):
        BaseHandler.__init__(self, 'just Thread name', topic)

    def handle(self, topic, msg):  # 实现handle来处理websocket推送的msg
        print(topic)

auhb = HBWebsocket(auth=True)
hb = HBWebsocket()
hb2 = HBWebsocket()
auhb.after_auth(auhb.sub_accounts)
hb.after_open(partial(hb.sub_kline, 'dcreth', '1min'))
hb2.after_open(partial(hb2.sub_depth, 'dcreth'))
handler = MyHandler(None)
auhb.register_handler(handler)
hb.register_handler(handler)
hb2.register_handler(handler)
auhb.run()
hb.run()
hb2.run()


time.sleep(30)
hb2.unregister_handler(handler)
hb.stop()
hb2.stop()
auhb.stop()

# hb.sub_kline('ethbtc', '1min')
# hb.req_kline('ethbtc', '1min')
# handler = DBHandler()
# hb.register_handler(handler)

# @hb.register_handle_func('market.dcreth.kline.1min')
# def handle(msg):
#     print('handle:', msg)

# api = HBRestAPI()
# print(api.get_timestamp())