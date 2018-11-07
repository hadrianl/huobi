#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/8 0008 13:47
# @Author  : Hadrianl 
# @File    : example.py
# @Contact   : 137150224@qq.com

"""
该demo是用于模拟较为复杂的交易策略，
同时用上了普通行情websocket，鉴权websocket与restfulapi，
包括展示如何初始化订阅，以及如果注册handler等

"""


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

# 初始化restapi
restapi = HBRestAPI(get_acc=True)
print(restapi.get_accounts())  # 请求账户

# 构造异步请求
rep1 = restapi.get_timestamp(_async=True)
rep2 = restapi.get_all_last_24h_kline(_async=True)
result = restapi.async_request([rep1, rep2]) # 一起发起请求
for r in result:
    print(r)


# 初始化多个ws
auhb = HBWebsocket(auth=True)
hb = HBWebsocket()
hb2 = HBWebsocket()

# 注册鉴权或连接后的订阅行为, 断线重连后依然会重新订阅
auhb.after_auth(auhb.sub_accounts)
hb.after_open(partial(hb.sub_kline, 'dcreth', '1min'))
hb2.after_open(partial(hb2.sub_depth, 'dcreth'))

# 把handler与handle_func注册进相应的ws
handler = MyHandler(None)  # topic为None即订阅全部topic
auhb.register_handler(handler)
hb.register_handler(handler)
hb2.register_handler(handler)
@hb2.register_handle_func('market.dcreth.depth.step0')
def print_msg(msg):
    print('handle_func', msg)

# 开始连接ws
auhb.run()
hb.run()
hb2.run()

time.sleep(5)

# 取消订阅
auhb.unsub_accounts()
hb.unsub_kline('dcreth', '1min')
hb2.unsub_depth('dcreth')

# 注销handler与handle_func
auhb.unregister_handler(handler)
hb.unregister_handler(handler)
hb2.unregister_handler(handler)
hb2.unregister_handle_func(print_msg, 'market.dcreth.depth.step0')

# 添加req请求的回调并发起请求
@hb.register_onRsp('market.dcreth.depth.step0')
def req1_callback(msg):
    print('req1', msg)

@hb.register_onRsp('market.dcreth.depth.step0')  # 可以添加多个请求回调
def req2_callback(msg):
    print('req2', msg)
topic, ReqId = hb.req_depth('dcreth',_id='ReqId')
print(topic, ReqId)

time.sleep(2)
# 一次性将所有请求回调注销
hb.unregister_onRsp('market.dcreth.depth.step0')

time.sleep(5)


# 关闭停止ws
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