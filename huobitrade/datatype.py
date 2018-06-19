#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/13 0013 16:36
# @Author  : Hadrianl
# @File    : datatype.py
# @Contact   : 137150224@qq.com

import pandas as pd
from .service import HBRestAPI
from .utils import PERIOD, DEPTH
from itertools import chain

__all__ = ['HBData']
_api = HBRestAPI()


class HBKline:
    def __init__(self, symbol):
        self.__symbol = symbol

    def __getattr__(self, item):
        global _api
        if item in ('_' + p for p in PERIOD):
            reply = _api.get_kline(self.__symbol, item.strip('_'))
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
            size = int(item.strip('last'))
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

