#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/25 0025 16:49
# @Author  : Hadrianl 
# @File    : rpc.py
# @Contact   : 137150224@qq.com

import zmq

from threading import Thread
import traceback


class RPCServerHandler:
    def __init__(self, reqPort=6868, pubPort=6869):
        self.__rpcFunc = {}
        self.__ctx = zmq.Context()
        self.__reqSocket = self.__ctx.socket(zmq.REQ)
        self.__pubSocket = self.__ctx.socket(zmq.PUB)
        self.__reqSocket.bind(f'tcp://*:{reqPort}')
        self.__pubSocket.bind(f'tcp://*:{pubPort}')
        self.__reqSocket.setsockopt(zmq.SNDTIMEO, 3000)
        self.reqThread = Thread(target=self.req, name='RPCSERVER')
        self.__actitve = False

    def publish(self, msg):
        self.__pubSocket.send_pyobj(msg)

    def req(self):
        while self.__active:
            try:
                func_name, args, kwargs = self.__reqSocket.recv_pyobj()
                ret = self.__rpcFunc[func_name](*args, **kwargs)
            except zmq.error.Again:
                continue
            except Exception as e:
                ret = e
            finally:
                self.__reqSocket.send_pyobj(ret)

    def start(self):
        if not self.__actitve and not self.reqThread.is_alive():
            self.__actitve = True
            self.reqThread.start()

    def stop(self):
        if self.reqThread.is_alive():
            self.__acitve = False
            self.reqThread.join(5)

    def register_rpcFunc(self, name, func):
        self.__rpcFunc.update({name: func})

    def unregister_rpcFunc(self, name):
        self.__rpcFunc.pop(name)

    @property
    def rpcFunc(self):
        return self.__rpcFunc


class PRCClient:
    def __init__(self, repAddr, subAddr, repPort=6868, subPort=6869):
        self.__ctx = zmq.Context()
        self.__repSocket = self.__ctx.socket(zmq.REP)
        self.__subSocket = self.__ctx.socket(zmq.SUB)
        self.__repSocket.bind(f'tcp://{repAddr}:{repPort}')
        self.__subSocket.bind(f'tcp://{subAddr}:{subPort}')

    def rpcCall(self, func_name, *args, **kwargs):
        self.__repSocket.send_pyobj([func_name, args, kwargs])
        ret = self.__repSocket.recv_pyobj()
        if isinstance(ret, Exception):
            raise ret
        else:
            return ret

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            return self.rpcCall(item, *args, **kwargs)
        return wrapper




