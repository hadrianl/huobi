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
    def __init__(self, addr='wss://api.huobi.br.com/ws'):
        self._addr = addr
        self.msg_queue = Queue()
        self.ws = ws.WebSocketApp(self._addr,
                                  on_open=self.on_open,
                                  on_message=self.on_message,
                                  on_error=self.on_error,
                                  on_close=self.on_close,
                                  # on_data=self.on_data
                                  )

    def on_data(self, ws, data, data_type, flag):
        ...

    def send_message(self, msg):
        msg_json = json.dumps(msg).encode()
        self.ws.send(msg_json)

    def on_message(self, ws, msg):
        json_data = gz.decompress(msg).decode()
        # print(msg)
        data = json.loads(json_data)
        if 'ping' in data:
            pong = {'pong': data['ping']}
            self.send_message(pong)
        else:
            logger.info(f'{data}')
            self.msg_queue.put(data)

    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws):
        logger.info(f'已断开与{self._addr}的连接')

    def on_open(self, ws):
        logger.info(f'建立与{self._addr}的连接')
        self.sub_kline('bchbtc', '1min')

    def run(self):
        self.ws.run_forever()

    def sub_kline(self, symbol, period, _id=''):
        if symbol not in u.SYMBOL:
            logger.error(f'<订阅>kline-不存在Symbol:{symbol}')
            return

        if period not in u.PERIOD:
            logger.error(f'<订阅>kline-不存在Period:{period}')
            return

        msg = {'sub': f'market.{symbol}.kline.{period}', 'id': _id}
        self.send_message(msg)
        logger.info(f'<订阅>kline-发送订阅请求*{symbol}*@{period} #{_id}#')

    def sub_depth(self, symbol, depth=0, _id=''):
        if symbol not in u.SYMBOL:
            logger.error(f'<订阅>depth-不存在Symbol:{symbol}')
            return

        if depth not in u.DEPTH:
            logger.error(f'<订阅>depth-Depth:{depth}')
            return

        msg = {'sub': f'market.{symbol}.depth.{u.DEPTH[depth]}', 'id': _id}
        self.send_message(msg)
        logger.info(f'<订阅>depth-发送订阅请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')

    def sub_tick(self, symbol, id=''):
        if symbol not in u.SYMBOL:
            logger.error(f'<订阅>tick-不存在Symbol:{symbol}')
            return

        msg = {'sub': f'market.{symbol}.trade.detail', 'id': id}
        self.send_message(msg)
        logger.info(f'<订阅>tick-发送订阅请求*{symbol}* #{_id}#')




if __name__ == '__main__':
    hb = HBWebsocket()
    hb.run()

