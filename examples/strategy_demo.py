#!/usr/bin/python
# -*- coding:utf-8 -*-

"""
@author:Hadrianl

该demo主要用于展示一个简单的策略应该如何编写，其中核心部分是实现一个handler


"""
from huobitrade.handler import BaseHandler
from huobitrade.utils import logger
import pymongo as pmo


class DemoHandler(BaseHandler):
    def __init__(self, symbol, _ktype='1min'):
        self._type = _ktype
        self._symbol = symbol
        self._topic = f'market.{self._symbol}.kline.{self._type}'
        BaseHandler.__init__(self, 'market_maker', self._topic, latest=True)  # 在handle需要执行比较长时间的情况下，最好用latest，保持获取最新行情，对于在handle处理过程中推送的行情忽略
        self._db = pmo.MongoClient('localhost', 27017).get_database('HuoBi')

    def into_db(self, data, collection):

        collection = self._db.get_collection(collection)
        collection.create_index('id')
        try:
            collection.replace_one({'id': data['id']}, data, upsert=True)
        except Exception as e:
            logger.error(f'<数据>插入交易深度数据错误{e}')

    def handle(self, topic, msg):   # 核心handle函数！！！
        data = msg.get('tick')
        symbol = topic.split('.')[1]
        ts = msg.get('ts')
        self.into_db(data, topic)
        logger.info(msg)

        buy_cond = False
        sell_cond = False

        if buy_cond:
            buy_amount = ...  #买入量
            buy_price = ...  # 买入价

            api.send_order(api.acc_id, buy_amount, symbol, 'buy-limit', buy_price)

        if sell_cond:
            sell_amount = ...
            sell_price = ...
            api.send_order(api.acc_id, sell_amount, symbol, 'sell-limit', sell_price)


if __name__ == '__main__':
    from huobitrade.service import HBWebsocket, HBRestAPI
    from huobitrade import setUrl, setKey

    setKey('', '')
    # setUrl('https://api.huobi.pro', 'https://api.huobi.pro')
    ws = HBWebsocket('api.huobi.br.com')  # 生产环境请不要用api.huobi.br.com
    api = HBRestAPI(get_acc=True)  # get_acc为true，初始化时候会获取acount_id中的第一个id并赋值给acc_id属性


    @ws.after_open   # 连接成功后会调用此函数，一般在这个位置进行初始化订阅
    def sub_depth():
        ws.sub_kline('dcreth', '1min')

    ws.run()

    demo_handler = DemoHandler('dcreth')
    ws.register_handler(demo_handler)
