#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/20 0020 9:23
# @Author  : Hadrianl 
# @File    : core.py
# @Contact   : 137150224@qq.com


import websocket as ws
import gzip as gz
import json
from . import utils as u
from .utils import logger, zmq_ctx
from threading import Thread
import datetime as dt
from dateutil import parser
from functools import wraps
import zmq
import pickle
import time
from abc import abstractmethod
import uuid
from .handler import BaseHandler
from concurrent.futures import ThreadPoolExecutor

logger.debug(f'<TESTING>LOG_TESTING')


class BaseWebsocket(object):
    ws_count = 0
    def __new__(cls, *args, **kwargs):
        cls.ws_count += 1
        if cls is _AuthWS:
            from .utils import ACCESS_KEY, SECRET_KEY
            if not (ACCESS_KEY and SECRET_KEY):
                raise Exception('ACCESS_KEY或SECRET_KEY未设置！')

        return object.__new__(cls)

    def send_message(self, msg):  # 发送消息
        msg_json = json.dumps(msg).encode()
        self.ws.send(msg_json)

    def on_message(self, _msg):  # 接收ws的消息推送并处理，包括了pingpong，处理订阅列表，以及处理数据推送
        json_data = gz.decompress(_msg).decode()
        msg = json.loads(json_data)
        logger.debug(f'{msg}')

    @abstractmethod
    def pub_msg(self, msg):
        """核心的处理函数，如果是handle_func直接处理，如果是handler，推送到handler的队列"""
        raise NotImplementedError

    def on_error(self, error):
        logger.error(f'<错误>on_error:{error}')

    def on_close(self):
        logger.info(f'<连接>已断开与{self.addr}的连接')
        if not self._active:
            return

        if self._reconn > 0:
            logger.info(f'<连接>尝试与{self.addr}进行重连')
            self.__start()
            self._reconn -= 1
            time.sleep(self._interval)
        else:
            logger.info(f'<连接>尝试与{self.addr}进行重连')
            self.__start()
            time.sleep(self._interval)

    def on_open(self):
        self._active = True
        logger.info(f'<连接>建立与{self.addr}的连接')

    # ------------------- 注册回调处理函数 -------------------------------
    def register_onRsp(self, req):
        """
        添加回调处理函数的装饰器
        :param req: 具体的topic，如
        :return:
        """
        def wrapper(_callback):
            callbackList = self._req_callbacks.setdefault(req, [])
            callbackList.append(_callback)
            return _callback
        return wrapper

    def unregister_onRsp(self, req):
        return self._req_callbacks.pop(req)

    # ------------------------------------------------------------------

    # ------------------------- 注册handler -----------------------------
    def register_handler(self, handler):  # 注册handler
        if handler not in self._handlers:
            self._handlers.append(handler)
            handler.start(self.name)

    def unregister_handler(self, handler):  # 注销handler
        if handler in self._handlers:
            self._handlers.remove(handler)
            handler.stop(self.name)

    def __add__(self, handler):
        if isinstance(handler, BaseHandler):
            self.register_handler(handler)
        else:
            raise Exception('{handler} is not aHandler')

        return self


    def __sub__(self, handler):
        if isinstance(handler, BaseHandler):
            self.unregister_handler(handler)
        else:
            raise Exception('{handler} is not aHandler')

        return self
    # -----------------------------------------------------------------

    # --------------------- 注册handle_func --------------------------
    def register_handle_func(self, topic):  # 注册handle_func
        def _wrapper(_handle_func):
            if topic not in self._handle_funcs:
                self._handle_funcs[topic] = []
            self._handle_funcs[topic].append(_handle_func)
            return _handle_func

        return _wrapper

    def unregister_handle_func(self, _handle_func_name, topic):
        """ 注销handle_func """
        handler_list = self._handle_funcs.get(topic, [])
        for i, h in enumerate(handler_list):
            if h is _handle_func_name or h.__name__ == _handle_func_name:
                handler_list.pop(i)

        if self._handle_funcs.get(topic) == []:
            self._handle_funcs.pop(topic)

    # -----------------------------------------------------------------

    # --------------------- handle属性 --------------------------------
    @property
    def handlers(self):
        return self._handlers

    @property
    def handle_funcs(self):
        return self._handle_funcs

    @property
    def OnRsp_callbacks(self):
        return self._req_callbacks
    # -----------------------------------------------------------------


    # -------------------------开关ws-----------------------------------------
    def run(self):
        if not hasattr(self, 'ws_thread') or not self.ws_thread.is_alive():
            self.__start()

    def __start(self):
        self.ws = ws.WebSocketApp(
            self.addr,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            # on_data=self.on_data
        )
        self.ws_thread = Thread(target=self.ws.run_forever, name=self.name)
        self.ws_thread.setDaemon(True)
        self.ws_thread.start()

    def stop(self):
        if hasattr(self, 'ws_thread') and self.ws_thread.is_alive():
            self._active = False
            self.ws.close()
            # self.ws_thread.join()
    # ------------------------------------------------------------------------


class _AuthWS(BaseWebsocket):
    def __init__(self, host='api.huobi.br.com',
                 reconn=10, interval=3):
        self._protocol = 'wss://'
        self._host = host
        self._path = '/ws/v1'
        self.addr = self._protocol + self._host + self._path
        self._threadPool = ThreadPoolExecutor(max_workers=3)
        # self.name = f'HuoBiAuthWS{self.ws_count}'
        self.name = f'HuoBiAuthWS_{uuid.uuid1()}'
        self.sub_dict = {}  # 订阅列表
        self._handlers = []  # 对message做处理的处理函数或处理类
        self._req_callbacks = {}
        self._handle_funcs = {}
        self._auth_callbacks = []
        self.ctx = zmq_ctx
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind(f'inproc://{self.name}')
        self._active = False
        self._reconn = reconn
        self._interval = interval

    def on_open(self):
        self._active = True
        logger.info(f'<连接>建立与{self.addr}的连接')
        self.auth()
        logger.info(f'<鉴权>向{self.addr}发起鉴权请求')

    def on_message(self, _msg):  # 鉴权ws的消息处理
        json_data = gz.decompress(_msg).decode()
        msg = json.loads(json_data)
        logger.debug(f'{msg}')
        op = msg['op']
        if op == 'ping':
            pong = {'op': 'pong', 'ts': msg['ts']}
            self.send_message(pong)
        if msg.setdefault('err-code', 0) == 0:
            if op == 'notify':
                self.pub_msg(msg)
            elif op == 'sub':
                logger.info(
                    f'<订阅>Topic:{msg["topic"]}订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["cid"]}#')
            elif op == 'unsub':
                logger.info(
                    f'<订阅>Topic:{msg["topic"]}取消订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["cid"]}#')
            elif op == 'req':
                logger.info(f'<请求>Topic:{msg["topic"]}请求数据成功 #{msg["cid"]}#')
                OnRsp = self._req_callbacks.get(msg['topic'], [])

                def callbackThread(_m):
                    for cb in OnRsp:
                        try:
                            cb(_m)
                        except Exception as e:
                            logger.error(f'<请求回调>{msg["topic"]}的回调函数{cb.__name__}异常-{e}')

                task = self._threadPool.submit(callbackThread, msg)
                # _t = Thread(target=callbackThread, args=(msg,))
                # _t.setDaemon(True)
                # _t.start()
            elif op == 'auth':
                logger.info(
                    f'<鉴权>鉴权成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["cid"]}#')
                for cb in self._auth_callbacks:
                    cb()

        else:
            logger.error(
                f'<错误>{msg.get("cid")}-OP:{op} ErrTime:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} ErrCode:{msg["err-code"]} ErrMsg:{msg["err-msg"]}'
            )

    def pub_msg(self, msg):
        """核心的处理函数，如果是handle_func直接处理，如果是handler，推送到handler的队列"""
        topic = msg.get('topic')
        self.pub_socket.send_multipart(
            [pickle.dumps(topic), pickle.dumps(msg)])

        for h in self._handle_funcs.get(topic, []):
            h(msg)

    def auth(self, cid:str =''):
        from .utils import ACCESS_KEY, SECRET_KEY, createSign
        timestamp = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params = {
          "AccessKeyId": ACCESS_KEY,
          "SignatureMethod": "HmacSHA256",
          "SignatureVersion": "2",
          "Timestamp": timestamp,}

        signature = createSign(params, 'GET', self._host, self._path, SECRET_KEY)
        params['Signature'] = signature
        params['op'] = 'auth'
        params['cid'] = cid
        self.send_message(params)
        return 'auth', cid

    def sub_accounts(self, cid:str=''):
        msg = {'op': 'sub', 'cid': cid, 'topic': 'accounts'}
        self.send_message(msg)
        logger.info(f'<订阅>accouts-发送订阅请求 #{cid}#')
        return msg['topic'], cid

    def unsub_accounts(self, cid:str=''):
        msg = {'op': 'unsub', 'cid': cid, 'topic': 'accounts'}
        self.send_message(msg)
        logger.info(f'<订阅>accouts-发送订阅取消请求 #{cid}#')
        return msg['topic'], cid

    def sub_orders(self, symbol='*', cid:str=''):
        """

        :param symbol: '*'为订阅所有订单变化
        :param cid:
        :return:
        """
        msg = {'op': 'sub', 'cid': cid, 'topic': f'orders.{symbol}'}
        self.send_message(msg)
        logger.info(f'<订阅>orders-发送订阅请求*{symbol}* #{cid}#')
        return msg['topic'], cid

    def unsub_orders(self, symbol='*', cid:str=''):
        """

        :param symbol: '*'为订阅所有订单变化
        :param cid:
        :return:
        """
        msg = {'op': 'unsub', 'cid': cid, 'topic': f'orders.{symbol}'}
        self.send_message(msg)
        logger.info(f'<订阅>orders-发送取消订阅请求*{symbol}* #{cid}#')
        return msg['topic'], cid

    # ------------------------------------------------------------------------
    # ----------------------帐户请求函数--------------------------------------
    def req_accounts(self, cid:str=''):
        msg = {'op': 'req', 'cid': cid, 'topic': 'accounts.list'}
        self.send_message(msg)
        logger.info(f'<请求>accounts-发送请求 #{cid}#')
        return msg['topic'], cid

    def req_orders(self, acc_id, symbol, states:list,
                   types:list=None,
                   start_date=None, end_date=None,
                   _from=None, direct=None,
                   size=None, cid:str=''):
        states = ','.join(states)
        msg = {'op': 'req', 'account-id': acc_id, 'symbol': symbol, 'states': states, 'cid': cid,
               'topic': 'orders.list'}
        if types:
            types = ','.join(types)
            msg['types'] = types

        if start_date:
            start_date = parser.parse(start_date).strftime('%Y-%m-%d')
            msg['start-date'] = start_date

        if end_date:
            end_date = parser.parse(end_date).strftime('%Y-%m-%d')
            msg['end-date'] = end_date

        if _from:
            msg['_from'] = _from

        if direct:
            msg['direct'] = direct

        if size:
            msg['size'] = size

        self.send_message(msg)
        logger.info(f'<请求>orders-发送请求 #{cid}#')
        return msg['topic'], cid

    def req_orders_detail(self, order_id, cid:str=''):
        msg = {'op': 'req', 'order-id': order_id, 'cid': cid, 'topic': 'orders.detail'}
        self.send_message(msg)
        logger.info(f'<请求>accounts-发送请求 #{cid}#')
        return msg['topic'], cid

    def after_auth(self,_func):  # ws开启之后需要完成的初始化处理
        @wraps(_func)
        def _callback():
            try:
                _func()
            except Exception as e:
                logger.exception(f'afer_open回调处理错误{e}')
        self._auth_callbacks.append(_callback)

        return _callback


class _HBWS(BaseWebsocket):
    def __init__(self, host='api.huobi.br.com',
                 reconn=10, interval=3):
        self._protocol = 'wss://'
        self._host = host
        self._path = '/ws'
        self.addr = self._protocol + self._host + self._path
        self._threadPool = ThreadPoolExecutor(max_workers=3)
        # self.name = f'HuoBiWS{self.ws_count}'
        self.name = f'HuoBiWS_{uuid.uuid1()}'
        self.sub_dict = {}  # 订阅列表
        self._handlers = []  # 对message做处理的处理函数或处理类
        self._req_callbacks = {}
        self._handle_funcs = {}
        self._open_callbacks = []
        self.ctx = zmq_ctx
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind(f'inproc://{self.name}')
        self._active = False
        self._reconn = reconn
        self._interval = interval

    def on_open(self):
        self._active = True
        logger.info(f'<连接>建立与{self.addr}的连接')
        for topic, subbed in self.sub_dict.items():
            msg = {'sub': subbed['topic'], 'id': subbed['id']}
            self.send_message(msg)
        else:
            logger.info(f'<订阅>初始化订阅完成')

        for fun in self._open_callbacks:
            fun()

    def on_message(self, _msg):  # 接收ws的消息推送并处理，包括了pingpong，处理订阅列表，以及处理数据推送
        json_data = gz.decompress(_msg).decode()
        msg = json.loads(json_data)
        logger.debug(f'{msg}')
        if 'ping' in msg:
            pong = {'pong': msg['ping']}
            self.send_message(pong)
        elif 'status' in msg:
            if msg['status'] == 'ok':
                if 'subbed' in msg:
                    self.sub_dict.update({
                        msg['subbed']: {
                            'topic': msg['subbed'],
                            'id': msg['id']
                        }
                    })
                    logger.info(
                        f'<订阅>Topic:{msg["subbed"]}订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["id"]}#'
                    )
                elif 'unsubbed' in msg:
                    self.sub_dict.pop(msg['unsubbed'])
                    logger.info(
                        f'<订阅>Topic:{msg["unsubbed"]}取消订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"]  / 1000)} #{msg["id"]}#'
                    )
                elif 'rep' in msg:
                    logger.info(f'<请求>Topic:{msg["rep"]}请求数据成功 #{msg["id"]}#')
                    OnRsp = self._req_callbacks.get(msg['rep'], [])
                    def callbackThread(_m):
                        for cb in OnRsp:
                            try:
                                cb(_m)
                            except Exception as e:
                                logger.error(f'<请求回调>{msg["rep"]}的回调函数{cb.__name__}异常-{e}')

                    task = self._threadPool.submit(callbackThread, msg)
                elif 'data' in msg:
                    self.pub_msg(msg)
                    # _t = Thread(target=callbackThread, args=(msg, ))
                    # _t.setDaemon(True)
                    # _t.start()
            elif msg['status'] == 'error':
                logger.error(
                    f'<错误>{msg.get("id")}-ErrTime:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} ErrCode:{msg["err-code"]} ErrMsg:{msg["err-msg"]}'
                )
        else:
            self.pub_msg(msg)

    def pub_msg(self, msg):
        """核心的处理函数，如果是handle_func直接处理，如果是handler，推送到handler的队列"""
        if 'ch' in msg:
            topic = msg.get('ch')
            self.pub_socket.send_multipart(
                [pickle.dumps(topic), pickle.dumps(msg)])

            for h in self._handle_funcs.get(topic, []):
                h(msg)

    @staticmethod
    def _check_info(**kwargs):
        log = []
        if 'period' in kwargs and kwargs['period'] not in u.PERIOD:
            log.append(f'<验证>不存在Period:{kwargs["period"]}')

        if 'depth' in kwargs and kwargs['depth'] not in u.DEPTH:
            log.append(f'<验证>不存在Depth:{kwargs["depth"]}')

        if log:
            for l in log:
                logger.warning(l)
            return False
        else:
            return True

    # ----------------------行情订阅函数---------------------------------------
    def sub_overview(self, _id=''):
        msg = {'sub': 'market.overview', 'id': _id}
        self.send_message(msg)
        logger.info(f'<订阅>overview-发送订阅请求 #{_id}#')
        return msg['sub'], _id

    def unsub_overview(self, _id=''):
        msg = {'unsub': 'market.overview', 'id': _id}
        self.send_message(msg)
        logger.info(f'<订阅>overview-发送取消订阅请求 #{_id}#')
        return msg['unsub'], _id

    def sub_kline(self, symbol, period, _id=''):
        if self._check_info(symbol=symbol, period=period):
            msg = {'sub': f'market.{symbol}.kline.{period}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>kline-发送订阅请求*{symbol}*@{period} #{_id}#')
            return msg['sub'], _id

    def unsub_kline(self, symbol, period, _id=''):
        if self._check_info(symbol=symbol, period=period):
            msg = {'unsub': f'market.{symbol}.kline.{period}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>kline-发送取消订阅请求*{symbol}*@{period} #{_id}#')
            return msg['unsub'], _id

    def sub_depth(self, symbol, depth=0, _id=''):
        if self._check_info(symbol=symbol, depth=depth):
            msg = {'sub': f'market.{symbol}.depth.{u.DEPTH[depth]}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>depth-发送订阅请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')
            return msg['sub'], _id

    def unsub_depth(self, symbol, depth=0, _id=''):
        if self._check_info(symbol=symbol, depth=depth):
            msg = {
                'unsub': f'market.{symbol}.depth.{u.DEPTH[depth]}',
                'id': _id
            }
            self.send_message(msg)
            logger.info(
                f'<订阅>depth-发送取消订阅请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')
            return msg['unsub'], _id

    def sub_tick(self, symbol, _id=''):
        if self._check_info(symbol=symbol):
            msg = {'sub': f'market.{symbol}.trade.detail', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>tick-发送订阅请求*{symbol}* #{_id}#')
            return msg['sub'], _id

    def unsub_tick(self, symbol, _id=''):
        if self._check_info(symbol=symbol):
            msg = {'unsub': f'market.{symbol}.trade.detail', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>tick-发送取消订阅请求*{symbol}* #{_id}#')
            return msg['unsub'], _id

    def sub_all_lastest_24h_ohlc(self, _id=''):
        msg = {'sub': f'market.tickers', 'id': _id}
        self.send_message(msg)
        logger.info(f'<订阅>all_ticks-发送订阅请求 #{_id}#')
        return msg['sub'], _id

    def unsub_all_lastest_24h_ohlc(self, _id=''):
        msg = {'unsub': f'market.tickers', 'id': _id}
        self.send_message(msg)
        logger.info(f'<订阅>all_ticks-发送取消订阅请求 #{_id}#')
        return msg['unsub'], _id
    # -------------------------------------------------------------------------

    # -------------------------行情请求函数----------------------------------------
    def req_kline(self, symbol, period, _id='', **kwargs):
        if self._check_info(symbol=symbol, period=period):
            msg = {'req': f'market.{symbol}.kline.{period}', 'id': _id}
            if '_from' in kwargs:
                _from = parser.parse(kwargs['_from']).timestamp() if isinstance(
                    kwargs['_from'], str) else kwargs['_from']
                msg.update({'from': int(_from)})
            if '_to' in kwargs:
                _to = parser.parse(kwargs['_to']).timestamp() if isinstance(
                    kwargs['_to'], str) else kwargs['_to']
                msg.update({'to': int(_to)})
            self.send_message(msg)
            logger.info(f'<请求>kline-发送请求*{symbol}*@{period} #{_id}#')
            return msg['req'], _id

    def req_depth(self, symbol, depth=0, _id=''):
        if self._check_info(depth=depth):
            msg = {'req': f'market.{symbol}.depth.{u.DEPTH[depth]}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<请求>depth-发送请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')
            return msg['req'], _id

    def req_tick(self, symbol, _id=''):
        msg = {'req': f'market.{symbol}.trade.detail', 'id': _id}
        self.send_message(msg)
        logger.info(f'<请求>tick-发送请求*{symbol}* #{_id}#')
        return msg['req'], _id

    def req_symbol(self, symbol, _id=''):
        msg = {'req': f'market.{symbol}.detail', 'id': _id}
        self.send_message(msg)
        logger.info(f'<请求>symbol-发送请求*{symbol}* #{_id}#')
        return msg['req'], _id

    # -------------------------------------------------------------------------

    def after_open(self,_func):  # ws开启之后需要完成的初始化处理
        @wraps(_func)
        def _callback():
            try:
                _func()
            except Exception as e:
                logger.exception(f'afer_open回调处理错误{e}')
        self._open_callbacks.append(_callback)

        return _callback


class _HBDerivativesWS(BaseWebsocket):
    def __init__(self, host='www.hbdm.com',
                 reconn=10, interval=3):
        self._protocol = 'wss://'
        self._host = host
        self._path = '/ws'
        self.addr = self._protocol + self._host + self._path
        self._threadPool = ThreadPoolExecutor(max_workers=3)
        # self.name = f'HuoBiWS{self.ws_count}'
        self.name = f'HuoBiDerivativesWS_{uuid.uuid1()}'
        self.sub_dict = {}  # 订阅列表
        self._handlers = []  # 对message做处理的处理函数或处理类
        self._req_callbacks = {}
        self._handle_funcs = {}
        self._open_callbacks = []
        self.ctx = zmq_ctx
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind(f'inproc://{self.name}')
        self._active = False
        self._reconn = reconn
        self._interval = interval

    def on_open(self):
        self._active = True
        logger.info(f'<连接>建立与{self.addr}的连接')
        for topic, subbed in self.sub_dict.items():
            msg = {'sub': subbed['topic'], 'id': subbed['id']}
            self.send_message(msg)
        else:
            logger.info(f'<订阅>初始化订阅完成')

        for fun in self._open_callbacks:
            fun()

    def on_message(self, _msg):  # 接收ws的消息推送并处理，包括了pingpong，处理订阅列表，以及处理数据推送
        json_data = gz.decompress(_msg).decode()
        msg = json.loads(json_data)
        logger.debug(f'{msg}')
        if 'ping' in msg:
            pong = {'pong': msg['ping']}
            self.send_message(pong)
        elif 'status' in msg:
            if msg['status'] == 'ok':
                if 'subbed' in msg:
                    self.sub_dict.update({
                        msg['subbed']: {
                            'topic': msg['subbed'],
                            'id': msg['id']
                        }
                    })
                    logger.info(
                        f'<订阅>Topic:{msg["subbed"]}订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["id"]}#'
                    )
                elif 'unsubbed' in msg:
                    self.sub_dict.pop(msg['unsubbed'])
                    logger.info(
                        f'<订阅>Topic:{msg["unsubbed"]}取消订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"]  / 1000)} #{msg["id"]}#'
                    )
                elif 'rep' in msg:
                    logger.info(f'<请求>Topic:{msg["rep"]}请求数据成功 #{msg["id"]}#')
                    OnRsp = self._req_callbacks.get(msg['rep'], [])
                    def callbackThread(_m):
                        for cb in OnRsp:
                            try:
                                cb(_m)
                            except Exception as e:
                                logger.error(f'<请求回调>{msg["rep"]}的回调函数{cb.__name__}异常-{e}')

                    task = self._threadPool.submit(callbackThread, msg)
                elif 'data' in msg:
                    self.pub_msg(msg)
                    # _t = Thread(target=callbackThread, args=(msg, ))
                    # _t.setDaemon(True)
                    # _t.start()
            elif msg['status'] == 'error':
                logger.error(
                    f'<错误>{msg.get("id")}-ErrTime:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} ErrCode:{msg["err-code"]} ErrMsg:{msg["err-msg"]}'
                )
        else:
            self.pub_msg(msg)


    def pub_msg(self, msg):
        """核心的处理函数，如果是handle_func直接处理，如果是handler，推送到handler的队列"""
        if 'ch' in msg:
            topic = msg.get('ch')
            self.pub_socket.send_multipart(
                [pickle.dumps(topic), pickle.dumps(msg)])

            for h in self._handle_funcs.get(topic, []):
                h(msg)

    @staticmethod
    def _check_info(**kwargs):
        log = []
        if 'period' in kwargs and kwargs['period'] not in u.PERIOD:
            log.append(f'<验证>不存在Period:{kwargs["period"]}')

        if 'depth' in kwargs and kwargs['depth'] not in u.DerivativesDEPTH:
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
            return msg['sub'], _id

    def unsub_kline(self, symbol, period, _id=''):
        if self._check_info(symbol=symbol, period=period):
            msg = {'unsub': f'market.{symbol}.kline.{period}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>kline-发送取消订阅请求*{symbol}*@{period} #{_id}#')
            return msg['unsub'], _id

    def sub_depth(self, symbol, depth=0, _id=''):
        if self._check_info(symbol=symbol, depth=depth):
            msg = {'sub': f'market.{symbol}.depth.{u.DEPTH[depth]}', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>depth-发送订阅请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')
            return msg['sub'], _id

    def unsub_depth(self, symbol, depth=0, _id=''):
        if self._check_info(symbol=symbol, depth=depth):
            msg = {
                'unsub': f'market.{symbol}.depth.{u.DEPTH[depth]}',
                'id': _id
            }
            self.send_message(msg)
            logger.info(
                f'<订阅>depth-发送取消订阅请求*{symbol}*@{u.DEPTH[depth]} #{_id}#')
            return msg['unsub'], _id

    def sub_last_24h_kline(self, symbol,  _id=''):
        msg = {'sub': f'market.{symbol}.detail', 'id': _id}
        self.send_message(msg)
        logger.info(f'<订阅>Last_24h_kline-发送订阅请求*{symbol}* #{_id}#')
        return msg['sub'], _id

    def unsub_last_24h_kline(self, symbol, _id=''):
        msg = {
            'unsub': f'market.{symbol}.detail',
            'id': _id
        }
        self.send_message(msg)
        logger.info(
            f'<订阅>Last_24h_kline-发送取消订阅请求*{symbol}* #{_id}#')
        return msg['unsub'], _id


    def sub_tick(self, symbol, _id=''):
        if self._check_info(symbol=symbol):
            msg = {'sub': f'market.{symbol}.trade.detail', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>tick-发送订阅请求*{symbol}* #{_id}#')
            return msg['sub'], _id

    def unsub_tick(self, symbol, _id=''):
        if self._check_info(symbol=symbol):
            msg = {'unsub': f'market.{symbol}.trade.detail', 'id': _id}
            self.send_message(msg)
            logger.info(f'<订阅>tick-发送取消订阅请求*{symbol}* #{_id}#')
            return msg['unsub'], _id

    # -------------------------------------------------------------------------

    # -------------------------行情请求函数----------------------------------------
    def req_kline(self, symbol, period, _id='', **kwargs):
        if self._check_info(symbol=symbol, period=period):
            msg = {'req': f'market.{symbol}.kline.{period}', 'id': _id}
            if '_from' in kwargs:
                _from = parser.parse(kwargs['_from']).timestamp() if isinstance(
                    kwargs['_from'], str) else kwargs['_from']
                msg.update({'from': int(_from)})
            if '_to' in kwargs:
                _to = parser.parse(kwargs['_to']).timestamp() if isinstance(
                    kwargs['_to'], str) else kwargs['_to']
                msg.update({'to': int(_to)})
            self.send_message(msg)
            logger.info(f'<请求>kline-发送请求*{symbol}*@{period} #{_id}#')
            return msg['req'], _id

    def req_tick(self, symbol, _id=''):
        msg = {'req': f'market.{symbol}.trade.detail', 'id': _id}
        self.send_message(msg)
        logger.info(f'<请求>tick-发送请求*{symbol}* #{_id}#')
        return msg['req'], _id

    # -------------------------------------------------------------------------

    def after_open(self,_func):  # ws开启之后需要完成的初始化处理
        @wraps(_func)
        def _callback():
            try:
                _func()
            except Exception as e:
                logger.exception(f'afer_open回调处理错误{e}')
        self._open_callbacks.append(_callback)

        return _callback


class _DerivativesAuthWS(BaseWebsocket):
    def __init__(self, host='api.hbdm.com',
                 reconn=10, interval=3):
        self._protocol = 'wss://'
        self._host = host
        self._path = '/notification'
        self.addr = self._protocol + self._host + self._path
        self._threadPool = ThreadPoolExecutor(max_workers=3)
        self.name = f'HuoBiDerivativesAuthWS_{uuid.uuid1()}'
        self.sub_dict = {}  # 订阅列表
        self._handlers = []  # 对message做处理的处理函数或处理类
        self._req_callbacks = {}
        self._handle_funcs = {}
        self._auth_callbacks = []
        self.ctx = zmq_ctx
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind(f'inproc://{self.name}')
        self._active = False
        self._reconn = reconn
        self._interval = interval

    def on_open(self):
        self._active = True
        logger.info(f'<连接>建立与{self.addr}的连接')
        self.auth()
        logger.info(f'<鉴权>向{self.addr}发起鉴权请求')

    def on_message(self, _msg):  # 鉴权ws的消息处理
        json_data = gz.decompress(_msg).decode()
        msg = json.loads(json_data)
        logger.debug(f'{msg}')
        op = msg['op']
        if op == 'ping':
            pong = {'op': 'pong', 'ts': msg['ts']}
            self.send_message(pong)
        if msg.setdefault('err-code', 0) == 0:
            if op == 'notify':
                self.pub_msg(msg)
            elif op == 'sub':
                logger.info(
                    f'<订阅>Topic:{msg["topic"]}订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["cid"]}#')
            elif op == 'unsub':
                logger.info(
                    f'<订阅>Topic:{msg["topic"]}取消订阅成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["cid"]}#')
            elif op == 'req':
                logger.info(f'<请求>Topic:{msg["topic"]}请求数据成功 #{msg["cid"]}#')
                OnRsp = self._req_callbacks.get(msg['topic'], [])

                def callbackThread(_m):
                    for cb in OnRsp:
                        try:
                            cb(_m)
                        except Exception as e:
                            logger.error(f'<请求回调>{msg["topic"]}的回调函数{cb.__name__}异常-{e}')

                task = self._threadPool.submit(callbackThread, msg)
                # _t = Thread(target=callbackThread, args=(msg,))
                # _t.setDaemon(True)
                # _t.start()
            elif op == 'auth':
                logger.info(
                    f'<鉴权>鉴权成功 Time:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} #{msg["cid"]}#')
                for cb in self._auth_callbacks:
                    cb()

        else:
            logger.error(
                f'<错误>{msg.get("cid")}-OP:{op} ErrTime:{dt.datetime.fromtimestamp(msg["ts"] / 1000)} ErrCode:{msg["err-code"]} ErrMsg:{msg["err-msg"]}'
            )

    def pub_msg(self, msg):
        """核心的处理函数，如果是handle_func直接处理，如果是handler，推送到handler的队列"""
        topic = msg.get('topic')
        self.pub_socket.send_multipart(
            [pickle.dumps(topic), pickle.dumps(msg)])

        for h in self._handle_funcs.get(topic, []):
            h(msg)

    def auth(self, cid:str =''):
        from .utils import ACCESS_KEY, SECRET_KEY, createSign
        timestamp = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params = {
          "AccessKeyId": ACCESS_KEY,
          "SignatureMethod": "HmacSHA256",
          "SignatureVersion": "2",
          "Timestamp": timestamp,}

        signature = createSign(params, 'GET', self._host, self._path, SECRET_KEY)
        params['Signature'] = signature
        params['op'] = 'auth'
        params['cid'] = cid
        params['type'] = 'api'
        self.send_message(params)
        return 'auth', cid

    # def sub_accounts(self, cid:str=''):
    #     msg = {'op': 'sub', 'cid': cid, 'topic': 'accounts'}
    #     self.send_message(msg)
    #     logger.info(f'<订阅>accouts-发送订阅请求 #{cid}#')
    #     return msg['topic'], cid
    #
    # def unsub_accounts(self, cid:str=''):
    #     msg = {'op': 'unsub', 'cid': cid, 'topic': 'accounts'}
    #     self.send_message(msg)
    #     logger.info(f'<订阅>accouts-发送订阅取消请求 #{cid}#')
    #     return msg['topic'], cid

    def sub_orders(self, symbol='*', cid:str=''):
        """

        :param symbol: '*'为订阅所有订单变化
        :param cid:
        :return:
        """
        msg = {'op': 'sub', 'cid': cid, 'topic': f'orders.{symbol}'}
        self.send_message(msg)
        logger.info(f'<订阅>orders-发送订阅请求*{symbol}* #{cid}#')
        return msg['topic'], cid

    def unsub_orders(self, symbol='*', cid:str=''):
        """

        :param symbol: '*'为订阅所有订单变化
        :param cid:
        :return:
        """
        msg = {'op': 'unsub', 'cid': cid, 'topic': f'orders.{symbol}'}
        self.send_message(msg)
        logger.info(f'<订阅>orders-发送取消订阅请求*{symbol}* #{cid}#')
        return msg['topic'], cid

    # # ------------------------------------------------------------------------
    # # ----------------------帐户请求函数--------------------------------------
    # def req_accounts(self, cid:str=''):
    #     msg = {'op': 'req', 'cid': cid, 'topic': 'accounts.list'}
    #     self.send_message(msg)
    #     logger.info(f'<请求>accounts-发送请求 #{cid}#')
    #     return msg['topic'], cid
    #
    # def req_orders(self, acc_id, symbol, states:list,
    #                types:list=None,
    #                start_date=None, end_date=None,
    #                _from=None, direct=None,
    #                size=None, cid:str=''):
    #     states = ','.join(states)
    #     msg = {'op': 'req', 'account-id': acc_id, 'symbol': symbol, 'states': states, 'cid': cid,
    #            'topic': 'orders.list'}
    #     if types:
    #         types = ','.join(types)
    #         msg['types'] = types
    #
    #     if start_date:
    #         start_date = parser.parse(start_date).strftime('%Y-%m-%d')
    #         msg['start-date'] = start_date
    #
    #     if end_date:
    #         end_date = parser.parse(end_date).strftime('%Y-%m-%d')
    #         msg['end-date'] = end_date
    #
    #     if _from:
    #         msg['_from'] = _from
    #
    #     if direct:
    #         msg['direct'] = direct
    #
    #     if size:
    #         msg['size'] = size
    #
    #     self.send_message(msg)
    #     logger.info(f'<请求>orders-发送请求 #{cid}#')
    #     return msg['topic'], cid
    #
    # def req_orders_detail(self, order_id, cid:str=''):
    #     msg = {'op': 'req', 'order-id': order_id, 'cid': cid, 'topic': 'orders.detail'}
    #     self.send_message(msg)
    #     logger.info(f'<请求>accounts-发送请求 #{cid}#')
    #     return msg['topic'], cid

    def after_auth(self,_func):  # ws开启之后需要完成的初始化处理
        @wraps(_func)
        def _callback():
            try:
                _func()
            except Exception as e:
                logger.exception(f'afer_open回调处理错误{e}')
        self._auth_callbacks.append(_callback)

        return _callback