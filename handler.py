#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/25 0025 14:52
# @Author  : Hadrianl 
# @File    : handler.py
# @Contact   : 137150224@qq.com

import pymongo as pmo
from .utils import logger
from threading import Thread
from queue import Queue,Empty
from abc import abstractmethod

class baseHandler():
    def __init__(self, name):
        self.name = name
        self.thread = Thread()
        self.queue = Queue()

    def run(self):
        while True:
            try:
                msg = self.queue.get(timeout=5)
                if msg == None:  # 向队列传入None来作为结束信号
                    break
                self.handle(msg)
            except Empty:
                ...
            except Exception as e:
                logger.exception(f'<Handler>-{self.name} exception:{e}')

    def stop(self):
        self.queue.put(None)
        self.thread.join()

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


class DBHandler(pmo.MongoClient, baseHandler):
    def __init__(self, host='localhost', port=27017, db='HuoBi'):
        pmo.MongoClient.__init__(self, host, port)
        baseHandler.__init__(self, name='DB')
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

    def handle(self, msg):
        if 'ch' in msg or 'rep' in msg:
            topic = msg.get('ch') or msg.get('rep')
            data = msg.get('tick') or msg.get('data')
            self.into_db(data, topic)


