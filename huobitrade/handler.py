#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/25 0025 14:52
# @Author  : Hadrianl 
# @File    : handler.py
# @Contact   : 137150224@qq.com

import pymongo as pmo
from .utils import logger, handler_profiler, zmq_ctx
from threading import Thread
from queue import Queue,Empty
from abc import abstractmethod
import zmq
import pickle

class baseHandler():
    def __init__(self, name, topic: (str, list)=None, *args, **kwargs):
        self.name = name
        self.topic = set(topic if isinstance(topic, list) else [topic]) if topic !=None else set()
        self.ctx = zmq_ctx
        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.setsockopt(zmq.RCVTIMEO, 3000)

        if self.topic:
            for t in self.topic:
                self.sub_socket.subscribe(t)
        else:
            self.sub_socket.subscribe('')

        if kwargs.get('latest', False):  # 可以通过lastest(bool)来订阅最新的数据
            self.sub_socket.set_hwm(1)
        self.thread = Thread(name=self.name)
        self.__active = False

    def run(self):
        self.sub_socket.connect('inproc://HBWS')
        while self.__active:
            try:
                # msg = self.queue.get(timeout=5)
                topic, msg = self.sub_socket.recv_multipart()
                if msg == None:  # 向队列传入None来作为结束信号
                    break
                msg = pickle.loads(msg)
                self.handle(msg)
            except zmq.error.Again:
                ...
            except Exception as e:
                logger.exception(f'<Handler>-{self.name} exception:{e}')
        self.sub_socket.disconnect('inproc://HBWS')

    def add_topic(self, new_topic):
        self.sub_socket.subscribe(new_topic)
        self.topic.add(new_topic)

    def remove_topic(self, topic):
        self.sub_socket.unsubscribe(topic)
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
    def handle(self, msg):  # 所有handler需要重写这个函数
        ...


class DBHandler(baseHandler, pmo.MongoClient):
    def __init__(self, topic=None, host='localhost', port=27017, db='HuoBi'):
        baseHandler.__init__(self, 'DB', topic)
        pmo.MongoClient.__init__(self, host, port)
        self.db = self.get_database(db)

    def into_db(self, data, topic:str):
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

    @handler_profiler
    def handle(self, msg):
        if 'ch' in msg or 'rep' in msg:
            topic = msg.get('ch') or msg.get('rep')
            data = msg.get('tick') or msg.get('data')
            self.into_db(data, topic)


