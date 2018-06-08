#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/25 0025 14:52
# @Author  : Hadrianl 
# @File    : handler.py
# @Contact   : 137150224@qq.com

import pymongo as pmo
from .utils import logger, handler_profiler
from threading import Thread
from queue import Queue,Empty
from abc import abstractmethod

class baseHandler():
    def __init__(self, name, topic: (str, list)=None):
        self.name = name
        self.topic = set(topic if isinstance(topic, list) else [topic]) if topic !=None else set()
        self.thread = Thread(name=self.name)
        self.queue = Queue()

    def run(self):
        while True:
            try:
                msg = self.queue.get(timeout=5)
                if msg == None:  # 向队列传入None来作为结束信号
                    break

                if self.topic == set():
                    self.handle(msg)
                else:
                    topic = msg.get('ch') or msg.get('rep')
                    print(topic)
                    if topic and topic in self.topic:
                        self.handle(msg)
            except Empty:
                ...
            except Exception as e:
                logger.exception(f'<Handler>-{self.name} exception:{e}')

    def add_topic(self, new_topic):
        self.topic.add(new_topic)

    def remove_topic(self, topic):
        self.topic.remove(topic)

    def stop(self):
        self.queue.put(None)
        self.thread.join()
        self.queue = Queue()

    def start(self):
        self.thread = Thread(target=self.run, name=self.name)
        self.thread.setDaemon(True)
        self.thread.start()

    @abstractmethod
    def handle(self, msg):  # 所有handler需要重写这个函数
        ...

    def __call__(self, msg):
        if self.thread.is_alive():
            self.queue.put(msg)


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


