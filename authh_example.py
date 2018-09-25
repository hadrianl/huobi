#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/25 0025 12:39
# @Author  : Hadrianl 
# @File    : authh_example.py
# @Contact   : 137150224@qq.com

from huobitrade.service import HBWebsocket
from huobitrade import setKey, logger
logger.setLevel('DEBUG')
setKey('access_key', 'secret_key')

auhb = HBWebsocket(auth=True)

auhb.after_auth(auhb.sub_accounts)

@auhb.after_auth
def init_sub():
    auhb.sub_accounts()
    auhb.sub_orders()

auhb.run()
