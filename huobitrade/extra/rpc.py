#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/25 0025 16:49
# @Author  : Hadrianl 
# @File    : rpc.py
# @Contact   : 137150224@qq.com

import zmq

from threading import Thread
import pickle
from abc import abstractmethod
from ..utils import logger


class RPC:
    """
    暂时使用pickle序列化，如果后期遇到兼容性和性能问题，可能转其他的序列化
    """
    def pack(self, data):  # 用pickle打包
        data_ = pickle.dumps(data,)
        return data_

    def unpack(self, data_):
        data = pickle.loads(data_)
        return data


class RPCServer(RPC):
    def __init__(self, repPort=6868, pubPort=6869):  #　请求端口和订阅端口
        self.__rpcFunc = {}
        self.__ctx = zmq.Context()
        self.__repSocket = self.__ctx.socket(zmq.REP)
        self.__pubSocket = self.__ctx.socket(zmq.PUB)
        self.__repSocket.bind(f'tcp://*:{repPort}')
        self.__pubSocket.bind(f'tcp://*:{pubPort}')
        self.__repSocket.setsockopt(zmq.SNDTIMEO, 3000)
        self._active = False

    def publish(self, topic, msg):  #　发布订阅消息
        topic_ = self.pack(topic)
        msg_ = self.pack(msg)
        self.__pubSocket.send_multipart([topic_, msg_])

    def rep(self):
        while self._active:
            try:
                func_name, args, kwargs = self.__repSocket.recv_pyobj()
                ret = self.__rpcFunc[func_name](*args, **kwargs)
            except zmq.error.Again:
                continue
            except Exception as e:
                ret = e
            finally:
                self.__repSocket.send_pyobj(ret)

    def startREP(self):
        if not self._active:
            self._active = True
            self.reqThread = Thread(target=self.rep, name='RPCSERVER')
            self.reqThread.setDaemon(True)
            self.reqThread.start()

    def stopREP(self):
        if self._active:
            self._active = False
            self.reqThread.join(5)

    def register_rpcFunc(self, name, func):
        self.__rpcFunc.update({name: func})

    def unregister_rpcFunc(self, name):
        self.__rpcFunc.pop(name)

    @property
    def rpcFunc(self):
        return self.__rpcFunc


class RPCClient(RPC):
    def __init__(self, reqAddr, subAddr, reqPort=6868, subPort=6869):
        self.__ctx = zmq.Context()
        self.__reqSocket = self.__ctx.socket(zmq.REQ)
        self.__subSocket = self.__ctx.socket(zmq.SUB)
        self.__subSocket.setsockopt(zmq.RCVTIMEO, 3000)
        self.__reqSocket.setsockopt(zmq.RCVTIMEO, 5000)
        self.__repAddr = f'tcp://{reqAddr}:{reqPort}'
        self.__subAddr = f'tcp://{subAddr}:{subPort}'
        self.__reqSocket.connect(self.__repAddr)
        self._active = False

    def rpcCall(self, func_name, *args, **kwargs):
        logger.debug(f'<rpcCall>func:{func_name}  args:{args} kwargs:{kwargs}')
        self.__reqSocket.send_pyobj([func_name, args, kwargs])
        ret = self.__reqSocket.recv_pyobj()
        if isinstance(ret, Exception):
            raise ret
        else:
            return ret

    def _run(self):
        self.__subSocket.connect(self.__subAddr)
        while self._active:
            try:
                ret_ = self.__subSocket.recv_multipart()
                topic, msg = [self.unpack(d_) for d_ in ret_]
                self.handle(topic, msg)
            except zmq.error.Again:
                ...
            except Exception as e:
                logger.exception(f'<RPCClient>-suberror:{e}', exc_info=True)
        self.__subSocket.disconnect(self.__subAddr)

    def startSUB(self):
        if not self._active:
            self._active = True
            self.subThread = Thread(target=self._run, name='RPCClient')
            self.subThread.setDaemon(True)
            self.subThread.start()

    def stopSUB(self):
        if self._active:
            self._active = False
            self.subThread.join(5)

    def subscribe(self, topic):
        if topic != '':
            topic_ = self.pack(topic)
            self.__subSocket.setsockopt(zmq.SUBSCRIBE, topic_)
        else:
            self.__subSocket.subscribe('')

    def unsubscribe(self, topic):
        if topic != '':
            topic_ = self.pack(topic)
            self.__subSocket.setsockopt(zmq.UNSUBSCRIBE, topic_)
        else:
            self.__subSocket.unsubscribe('')

    @abstractmethod
    def handle(self, topic, msg):
        raise NotImplementedError('Please overload handle function')

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            return self.rpcCall(item, *args, **kwargs)
        return wrapper




