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

__all__ = ['HBMarket', 'HBAccount', 'HBMargin']
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
        elif item == 'last':
            reply = _api.get_last_1m_kline(self.__symbol)
            last_kline = pd.Series(reply['tick'])
            return last_kline
        elif item == 'last_24_hour':
            reply = _api.get_last_24h_kline(self.__symbol)
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
            reply = _api.get_last_depth(self.__symbol, item)
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
        if item == 'last':
            reply = _api.get_last_ticker(self.__symbol)
            last_ticker = pd.DataFrame(reply['tick']['data'])
            return last_ticker
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


class HBMarket:
    """
    火币的市场数据类，快捷获取数据
    """

    def __init__(self):
        self.symbols = []
        self._update_symbols()

    def add_symbol(self, symbol):
        setattr(self, symbol.name, symbol)

    def _update_symbols(self):
        global _api
        _symbols = _api.get_symbols()
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
        if item == 'all_24h_kline':
            return _api.get_all_last_24h_kline()


class HBOrder:
    def __init__(self, acc_id):
        self.acc_id = acc_id

    def send(self, amount, symbol, _type, price=0):
        ret = _api.send_order(self.acc_id, amount, symbol, _type, price)
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

    def get_by_id(self, order_id):
        oi_ret = _api.get_order_info(order_id, _async=True)
        mr_ret = _api.get_order_matchresults(order_id, _async=True)
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
            raise Exception(f'get order request failed!--{ret}')

    def get_by_symbol(self, symbol, states, types=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
        ret = _api.get_orders_info(symbol, states, types, start_date, end_date, _from, direct, size)
        logger.debug(f'get_orders_ret:{ret}')
        if ret and ret['status'] == 'ok':
            data = ret['data']
            df = pd.DataFrame(data).set_index('id')
            return df
        else:
            raise Exception(f'get orders request failed!--{ret}')

    def __getitem__(self, item):
        return self.get_by_id(item)


class HBTrade:
    def __init__(self, acc_id):
        self.acc_id = acc_id

    def get_by_id(self, order_id):
        ret = _api.get_order_matchresults(order_id)
        logger.debug(f'trade_ret:{ret}')
        if ret and ret['status'] == 'ok':
            data = ret['data']
            df = pd.DataFrame(data).set_index('id')
            return df
        else:
            raise Exception(f'trade results request failed!--{ret}')

    def get_by_symbol(self, symbol, types, start_date=None, end_date=None, _from=None, direct=None, size=None):
        ret = _api.get_orders_matchresults(symbol, types, start_date, end_date, _from, direct, size)
        logger.debug(f'trade_ret:{ret}')
        if ret and ret['status'] == 'ok':
            data = ret['data']
            df = pd.DataFrame(data).set_index('id')
            return df
        else:
            raise Exception(f'trade results request failed!--{ret}')

    def __getitem__(self, item):
        return self.get_by_id(item)


class HBAccount:
    def __init__(self):
        ret = _api.get_accounts()
        logger.debug(f'get_order_ret:{ret}')
        if ret and ret['status'] == 'ok':
            data = ret['data']
            self.Detail = pd.DataFrame(data).set_index('id')
        else:
            raise Exception(f'get accounts request failed!--{ret}')

    def __getattr__(self, item):
        try:
            args = item.split('_')
            if int(args[1]) in self.Detail.index.tolist():
                if args[0] == 'balance':
                    bal = HBBalance(args[1])
                    setattr(self.__class__, item, bal)
                    return bal
                elif args[0] == 'order':
                    order = HBOrder(args[1])
                    setattr(self, item, order)
                    return order
                elif args[0] == 'trade':
                    trade = HBTrade(args[1])
                    setattr(self, item, trade)
                    return trade
                else:
                    raise AttributeError
            else:
                raise AttributeError
        except Exception as e:
            raise e

    def __repr__(self):
        return f'<HBAccount>Detail:\n{self.Detail}'

    def __str__(self):
        return f'<HBAccount>Detail:\n{self.Detail}'


class HBBalance:
    def __init__(self, account_id):
        self.acc_id = account_id
        self.update()

    def update(self):
        ret = _api.get_balance(self.acc_id)
        if ret and ret['status'] == 'ok':
            data = ret['data']
            self.Id = data['id']
            self.Type = data['type']
            self.State = data['state']
            self.Detail = pd.DataFrame(data['list']).set_index('currency')
        else:
            raise Exception(f'get balance request failed--{ret}')

    def __get__(self, instance, owner):
        bal = instance.__dict__.setdefault('balance', {})
        bal[self.acc_id] = self
        self.update()
        return self

    def __repr__(self):
        return f'<HBBalance>ID:{self.Id} Type:{self.Type} State:{self.State}'

    def __str__(self):
        return f'<HBBalance>ID:{self.Id} Type:{self.Type} State:{self.State}'

    def __getitem__(self, item):
        return self.Detail.loc[item]


class HBMargin:
    def __init__(self):
        ...

    def transferIn(self, symbol, currency, amount):
        ret = _api.exchange_to_margin(symbol, currency, amount)
        logger.debug(f'transferIn_ret:{ret}')
        if ret and ret['status'] == 'ok':
            return ret['data']
        else:
            raise Exception(f'transferIn request failed!--{ret}')

    def transferOut(self, symbol, currency, amount):
        ret = _api.exchange_to_margin(symbol, currency, amount)
        logger.debug(f'transferOut_ret:{ret}')
        if ret and ret['status'] == 'ok':
            return ret['data']
        else:
            raise Exception(f'transferOut request failed!--{ret}')

    def applyLoan(self, symbol, currency, amount):
        ret = _api.apply_loan(symbol, currency, amount)
        logger.debug(f'apply_loan_ret:{ret}')
        if ret and ret['status'] == 'ok':
            return ret['data']
        else:
            raise Exception(f'apply_loan request failed!--{ret}')

    def repayLoan(self, symbol, currency, amount):
        ret = _api.repay_loan(symbol, currency, amount)
        logger.debug(f'repay_loan_ret:{ret}')
        if ret and ret['status'] == 'ok':
            return ret['data']
        else:
            raise Exception(f'repay_loan request failed!--{ret}')

    def getLoan(self, symbol, currency, states=None, start_date=None, end_date=None, _from=None, direct=None, size=None):
        ret = _api.get_loan_orders(symbol, currency, states, start_date, end_date, _from, direct, size)
        logger.debug(f'get_loan_ret:{ret}')
        if ret and ret['status'] == 'ok':
            df = pd.DataFrame(ret['data']).set_index('id')
            return df
        else:
            raise Exception(f'get_loan request failed!--{ret}')

    def getBalance(self, symbol):
        return HBMarginBalance(symbol)

    def __getitem__(self, item):
        return self.getBalance(item)

class HBMarginBalance:
    def __init__(self, symbol):
        ret = _api.get_margin_balance(symbol)
        logger.debug(f'<保证金结余>信息:{ret}')
        if ret and ret['status'] == 'ok':
            balance = {}
            for d in ret['data']:
                data = balance.setdefault(d['id'], {})
                data['id'] = d['id']
                data['type'] = d['type']
                data['state'] = d['state']
                data['symbol'] = d['symbol']
                data['fl-price'] = d['fl-price']
                data['fl-type'] = d['fl-type']
                data['risk-rate'] = d['risk-rate']
                data['detail'] = pd.DataFrame(d['list']).set_index('currency')
        else:
            raise Exception(f'get balance request failed--{ret}')

        self.__balance = balance

    def __repr__(self):
        info = []
        for b in self._balance.values():
            info.append(f'<HBMarginBalance: {b["symbol"]}>ID:{b["id"]} Type:{b["type"]} State:{b["state"]} Risk-rate:{b["risk-rate"]}')
            info = '\n'.join(info)
        return info

    def __str__(self):
        info = []
        for b in self.__balance:
            info.append(f'<HBMarginBalance: {b["symbol"]}>ID:{b["id"]} Type:{b["type"]} State:{b["state"]} Risk-rate:{b["risk-rate"]}')
            info = '\n'.join(info)
        return info

    def __getitem__(self, item):
        return self.__balance[item]

    @property
    def balance(self):
        return self.__balance