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
from utils import logger
from threading import Thread, Condition, Lock
import datetime as dt
from dateutil import parser



logger.debug('TESTING')
class HBWebsocket():
    def __init__(self, addr='wss://api.huobi.br.com/ws'):
        self._addr = addr
        self.msg_queue = Queue()
        self.sub_list = set()
        self.handlers = {}

    def on_data(self, ws, data, data_type, flag):
        ...

    def send_message(self, msg):
        msg_json = json.dumps(msg).encode()
        self.ws.send(msg_json)

    def on_message(self, ws, _msg):
        json_data = gz.decompress(_msg).decode()
        msg = json.loads(json_data)
        if 'ping' in msg:
            pong = {'pong': msg['ping']}
            self.send_message(pong)
        elif 'status' in msg:
            if msg['status'] == 'ok':
                if 'subbed' in msg:
                    self.sub_list.add(msg['subbed'])
                    logger.info(f'<订阅>Topic:{msg["subbed"]}订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["id"]}#')
                elif 'unsubbed' in msg:
                    self.sub_list.remove(msg['unsubbed'])
                    logger.info(f'<订阅>Topic:{msg["subbed"]}取消订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"]  / 1000)} #{msg["id"]}#')
                elif 'rep' in msg:
                    logger.info(f'<请求>Topic:{msg["rep"]}请求数据成功 #{msg["id"]}#')
            elif msg['status'] == 'error':
                logger.error(f'<错误>{msg.get("id")}-ErrTime:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} ErrCode:{msg["err-code"]} ErrMsg:{msg["err-msg"]}')
        else:
            # logger.info(f'{msg}')
            self.pub_msg(msg)

    def pub_msg(self, msg):
        if 'ch' in msg or 'rep' in msg:
            topic = msg.get('ch') or msg.get('rep')

            for h in self.handlers.get(topic, []):
                h(msg)

    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws):
        logger.info(f'<连接>已断开与{self._addr}的连接')

    def on_open(self, ws):
        logger.info(f'<连接>建立与{self._addr}的连接')

    def register_handler(self, handler, topic):  # 注册handler
        if topic not in self.handlers:
            self.handlers[topic] = []
        self.handlers[topic].append(handler)
        handler.start()

    def unregister_handler(self, handler, topic):  #
        if handler in self.handlers.get(topic, []):
            self.handlers.pop(handler)

        if self.handlers.get(topic) == []:
            self.handlers.pop(topic)

    @staticmethod
    def _check_info(**kwargs):
        log = []
        if 'symbol' in kwargs and kwargs['symbol'] not in u.SYMBOL:
            log.append(f'<验证>不存在Symbol:{symbol}')

        if 'period' in kwargs and kwargs['period'] not in u.PERIOD:
            log.append(f'<验证>不存在Period:{period}')

        if 'depth' in kwargs and kwargs['depth'] not in u.DEPTH:
            log.append(f'<验证>不存在Depth:{kwargs["depth"]}')

        if log:
            for l in log:
                logger.warning(l)
            return False
        else:
            return True

    def sub_kline(self, symbol, period, _id=''):
        if self._check_info(symbol=symbol, period=period):
            msg = {'sub': f'market.{symbol}.kline.{period}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>kline-发送订阅请求*{symbol}*@{period} #{_id}#')

    def unsub_kline(self, symbol, period, _id=''):
        if self._check_info(symbol=symbol, period=period):
            msg = {'unsub': f'market.{symbol}.kline.{period}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>kline-发送取消订阅请求*{symbol}*@{period} #{_id}#')

    def sub_depth(self, symbol, depth=0, _id=''):
        if self._check_info(symbol=symbol, depth=depth):
            msg = {'sub': f'market.{symbol}.depth.{u.DEPTH[depth]}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>depth-发送订阅请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')

    def unsub_depth(self, symbol, depth=0, _id=''):
        if self._check_info(symbol=symbol, depth=depth):
            msg = {'unsub': f'market.{symbol}.depth.{u.DEPTH[depth]}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>depth-发送取消订阅请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')

    def sub_tick(self, symbol, _id=''):
        if self._check_info(symbol=symbol):
            msg = {'sub': f'market.{symbol}.trade.detail', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>tick-发送订阅请求*{symbol}* #{_id}#')

    def unsub_tick(self, symbol, _id=''):
        if self._check_info(symbol=symbol):
            msg = {'unsub': f'market.{symbol}.trade.detail', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>tick-发送取消订阅请求*{symbol}* #{_id}#')

    def rep_kline(self, symbol, period, _id='', **kwargs):
        if self._check_info(symbol=symbol, period=period):
            msg = {'req': f'market.{symbol}.kline.{period}', 'id': _id}
            if 'from' in kwargs:
                _from = parser.parse(kwargs['from']) if isinstance(kwargs['from'], str) else kwargs['from']
                msg.update({'from': _from})
            if 'to' in kwargs:
                _to = parser.parse(kwargs['to']) if isinstance(kwargs['to'], str) else kwargs['to']
                msg.update({'to': _to})
            self.send_message(msg)
            logger.info(f'<请求>kline-发送请求*{symbol}*@{period} #{_id}#')

    def rep_depth(self, symbol, depth=0, _id=''):
        if self._check_info(symbol=symbol, depth=depth):
            msg = {'req': f'market.{symbol}.depth.{u.DEPTH[depth]}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<请求>depth-发送请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')

    def rep_tick(self, symbol, _id=''):
        if self._check_info(symbol=symbol):
            msg = {'rep': f'market.{symbol}.trade.detail', 'id': _id}
            self.send_message(msg)
            logger.info(f'<请求>tick-发送请求*{symbol}* #{_id}#')


    def run(self):
        if not hasattr(self, 'ws_thread') or not self.ws_thread.is_alive():
            self.ws = ws.WebSocketApp(self._addr,
                                      on_open=self.on_open,
                                      on_message=self.on_message,
                                      on_error=self.on_error,
                                      on_close=self.on_close,
                                      # on_data=self.on_data
                                      )
            self.ws_thread = Thread(target=self.ws.run_forever)
            self.ws_thread.start()

    def stop(self):
        if hasattr(self, 'ws_thread') and self.ws_thread.is_alive():
            self.ws.close()
            self.ws_thread.join()



if __name__ == '__main__':
    import time
    hb = HBWebsocket()
    hb.run()
    time.sleep(1)
    hb.sub_kline('ethbtc', '1min')
    from handler import DBHandler
    handler = DBHandler()
    hb.register_handler(handler, 'market.ethbtc.kline.1min')

