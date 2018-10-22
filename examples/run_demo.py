#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/10/22 0022 13:33
# @Author  : Hadrianl 
# @File    : run_demo.py
# @Contact   : 137150224@qq.com


from huobitrade import HBRestAPI
from huobitrade.core import _HBWS, _AuthWS

def init(restapi:HBRestAPI, ws:_HBWS, auth_ws:_AuthWS):
    print(restapi.get_timestamp())
    print(ws.sub_depth('omgeth'))
    print(auth_ws.sub_orders())

def handle_depth(msg):
    print(msg)

def handle_account(msg):
    print(msg)

handle_func = {'market.omgeth.depth.step0': handle_depth,
               'accounts': handle_account}