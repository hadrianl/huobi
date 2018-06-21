#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/13 0013 16:36
# @Author  : Hadrianl
# @File    : datatype.py
# @Contact   : 137150224@qq.com

import pandas as pd
from .service import HBRestAPI
from .utils import PERIOD, DEPTH, logger
from itertools import chain

__all__ = ['HBData']
_api = HBRestAPI(get_acc=True)


class HBKline:
    def __init__(self, symbol):
        self.__symbol = symbol

    def __getattr__(self, item):
        global _api
        if item[0] == '_':
            args = item[1:].split('_')
            if args[0] not in PERIOD:
                raise Exception('period not exist.')
            else:
                reply = _api.get_kline(self.__symbol, args[0], int(args[1]))
                klines = pd.DataFrame(reply['data'])
                return klines
        elif item == 'latest':
            reply = _api.get_latest_1m_ohlc(self.__symbol)
            latest_kline = pd.Series(reply['tick'])
            return latest_kline
        elif item == 'last_24_hour':
            reply = _api.get_lastest_24H_detail(self.__symbol)
            last_24h = pd.Series(reply['tick'])
            return last_24h
        else:
            raise AttributeError

    def __repr__(self):
        return f'<{self.__class__} for {self.__symbol}>'

    def __str__(self):
        return f'<{self.__class__} for {self.__symbol}>'


class HBDepth:
    def __init__(self, symbol):
        self.__symbol = symbol

    def __getattr__(self, item):
        global _api
        if item in (d for d in DEPTH.values()):
            reply = _api.get_latest_depth(self.__symbol, item)
            bids, asks = reply['tick']['bids'], reply['tick']['asks']
            df_bids = pd.DataFrame(bids, columns=['bid', 'bid_qty'])
            df_asks = pd.DataFrame(asks, columns=['ask', 'ask_qty'])
            depth = pd.concat([df_bids, df_asks], 1)
            return depth
        else:
            raise AttributeError

    def __repr__(self):
        return f'<{self.__class__} for {self.__symbol}>'

    def __str__(self):
        return f'<{self.__class__} for {self.__symbol}>'


class HBTicker:
    def __init__(self, symbol):
        self.__symbol = symbol

    def __getattr__(self, item):
        global _api
        if item == 'latest':
            reply = _api.get_latest_ticker(self.__symbol)
            latest_ticker = pd.DataFrame(reply['tick']['data'])
            return latest_ticker
        elif 'last' in item:
            args = item.split('_')
            size = int(args[1])
            reply = _api.get_ticker(self.__symbol, size)
            ticker_list = [
                t for t in chain(*[i['data'] for i in reply['data']])
            ]
            tickers = pd.DataFrame(ticker_list)
            return tickers

    def __repr__(self):
        return f'<{self.__class__} for {self.__symbol}>'

    def __str__(self):
        return f'<{self.__class__} for {self.__symbol}>'

class HBSymbol:
    def __init__(self, name, **kwargs):
        self.name = name
        self.attr = kwargs
        for k, v in kwargs.items():
            k = k.replace('-', '_')
            setattr(self, k, v)
        self.kline = HBKline(self.name)
        self.depth = HBDepth(self.name)
        self.ticker = HBTicker(self.name)

    def __repr__(self):
        return f'<Symbol:{self.name}-{self.attr}>'

    def __str__(self):
        return f'<Symbol:{self.name}-{self.attr}>'


class HBData:
    """
    火币的集成数据类，快速获取数据
    """

    def __init__(self, site='Pro'):
        self.site = site
        self.symbols = []
        self._update_symbols()

    def add_symbol(self, symbol):
        setattr(self, symbol.name, symbol)

    def _update_symbols(self):
        global _api
        _symbols = _api.get_symbols(self.site)
        if _symbols['status'] == 'ok':
            for d in _symbols['data']:  # 获取交易对信息
                name = d['base-currency'] + d['quote-currency']
                self.add_symbol(HBSymbol(name, **d))
                self.symbols.append(name)
        else:
            raise Exception(f'err-code:{_symbols["err-code"]}  err-msg:{_symbols["err-msg"]}')

    def __repr__(self):
        return f'<HBData>:{self.symbols}'

    def __str__(self):
        return f'<HBData>:{self.symbols}'

    def __getattr__(self, item):
        global _api
        if item == 'all_24h_ohlc':
            return _api.get_all_lastest_24h_ohlc()


class HBOrder:
    def __init__(self, acc_id, site):
        self.acc_id = acc_id
        self.site = site

    def send(self, amount, symbol, _type, price=0):
        ret = _api.send_order(self.acc_id, amount, symbol, _type, price, site=self.site)
        logger.debug(f'send_order_ret:{ret}')
        if ret and ret['status'] == 'ok':
            return ret['data']
        else:
            raise Exception(f'send order request failed!--{ret}')

    def cancel(self, order_id):
        ret = _api.cancel_order(order_id)
        logger.debug(f'cancel_order_ret:{ret}')
        if ret and ret['status'] == 'ok':
            return ret['data']
        else:
            raise Exception(f'cancel order request failed!--{ret}')

    def batchcancel(self, order_ids:list):
        ret = _api.batchcancel_order(order_ids)
        logger.debug(f'batchcancel_order_ret:{ret}')
        if ret and ret['status'] == 'ok':
            return ret['data']
        else:
            raise Exception(f'batchcancel order request failed!--{ret}')

    def __getitem__(self, item):
        oi_ret = _api.get_order_info(item, _async=True)
        mr_ret = _api.get_order_matchresults(item, _async=True)
        ret = _api.async_request([oi_ret, mr_ret])
        logger.debug(f'get_order_ret:{ret}')
        d = dict()
        if all(ret):
            if ret[0]['status'] == 'ok':
                d.update({'order_info': ret[0]['data']})
            else:
                d.update({'order_info':{}})

            if ret[1]['status'] == 'ok':
                d.update({'match_result': ret[1]['data']})
            else:
                d.update({'match_result': {}})
            return d
        else:
            raise Exception(f'get order request failed--{ret}')


class HBAccount:
    def __init__(self):
        ret = _api.get_accounts()
        logger.debug(f'get_order_ret:{ret}')
        if ret and ret['status'] == 'ok':
            data = ret['data']
            self.Detail = pd.DataFrame(data).set_index('id')
        else:
            raise Exception(f'get accounts request failed--{ret}')

    def __getattr__(self, item):
        try:
            args = item.split('_')
            if int(args[1]) in self.Detail.index.tolist():
                if args[2] == 'balance':
                    bal = HBBalance(args[1], args[0])
                    setattr(self, item, bal)
                    return bal
                elif args[2] == 'order':
                    order = HBOrder(args[1], args[0])
                    setattr(self, item, order)
                    return order
                else:
                    raise AttributeError
            else:
                raise AttributeError
        except Exception as e:
            raise e




class HBBalance:
    def __init__(self, account_id, site):
        self.acc_id = account_id
        self.site = site
        self.update()

    def update(self):
        ret = _api.get_balance(self.acc_id, self.site)
        if ret and ret['status'] == 'ok':
            data = ret['data']
            self.Id = data['id']
            self.Type = data['type']
            self.State = data['state']
            self.Detail = pd.DataFrame(data['list']).set_index('currency')
        else:
            raise Exception(f'get balance request failed--{ret}')

    def __repr__(self):
        return f'<HBBalance: {self.site}>ID:{self.Id} Type:{self.Type} State:{self.State}'

    def __str__(self):
        return f'<HBBalance: {self.site}>ID:{self.Id} Type:{self.Type} State:{self.State}'


# class HBMargin:
#     def __init__(self, account_id):

