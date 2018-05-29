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
from . import utils as u
from .utils import logger, api_key_get, api_key_post, http_get_request, http_post_request
from threading import Thread
import datetime as dt
from dateutil import parser



logger.debug(f'<TESTING>LOG_TESTING')
class HBWebsocket():
    def __init__(self, addr='wss://api.huobi.br.com/ws'):
        self._addr = addr
        self.msg_queue = Queue()
        self.sub_list = set()
        self.handlers = {}

    # def on_data(self, ws, data, data_type, flag):
    #     print(data)
    #     print(data_type)
    #     print(flag)

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
        logger.error(f'<错误>on_error:{error}')

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


class HBRestAPI():
    def __init__(self):
        self.acct_id = self.get_accounts()['data'][0]['id']
    # 获取KLine
    def get_kline(self, symbol, period, size=150):
        """
        :param symbol
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
        :param size: 可选值： [1,2000]
        :return:
        """
        params = {'symbol': symbol,
                  'period': period,
                  'size': size}

        url = u.MARKET_URL + '/market/history/kline'
        return http_get_request(url, params)

    # 获取marketdepth
    def get_latest_depth(self, symbol, type):
        """
        :param symbol
        :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return:
        """
        params = {'symbol': symbol,
                  'type': type}

        url = u.MARKET_URL + '/market/depth'
        return http_get_request(url, params)

    # 获取tradedetail
    def get_latest_ticker(self, symbol):
        """
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/trade'
        return http_get_request(url, params)

    # 获取merge ticker
    def get_latest_1m_ohlc(self, symbol):
        """
        :param symbol:
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/detail/merged'
        return http_get_request(url, params)

    # 获取 Market Detail 24小时成交量数据
    def get_lastest_24H_detail(self, symbol):
        """
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/detail'
        return http_get_request(url, params)

    # 获取  支持的交易对
    def get_symbols(self, site='Pro'):
        """
        """
        assert site in ['Pro', 'HADAX']
        params = {}
        path = f'/v1/{"common" if site == "Pro" else "hadax"}/symbols'
        return api_key_get(params, path)

    def get_currencys(self, site='Pro'):
        """

        :return:
        """
        assert site in ['Pro', 'HADAX']
        params = {}
        path = f'/v1/{"common" if site == "Pro" else "hadax"}/currencys'
        return api_key_get(params, path)

    def get_timestamp(self):
        params = {}
        path = '/v1/common/timestamp'
        return api_key_get(params, path)

    '''
    Trade/Account API
    '''

    def get_accounts(self):
        """
        :return:
        """
        path = '/v1/account/accounts'
        params = {}
        return api_key_get(params, path)


    # 获取当前账户资产
    def get_balance(self, site='Pro'):
        """
        :return:
        """
        assert site in ['Pro', 'HADAX']
        path = f'/v1{"/" if site == "Pro" else "/hadax"}account/accounts/{self.acct_id}/balance'
        # params = {'account-id': self.acct_id}
        params = {}
        return api_key_get(params, path)

    # 下单

    # 创建并执行订单
    def send_order(self, amount,  symbol, _type, price=0, site='Pro'):
        """
        :param amount:
        :param source: 如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖, buy-ioc：IOC买单, sell-ioc：IOC卖单}
        :param price:
        :return:
        """
        assert site in ['Pro', 'HADAX']
        assert _type in u.ORDER_TYPE
        params = {'account-id': self.acct_id,
                  'amount': amount,
                  'symbol': symbol,
                  'type': _type,
                  'source': 'api'}
        if price:
            params['price'] = price

        path = f'/v1{"/" if site == "Pro" else "/hadax"}order/orders/place'
        return api_key_post(params, path)

    # 撤销订单
    def cancel_order(self, order_id):
        """

        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}/submitcancel'
        return api_key_post(params, path)

    # 批量撤销订单
    def batchcancel_order(self, order_ids:list):
        """

        :param order_id:
        :return:
        """
        assert isinstance(order_ids, list)
        params = {'order-ids': order_ids}
        path = f'/v1/order/orders/batchcancel'
        return api_key_post(params, path)

    # 查询某个订单
    def get_order_info(self, order_id):
        """

        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}'
        return api_key_get(params, path)

    # 查询某个订单的成交明细
    def get_order_matchresults(self, order_id):
        """

        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}/matchresults'
        return api_key_get(params, path)

    # 查询当前委托、历史委托
    def get_orders_info(self, symbol, states, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
        """

        :param symbol:
        :param states: 可选值 {pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销}
        :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param start_date:
        :param end_date:
        :param _from:
        :param direct: 可选值{prev 向前，next 向后}
        :param size:
        :return:
        """
        params = {'symbol': symbol,
                  'states': states}

        if types:
            params[types] = types
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if _from:
            params['from'] = _from
        if direct:
            assert direct in ['prev', 'next']
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/order/orders'
        return api_key_get(params, path)

    # 查询当前成交、历史成交
    def get_orders_matchresults(self, symbol, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
        """

        :param symbol:
        :param types: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param start_date:
        :param end_date:
        :param _from:
        :param direct: 可选值{prev 向前，next 向后}
        :param size:
        :return:
        """
        params = {'symbol': symbol}

        if types:
            params[types] = types
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/order/matchresults'
        return api_key_get(params, path)

    # 申请提现虚拟币
    def req_withdraw(self, address, amount, currency, fee=0, addr_tag=""):
        """
        :param address_id:
        :param amount:
        :param currency:btc, ltc, bcc, eth, etc ...(火币Pro支持的币种)
        :param fee:
        :param addr-tag:
        :return: {
                  "status": "ok",
                  "data": 700
                }
        """
        params = {'address': address,
                  'amount': amount,
                  'currency': currency,
                  'fee': fee,
                  'addr-tag': addr_tag}
        path = '/v1/dw/withdraw/api/create'

        return api_key_post(params, path)

    # 申请取消提现虚拟币
    def cancel_withdraw(self, address_id):
        """
        :param address_id:
        :return: {
                  "status": "ok",
                  "data": 700
                }
        """
        params = {}
        path = f'/v1/dw/withdraw-virtual/{address_id}/cancel'

        return api_key_post(params, path)

    def get_deposit_withdraw_record(self, currency, _type, _from, size):
        """

        :param currency:
        :param _type:
        :param _from:
        :param size:
        :return:
        """
        assert _type in ['deposit', 'withdraw']
        params = {'currency': currency,
                  'type': _type,
                  'from': _from,
                  'size': size}
        path = '/v1/query/deposit-withdraw'
        return api_key_get(params, path)

    '''
    借贷API
    '''

    # 创建并执行借贷订单

    def send_margin_order(self, amount, symbol, _type, price=0):
        """
        :param amount:
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price:
        :return:
        """

        params = {'account-id': self.acct_id,
                  'amount': amount,
                  'symbol': symbol,
                  'type': _type,
                  'source': 'margin-api'}
        if price:
            params['price'] = price

        path = '/v1/order/orders/place'
        return api_key_post(params, path)

    # 现货账户划入至借贷账户

    def exchange_to_margin(self, symbol, currency, amount):
        """
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol,
                  'currency': currency,
                  'amount': amount}

        path = '/v1/dw/transfer-in/margin'
        return api_key_post(params, path)

    # 借贷账户划出至现货账户

    def margin_to_exchange(self, symbol, currency, amount):
        """
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol,
                  'currency': currency,
                  'amount': amount}

        path = '/v1/dw/transfer-out/margin'
        return api_key_post(params, path)

    # 申请借贷
    def req_margin(self, symbol, currency, amount):
        """
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol,
                  'currency': currency,
                  'amount': amount}
        path = '/v1/margin/orders'
        return api_key_post(params, path)

    # 归还借贷
    def repay_margin(self, order_id, amount):
        """
        :param order_id:
        :param amount:
        :return:
        """
        params = {'order-id': order_id,
                  'amount': amount}
        path = f'/v1/margin/orders/{order_id}/repay'
        return api_key_post(params, path)

    # 借贷订单
    def get_loan_orders(self, symbol, currency, start_date="", end_date="", start="", direct="", size=""):
        """
        :param symbol:
        :param currency:
        :param direct: prev 向前，next 向后
        :return:
        """
        params = {'symbol': symbol,
                  'currency': currency}
        if start_date:
            params['start-date'] = start_date
        if end_date:
            params['end-date'] = end_date
        if start:
            params['from'] = start
        if direct and direct in ['prev', 'next']:
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/margin/loan-orders'
        return api_key_get(params, path)

    # 借贷账户详情,支持查询单个币种
    def get_margin_balance(self, symbol):
        """
        :param symbol:
        :return:
        """
        params = {}
        path = '/v1/margin/accounts/balance'
        if symbol:
            params['symbol'] = symbol

        return api_key_get(params, path)


if __name__ == '__main__':
    import time
    hb = HBWebsocket()
    hb.run()
    time.sleep(1)
    hb.sub_kline('ethbtc', '1min')
    from handler import DBHandler
    handler = DBHandler()
    hb.register_handler(handler, 'market.ethbtc.kline.1min')
    api = HBRestAPI()
    print(api.get_timestamp())


