#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/25 0025 12:39
# @Author  : Hadrianl 
# @File    : auth_test.py
# @Contact   : 137150224@qq.com

"""
该例子仅限于用来测试鉴权接口是否能鉴权成功
"""

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
