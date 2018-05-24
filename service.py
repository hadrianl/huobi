#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/24 0024 14:16
# @Author  : Hadrianl 
# @File    : service.py
# @Contact   : 137150224@qq.com

import logging
import websocket as ws
import gzip as gz
import json
from queue import Queue
import utils as u


logger = logging.getLogger(__name__)
logger.debug('TESTING')
class HBWebsocket():
    def __init__(self, addr='wss://api.huobi.pro/ws'):
        self._addr = addr
        self.msg_queue = Queue()
        self.ws = ws.WebSocketApp(self._addr,
                                  on_open=self.on_open,
                                  on_message=self.on_message,
                                  on_error=self.on_error,
                                  on_close=self.on_close)


    def send_message(self, ws, data):
        msg = json.dumps(data).encode()
        ws.send(msg)

    def on_message(self, ws, msg):
        # json_data = gz.decompress(msg).decode()
        print(msg)
        data = json.loads(msg)
        logger.info(f'{data}')
        if 'ping' in data:
            respond = { "pong": data['ping'] }
            self.send_message(ws, respond)
        else:
            self.msg_queue.put(data)

    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws):
        logger.info(f'已断开与{self._addr}的连接')

    def on_open(self, ws):
        self.send_message(ws, {
  "req": "market.btcusdt.kline.1min",
  "id": "id10"
})
        logger.info(f'建立与{self._addr}的连接')

    def run(self):
        self.ws.run_forever()

if __name__ == '__main__':
    hb = HBWebsocket()
    hb.run()

