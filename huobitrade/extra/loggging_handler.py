#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/15 0015 14:01
# @Author  : Hadrianl 
# @File    : loggging_handler.py
# @Contact   : 137150224@qq.com

from logging import Handler, Formatter
from ..datatype import HBMarket
try:
    import itchat
    from itchat.content import TEXT
except ImportError:
    print(f'Module itchat not found.WeChatHandler is not available.')

TRADE_INFO = 60

class WeChatHandler(Handler):
    def __init__(self, chatroom=None, level=TRADE_INFO, enableCmdQR=True):
        super(WeChatHandler, self).__init__(level)
        self._CmdQR = enableCmdQR
        self._chatroom = chatroom
        self.client = itchat.new_instance()
        formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)

    def run(self):
        self.client.auto_login(hotReload=True, loginCallback=self._loginCallback, exitCallback=self._exitCallback, enableCmdQR=self._CmdQR)
        self.client.run(debug=False, blockThread=False)

    def stop(self):
        self.send_log('暂停接收HUOBI信息')
        self.client.logout()

    def _loginCallback(self):
        try:
            self.log_receiver = self.client.search_chatrooms(name=self._chatroom)[0]['UserName']
        except Exception as e:
            print(e)
            self.log_receiver = None
        self.send_log('开始接收HUOBI信息')

    def _exitCallback(self):
        print(f'微信logger->{self.log_receiver}已终止')

    def init_reply(self):
        d = HBMarket()

        @self.client.msg_register(TEXT, isGroupChat=True)
        def reply(msg):
            if msg['isAt']:
                try:
                    topic = msg['Text'].split('.')
                    v = d
                    for t in topic:
                        v = getattr(v, t)
                    self.send_log(f'{v}')
                except Exception as e:
                    print(e)

    def send_log(self, msg):
        self.client.send(msg, self.log_receiver)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.send_log(msg)
        except Exception as e:
            print(e)
