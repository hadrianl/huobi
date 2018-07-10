#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/25 0025 14:52
# @Author  : Hadrianl
# @File    : handler.py
# @Contact   : 137150224@qq.com

import pymongo as pmo
from .utils import logger, handler_profiler, zmq_ctx
from threading import Thread, Timer
from abc import abstractmethod
import zmq
import pickle
from .extra.rpc import RPCServer


class BaseHandler:
    def __init__(self, name, topic: (str, list) = None, *args, **kwargs):
        self.name = name
        self.topic = set(topic if isinstance(topic, list) else
                         [topic]) if topic is not None else set()
        self.ctx = zmq_ctx
        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.setsockopt(zmq.RCVTIMEO, 3000)

        if self.topic:  # 如果topic默认为None，则对所有的topic做处理
            for t in self.topic:
                self.sub_socket.setsockopt(zmq.SUBSCRIBE, pickle.dumps(t))
        else:
            self.sub_socket.subscribe('')

        if kwargs.get('latest', False):  # 可以通过latest(bool)来订阅最新的数据
            self.latest_handle_thread = Thread(name=f'{self.name}-latest_handle')
            self.latest = True
        else:
            self.latest = False
        self.thread = Thread(name=self.name)
        self.__active = False

    def run(self):
        self.sub_socket.connect('inproc://HBWS')
        while self.__active:
            try:
                topic_, msg_ = self.sub_socket.recv_multipart()
                if msg_ is None:  # 向队列传入None来作为结束信号
                    break
                topic = pickle.loads(topic_)
                msg = pickle.loads(msg_)
                if not self.latest:  # 对所有msg做处理
                    self.handle(topic, msg)
                elif not self.latest_handle_thread.is_alive():  # 只对latest的msg做处理
                    self.latest_handle_thread = Thread(target=self.handle, args=(topic, msg), name=f'{self.name}-latest_handle')
                    self.latest_handle_thread.setDaemon(True)
                    self.latest_handle_thread.start()
            except zmq.error.Again:
                ...
            except Exception as e:
                logger.exception(f'<Handler>-{self.name} exception:{e}')
        self.sub_socket.disconnect('inproc://HBWS')

    def add_topic(self, new_topic):
        self.sub_socket.setsockopt(zmq.SUBSCRIBE, pickle.dumps(new_topic))
        self.topic.add(new_topic)

    def remove_topic(self, topic):
        self.sub_socket.setsockopt(zmq.UNSUBSCRIBE, pickle.dumps(topic))
        self.topic.remove(topic)

    def stop(self):
        self.__active = False
        self.thread.join()

    def start(self):
        self.__active = True
        self.thread = Thread(target=self.run, name=self.name)
        self.thread.setDaemon(True)
        self.thread.start()

    @abstractmethod
    def handle(self, topic, msg):  # 所有handler需要重写这个函数
        ...


class TimeHandler:
    def __init__(self, name, interval, get_msg=None):
        self.name = name
        self.interval = interval
        self.get_msg = get_msg

    def run(self):
        try:
            msg = self.get_msg() if self.get_msg else None
            self.handle(msg)
        except Exception as e:
            logger.exception(f'<TimeHandler>-{self.name} exception:{e}')

    def stop(self):
        self.timer.cancel()
        self.timer.join()

    def start(self):
        self.timer = Timer(self.interval, self.run)
        self.timer.setName(self.name)
        self.timer.setDaemon(True)
        self.timer.start()

    @abstractmethod
    def handle(self, topic, msg):
        ...


class DBHandler(BaseHandler, pmo.MongoClient):
    def __init__(self, topic=None, host='localhost', port=27017, db='HuoBi'):
        BaseHandler.__init__(self, 'DB', topic)
        pmo.MongoClient.__init__(self, host, port)
        self.db = self.get_database(db)

    def into_db(self, data, topic: str):
        collection = self.db.get_collection(topic)
        try:
            if 'kline' in topic:
                if isinstance(data, dict):
                    collection.update({'id': data['id']}, data, upsert=True)
                elif isinstance(data, list):
                    for d in data:
                        collection.update({'id': d['id']}, d, upsert=True)
            elif 'trade.detail' in topic:
                for d in data:
                    collection.update({'id': d['id']}, d, upsert=True)
        except Exception as e:
            logger.error(f'<数据>插入数据库错误-{e}')

    def handle(self, topic, msg):
        if 'ch' in msg or 'rep' in msg:
            topic = msg.get('ch') or msg.get('rep')
            data = msg.get('tick') or msg.get('data')
            self.into_db(data, topic)


class RPCServerHandler(BaseHandler):
    def __init__(self, reqPort=6868, pubPort=6869, topic=None):
        BaseHandler.__init__(self, 'RPCServer', topic)
        self.rpcServer = RPCServer(reqPort, pubPort)
        self.rpcServer.startREP()

    def handle(self, topic, msg):
        self.rpcServer.publish(topic, msg)

    def register_func(self, name, func):
        self.rpcServer.register_rpcFunc(name, func)

    def unregister_func(self, name):
        self.rpcServer.unregister_rpcFunc(name)
