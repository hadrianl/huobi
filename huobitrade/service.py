#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/24 0024 14:16
# @Author  : Hadrianl
# @File    : service.py
# @Contact   : 137150224@qq.com


from . import utils as u
from .utils import logger, api_key_get, api_key_post, http_get_request, setUrl, setKey, Singleton
from dateutil import parser
from functools import wraps
from .core import _AuthWS, _HBWS
import warnings

logger.debug(f'<TESTING>LOG_TESTING')


def HBWebsocket(host='api.huobi.br.com', auth=False, reconn=10, interval=3):
    if auth:
        return _AuthWS(host, reconn, interval)
    else:
        return _HBWS(host, reconn, interval)



class HBRestAPI(metaclass=Singleton):
    def __init__(self, addrs=None, keys=None, get_acc=False):
        """
        火币REST API封装
        :param addrs: 传入(market_url, trade_url)，若为None，默认是https://api.huobi.br.com
        :param keys: 传入(acess_key, secret_key),可用setKey设置
        """
        if addrs:
            setUrl(*addrs)
        if keys:
            setKey(*keys)
        if get_acc:
            try:
                accounts = self.get_accounts()['data']
                self.acc_id = self.get_accounts()['data'][0]['id']
                if len(accounts) > 1:
                    warnings.warn(f'默认设置acc_id为{self.acc_id}')
            except Exception as e:
                raise Exception(f'Failed to get account: key may not be set ->{e}')

    def set_acc_id(self, acc_id):
        self.acc_id = acc_id

    def __async_request_exception_handler(self, req, e):
        logger.error(f'async_request:{req}--exception:{e}')

    def async_request(self, reqs:list)->list:
        """
        异步并发请求
        :param reqs: 请求列表
        :return:
        """
        result = (response.result() for response in reqs)
        ret = [r.json() if r.status_code == 200 else None for r in result]
        return ret

    def get_kline(self, symbol, period, size=150, _async=False):
        """
        获取KLine
        :param symbol
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
        :param size: 可选值： [1,2000]
        :return:
        """
        params = {'symbol': symbol, 'period': period, 'size': size}

        url = u.MARKET_URL + '/market/history/kline'
        return http_get_request(url, params, _async=_async)

    def get_last_depth(self, symbol, _type, _async=False):
        """
         获取marketdepth
        :param symbol
        :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return:
        """
        params = {'symbol': symbol, 'type': _type}

        url = u.MARKET_URL + '/market/depth'
        return http_get_request(url, params, _async=_async)

    def get_last_ticker(self, symbol, _async=False):
        """
        获取tradedetail
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/trade'
        return http_get_request(url, params, _async=_async)

    def get_ticker(self, symbol, size=1, _async=False):
        """
        获取历史ticker
        :param symbol:
        :param size: 可选[1,2000]
        :return:
        """
        params = {'symbol': symbol, 'size': size}

        url = u.MARKET_URL + '/market/history/trade'
        return http_get_request(url, params, _async=_async)

    def get_all_last_24h_kline(self, _async=False):
        """
        获取所有24小时的概况
        :param _async:
        :return:
        """
        params = {}
        url = u.MARKET_URL + '/market/tickers'
        return http_get_request(url, params, _async=_async)

    def get_last_1m_kline(self, symbol, _async=False):
        """
        获取最新一分钟的k线
        :param symbol:
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/detail/merged'
        return http_get_request(url, params, _async=_async)

    def get_last_24h_kline(self, symbol, _async=False):
        """
        获取最近24小时的概况
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/detail'
        return http_get_request(url, params, _async=_async)

    def get_symbols(self, site='Pro', _async=False):
        """
        获取  支持的交易对
        :param site:
        :return:
        """
        assert site in ['Pro', 'HADAX']
        params = {}
        path = f'/v1{"/" if site == "Pro" else "/hadax/"}common/symbols'
        return api_key_get(params, path, _async=_async)

    def get_currencys(self, site='Pro', _async=False):
        """
        获取所有币种
        :param site:
        :return:
        """
        assert site in ['Pro', 'HADAX']
        params = {}
        path = f'/v1{"/" if site == "Pro" else "/hadax/"}common/currencys'
        return api_key_get(params, path, _async=_async)

    def get_timestamp(self, _async=False):
        params = {}
        path = '/v1/common/timestamp'
        return api_key_get(params, path, _async=_async)

    '''
    Trade/Account API
    '''

    def get_accounts(self, _async=False):
        """
        :return:
        """
        path = '/v1/account/accounts'
        params = {}
        return api_key_get(params, path, _async=_async)

    def get_balance(self, acc_id=None, site='Pro', _async=False):
        """
        获取当前账户资产
        :return:
        """
        acc_id = self.acc_id if acc_id is None else acc_id
        assert site in ['Pro', 'HADAX']
        path = f'/v1{"/" if site == "Pro" else "/hadax/"}account/accounts/{acc_id}/balance'
        # params = {'account-id': self.acct_id}
        params = {}
        return api_key_get(params, path, _async=_async)

    def send_order(self, acc_id, amount, symbol, _type, price=0, site='Pro', _async=False):
        """
        创建并执行订单
        :param amount:
        :param source: 如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖, buy-ioc：IOC买单, sell-ioc：IOC卖单}
        :param price:
        :return:
        """
        assert site in ['Pro', 'HADAX']
        assert _type in u.ORDER_TYPE
        params = {
            'account-id': acc_id,
            'amount': amount,
            'symbol': symbol,
            'type': _type,
            'source': 'api'
        }
        if price:
            params['price'] = price

        path = f'/v1{"/" if site == "Pro" else "/hadax/"}order/orders/place'
        return api_key_post(params, path, _async=_async)

    def cancel_order(self, order_id, _async=False):
        """
        撤销订单
        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}/submitcancel'
        return api_key_post(params, path, _async=_async)

    def batchcancel_orders(self, order_ids: list, _async=False):
        """
        批量撤销订单
        :param order_id:
        :return:
        """
        assert isinstance(order_ids, list)
        params = {'order-ids': order_ids}
        path = f'/v1/order/orders/batchcancel'
        return api_key_post(params, path, _async=_async)

    def batchcancel_openOrders(self, acc_id, symbol=None, side=None, size=None, _async=False):
        """
        批量撤销未成交订单
        :param acc_id: 帐号ID
        :param symbol: 交易对
        :param side: 方向
        :param size:
        :param _async:
        :return:
        """

        params = {}
        path = '/v1/order/batchCancelOpenOrders'
        params['account-id'] = acc_id
        if symbol:
            params['symbol'] = symbol
        if side:
            assert side in ['buy', 'sell']
            params['side'] = side
        if size:
            params['size'] = size

        return api_key_get(params, path, _async=_async)



    def get_order_info(self, order_id, _async=False):
        """
        查询某个订单
        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}'
        return api_key_get(params, path, _async=_async)

    def get_openOrders(self, acc_id=None, symbol=None, side=None, size=None, _async=False):
        """
        查询未成交订单
        :param acc_id: 帐号ID
        :param symbol: 交易对ID
        :param side: 交易方向，'buy'或者'sell'
        :param size: 记录条数，最大500
        :return:
        """
        params = {}
        path = '/v1/order/openOrders'
        if all([acc_id, symbol]):
            params['account-id'] = acc_id
            params['symbol'] = symbol
        if side:
            assert side in ['buy', 'sell']
            params['side'] = side
        if size:
            params['size'] = size

        return api_key_get(params, path, _async=_async)

    def get_order_matchresults(self, order_id, _async=False):
        """
        查询某个订单的成交明细
        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}/matchresults'
        return api_key_get(params, path, _async=_async)

    def get_orders_info(self,
                        symbol,
                        states:list,
                        types:list=None,
                        start_date=None,
                        end_date=None,
                        _from=None,
                        direct=None,
                        size=None,
                        _async=False):
        """
        查询当前委托、历史委托
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
        states = ','.join(states)
        params = {'symbol': symbol, 'states': states}

        if types:
            params['types'] = ','.join(types)
        if start_date:
            sd = parser.parse(start_date).date()
            params['start-date'] = str(sd)
        if end_date:
            ed = parser.parse(end_date).date()
            params['end-date'] = str(ed)
        if _from:
            params['from'] = _from
        if direct:
            assert direct in ['prev', 'next']
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/order/orders'
        return api_key_get(params, path, _async=_async)

    def get_orders_matchresults(self,
                                symbol,
                                types:list=None,
                                start_date=None,
                                end_date=None,
                                _from=None,
                                direct=None,
                                size=None,
                                _async=False):
        """
        查询当前成交、历史成交
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
            params['types'] = ','.join(types)
        if start_date:
            sd = parser.parse(start_date).date()
            params['start-date'] = str(sd)
        if end_date:
            ed = parser.parse(end_date).date()
            params['end-date'] = str(ed)
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/order/matchresults'
        return api_key_get(params, path, _async=_async)

    def req_withdraw(self, address, amount, currency, fee=0, addr_tag="", _async=False):
        """
        申请提现虚拟币
        :param address:
        :param amount:
        :param currency:btc, ltc, bcc, eth, etc ...(火币Pro支持的币种)
        :param fee:
        :param addr_tag:
        :return: {
                  "status": "ok",
                  "data": 700
                }
        """
        params = {
            'address': address,
            'amount': amount,
            'currency': currency,
            'fee': fee,
            'addr-tag': addr_tag
        }
        path = '/v1/dw/withdraw/api/create'

        return api_key_post(params, path, _async=_async)

    def cancel_withdraw(self, address_id, _async=False):
        """
        申请取消提现虚拟币
        :param address_id:
        :return: {
                  "status": "ok",
                  "data": 700
                }
        """
        params = {}
        path = f'/v1/dw/withdraw-virtual/{address_id}/cancel'

        return api_key_post(params, path, _async=_async)

    def get_deposit_withdraw_record(self, currency, _type, _from, size, _async=False):
        """

        :param currency:
        :param _type:
        :param _from:
        :param size:
        :return:
        """
        assert _type in ['deposit', 'withdraw']
        params = {
            'currency': currency,
            'type': _type,
            'from': _from,
            'size': size
        }
        path = '/v1/query/deposit-withdraw'
        return api_key_get(params, path, _async=_async)

    '''
    借贷API
    '''

    def send_margin_order(self, acc_id, amount, symbol, _type, price=0, _async=False):
        """
        创建并执行借贷订单
        :param amount:
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price:
        :return:
        """

        params = {
            'account-id': acc_id,
            'amount': amount,
            'symbol': symbol,
            'type': _type,
            'source': 'margin-api'
        }
        if price:
            params['price'] = price

        path = '/v1/order/orders/place'
        return api_key_post(params, path, _async=_async)

    def exchange_to_margin(self, symbol, currency, amount, _async=False):
        """
        现货账户划入至借贷账户
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol, 'currency': currency, 'amount': amount}

        path = '/v1/dw/transfer-in/margin'
        return api_key_post(params, path, _async=_async)

    def margin_to_exchange(self, symbol, currency, amount, _async=False):
        """
        借贷账户划出至现货账户
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol, 'currency': currency, 'amount': amount}

        path = '/v1/dw/transfer-out/margin'
        return api_key_post(params, path, _async=_async)

    def apply_loan(self, symbol, currency, amount, _async=False):
        """
        申请借贷
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol, 'currency': currency, 'amount': amount}
        path = '/v1/margin/orders'
        return api_key_post(params, path, _async=_async)

    def repay_loan(self, order_id, amount, _async=False):
        """
        归还借贷
        :param order_id:
        :param amount:
        :return:
        """
        params = {'order-id': order_id, 'amount': amount}
        path = f'/v1/margin/orders/{order_id}/repay'
        return api_key_post(params, path, _async=_async)

    def get_loan_orders(self,
                        symbol,
                        states=None,
                        start_date=None,
                        end_date=None,
                        _from=None,
                        direct=None,
                        size=None,
                        _async=False):

        params = {'symbol': symbol}
        if states:
            params['states'] = states
        if start_date:
            sd = parser.parse(start_date).date()
            params['start-date'] = str(sd)
        if end_date:
            ed = parser.parse(end_date).date()
            params['end_date'] = str(ed)
        if _from:
            params['from'] = _from
        if direct and direct in ['prev', 'next']:
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/margin/loan-orders'
        return api_key_get(params, path, _async=_async)

    def get_margin_balance(self, symbol=None, _async=False):
        """
        借贷账户详情,支持查询单个币种
        :param symbol:
        :return:
        """
        params = {}
        path = '/v1/margin/accounts/balance'
        if symbol:
            params['symbol'] = symbol

        return api_key_get(params, path, _async=_async)

    def get_etf_config(self, etf_name, _async=False):
        """
        查询etf的基本信息
        :param etf_name:  etf基金名称
        :param _async:
        :return:
        """
        params = {}
        path = '/etf/swap/config'
        params['etf_name'] = etf_name

        return api_key_get(params, path,  _async=_async)

    def etf_swap_in(self, etf_name, amount, _async=False):
        """
        换入etf
        :param etf_name: etf基金名称
        :param amount:   数量
        :param _async:
        :return:
        """

        params = {}
        path = '/etf/swap/in'
        params['etf_name'] = etf_name
        params['amount'] = amount

        return api_key_post(params, path,  _async=_async)

    def etf_swap_out(self, etf_name, amount, _async=False):
        """
        换出etf
        :param etf_name: etf基金名称
        :param amount:   数量
        :param _async:
        :return:
        """

        params = {}
        path = '/etf/swap/out'
        params['etf_name'] = etf_name
        params['amount'] = amount

        return api_key_post(params, path,  _async=_async)

    def get_etf_records(self, etf_name, offset, limit, _async=False):
        """
        查询etf换入换出明细
        :param etf_name: eth基金名称
        :param offset: 开始位置,0为最新一条
        :param limit:   返回记录条数(0, 100]
        :param _async:
        :return:
        """
        params = {}
        path = '/etf/list'
        params['etf_name'] = etf_name
        params['offset'] = offset
        params['limit'] = limit

        return api_key_get(params, path, _async=_async)

    def get_quotation_kline(self, symbol, period, limit=None, _async=False):
        """
        获取etf净值
        :param symbol: etf名称
        :param period: K线类型
        :param limit: 获取数量
        :param _async:
        :return:
        """
        params = {}
        path = '/quotation/market/history/kline'
        params['symbol'] = symbol
        params['period'] = period
        if limit:
            params['limit'] = limit

        return api_key_get(params, path, _async=_async)

    def transfer(self, sub_uid, currency, amount, transfer_type, _async=False):
        """
        母账户执行子账户划转
        :param sub_uid: 子账户id
        :param currency: 币种
        :param amount: 划转金额
        :param transfer_type: 划转类型，master-transfer-in（子账户划转给母账户虚拟币）/ master-transfer-out （母账户划转给子账户虚拟币）/master-point-transfer-in （子账户划转给母账户点卡）/master-point-transfer-out（母账户划转给子账户点卡）
        :param _async: 是否异步执行
        :return:
        """
        params = {}
        path = '/v1/subuser/transfer'
        params['sub-uid'] = sub_uid
        params['currency'] = currency
        params['amount'] = amount
        params['type'] = transfer_type

        return api_key_post(params, path, _async=_async)

    def get_aggregate_balance(self, _async=False):
        """
        查询所有子账户汇总
        :param _async: 是否异步执行
        :return:
        """
        params = {}
        path = '/v1/subuser/aggregate-balance'
        return  api_key_get(params, path, _async=_async)

    def get_sub_balance(self, sub_id, _async=False):
        """
        查询子账户各币种账户余额
        :param sub_uid: 子账户id
        :param _async:
        :return:
        """

        params = {}
        params['sub-uid'] = sub_id
        path = '/v1/account/accounts/{sub-uid}'
        return api_key_get(params, path, _async=_async)



class HBRestAPI_DEC():
    def __init__(self, addr=None, key=None, get_acc=False):
        """
        火币REST API封装decoration版
        :param addrs: 传入(market_url, trade_url)，若为None，默认是https://api.huobi.br.com
        :param keys: 传入(acess_key, secret_key),可用setKey设置
        :param get_acc: 设置是否初始化获取acc_id,,默认False
        """
        if addr:
            setUrl(*addr)
        if key:
            setKey(*key)
        if get_acc:
            @self.get_accounts()
            def set_acc(msg):
                self.acc_id = msg['data'][0]['id']
            set_acc()

    def set_acc_id(self, acc_id):
        self.acc_id = acc_id

    def get_kline(self, symbol, period, size=150):
        """
        获取K线
        :param symbol
        :param period: 可选值：{1min, 5min, 15min, 30min, 60min, 1day, 1mon, 1week, 1year }
        :param size: 可选值： [1,2000]
        :return:
        """
        params = {'symbol': symbol, 'period': period, 'size': size}
        url = u.MARKET_URL + '/market/history/kline'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(http_get_request(url, params))

            return handle

        return _wrapper

    def get_last_depth(self, symbol, _type):
        """
        获取marketdepth
        :param symbol
        :param type: 可选值：{ percent10, step0, step1, step2, step3, step4, step5 }
        :return:
        """
        params = {'symbol': symbol, 'type': _type}

        url = u.MARKET_URL + '/market/depth'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(http_get_request(url, params))

            return handle

        return _wrapper

    def get_last_ticker(self, symbol):
        """
        获取最新的ticker
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/trade'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(http_get_request(url, params))

            return handle

        return _wrapper

    def get_ticker(self, symbol, size=1):
        """
        获取历史ticker
        :param symbol:
        :param size: 可选[1,2000]
        :return:
        """
        params = {'symbol': symbol, 'size': size}

        url = u.MARKET_URL + '/market/history/trade'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(http_get_request(url, params))

            return handle

        return _wrapper

    def get_all_last_24h_kline(self):
        """
        获取所有ticker
        :param _async:
        :return:
        """
        params = {}
        url = u.MARKET_URL + '/market/tickers'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(http_get_request(url, params))

            return handle

        return _wrapper


    def get_last_1m_kline(self, symbol):
        """
        获取最新一分钟的kline
        :param symbol:
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/detail/merged'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(http_get_request(url, params))

            return handle

        return _wrapper

    def get_last_24h_kline(self, symbol):
        """
        获取 Market Detail 24小时成交量数据
        :param symbol
        :return:
        """
        params = {'symbol': symbol}

        url = u.MARKET_URL + '/market/detail'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(http_get_request(url, params))

            return handle

        return _wrapper

    def get_symbols(self, site='Pro'):
        """
        获取支持的交易对
        :param site:
        :return:
        """
        assert site in ['Pro', 'HADAX']
        params = {}
        path = f'/v1{"/" if site == "Pro" else "/hadax/"}common/symbols'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def get_currencys(self, site='Pro'):
        """

        :return:
        """
        assert site in ['Pro', 'HADAX']
        params = {}
        path = f'/v1{"/" if site == "Pro" else "/hadax/"}common/currencys'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def get_timestamp(self):
        params = {}
        path = '/v1/common/timestamp'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    '''
    Trade/Account API
    '''

    def get_accounts(self):
        """
        :return:
        """
        path = '/v1/account/accounts'
        params = {}

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def get_balance(self, acc_id, site='Pro'):
        """
        获取当前账户资产
        :return:
        """
        assert site in ['Pro', 'HADAX']
        path = f'/v1{"/" if site == "Pro" else "/hadax/"}account/accounts/{acc_id}/balance'
        # params = {'account-id': self.acct_id}
        params = {}

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def send_order(self, acc_id, amount, symbol, _type, price=0, site='Pro'):
        """
        创建并执行订单
        :param amount:
        :param source: 如果使用借贷资产交易，请在下单接口,请求参数source中填写'margin-api'
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖, buy-ioc：IOC买单, sell-ioc：IOC卖单}
        :param price:
        :return:
        """
        assert site in ['Pro', 'HADAX']
        assert _type in u.ORDER_TYPE
        params = {
            'account-id': acc_id,
            'amount': amount,
            'symbol': symbol,
            'type': _type,
            'source': 'api'
        }
        if price:
            params['price'] = price

        path = f'/v1{"/" if site == "Pro" else "/hadax/"}order/orders/place'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def cancel_order(self, order_id):
        """
        撤销订单
        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}/submitcancel'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def batchcancel_order(self, order_ids: list):
        """
        批量撤销订单
        :param order_id:
        :return:
        """
        assert isinstance(order_ids, list)
        params = {'order-ids': order_ids}
        path = f'/v1/order/orders/batchcancel'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def get_order_info(self, order_id):
        """
        查询某个订单
        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def get_order_matchresults(self, order_id):
        """
        查询某个订单的成交明细
        :param order_id:
        :return:
        """
        params = {}
        path = f'/v1/order/orders/{order_id}/matchresults'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def get_orders_info(self,
                        symbol,
                        states,
                        types=None,
                        start_date=None,
                        end_date=None,
                        _from=None,
                        direct=None,
                        size=None):
        """
        查询当前委托、历史委托
        :param symbol:
        :param states: 可选值 {pre-submitted 准备提交, submitted 已提交, partial-filled 部分成交, partial-canceled 部分成交撤销, filled 完全成交, canceled 已撤销}
        :param types: 可选值 买卖类型
        :param start_date:
        :param end_date:
        :param _from:
        :param direct: 可选值{prev 向前，next 向后}
        :param size:
        :return:
        """
        params = {'symbol': symbol, 'states': states}

        if types:
            params['types'] = types
        if start_date:
            sd = parser.parse(start_date).date()
            params['start-date'] = str(sd)
        if end_date:
            ed = parser.parse(end_date).date()
            params['end_date'] = str(ed)
        if _from:
            params['from'] = _from
        if direct:
            assert direct in ['prev', 'next']
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/order/orders'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def get_orders_matchresults(self,
                                symbol,
                                types=None,
                                start_date=None,
                                end_date=None,
                                _from=None,
                                direct=None,
                                size=None):
        """
        查询当前成交、历史成交
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
            params['types'] = types
        if start_date:
            sd = parser.parse(start_date).date()
            params['start-date'] = str(sd)
        if end_date:
            ed = parser.parse(end_date).date()
            params['end_date'] = str(ed)
        if _from:
            params['from'] = _from
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/order/matchresults'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def req_withdraw(self, address, amount, currency, fee=0, addr_tag=""):
        """
        申请提现虚拟币
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
        params = {
            'address': address,
            'amount': amount,
            'currency': currency,
            'fee': fee,
            'addr-tag': addr_tag
        }
        path = '/v1/dw/withdraw/api/create'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def cancel_withdraw(self, address_id):
        """
        申请取消提现虚拟币
        :param address_id:
        :return: {
                  "status": "ok",
                  "data": 700
                }
        """
        params = {}
        path = f'/v1/dw/withdraw-virtual/{address_id}/cancel'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def get_deposit_withdraw_record(self, currency, _type, _from, size):
        """

        :param currency:
        :param _type:
        :param _from:
        :param size:
        :return:
        """
        assert _type in ['deposit', 'withdraw']
        params = {
            'currency': currency,
            'type': _type,
            'from': _from,
            'size': size
        }
        path = '/v1/query/deposit-withdraw'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    '''
    借贷API
    '''

    def send_margin_order(self, acc_id, amount, symbol, _type, price=0):
        """
        创建并执行借贷订单
        :param amount:
        :param symbol:
        :param _type: 可选值 {buy-market：市价买, sell-market：市价卖, buy-limit：限价买, sell-limit：限价卖}
        :param price:
        :return:
        """

        params = {
            'account-id': acc_id,
            'amount': amount,
            'symbol': symbol,
            'type': _type,
            'source': 'margin-api'
        }
        if price:
            params['price'] = price

        path = '/v1/order/orders/place'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def exchange_to_margin(self, symbol, currency, amount):
        """
        现货账户划入至借贷账户
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol, 'currency': currency, 'amount': amount}
        path = '/v1/dw/transfer-in/margin'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def margin_to_exchange(self, symbol, currency, amount):
        """
        借贷账户划出至现货账户
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol, 'currency': currency, 'amount': amount}

        path = '/v1/dw/transfer-out/margin'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def apply_loan(self, symbol, currency, amount):
        """
        申请借贷
        :param amount:
        :param currency:
        :param symbol:
        :return:
        """
        params = {'symbol': symbol, 'currency': currency, 'amount': amount}
        path = '/v1/margin/orders'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def repay_loan(self, order_id, amount):
        """
        归还借贷
        :param order_id:
        :param amount:
        :return:
        """
        params = {'order-id': order_id, 'amount': amount}
        path = f'/v1/margin/orders/{order_id}/repay'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_post(params, path))

            return handle

        return _wrapper

    def get_loan_orders(self,
                        symbol,
                        currency,
                        states=None,
                        start_date=None,
                        end_date=None,
                        _from=None,
                        direct=None,
                        size=None):
        """
        借贷订单
        :param symbol:
        :param currency:
        :param start_date:
        :param end_date:
        :param _from:
        :param direct:
        :param size:
        :return:
        """
        params = {'symbol': symbol, 'currency': currency}
        if states:
            params['states'] = states
        if start_date:
            sd = parser.parse(start_date).date()
            params['start-date'] = str(sd)
        if end_date:
            ed = parser.parse(end_date).date()
            params['end_date'] = str(ed)
        if _from:
            params['from'] = _from
        if direct and direct in ['prev', 'next']:
            params['direct'] = direct
        if size:
            params['size'] = size
        path = '/v1/margin/loan-orders'

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper

    def get_margin_balance(self, symbol):
        """
        借贷账户详情,支持查询单个币种
        :param symbol:
        :return:
        """
        params = {}
        path = '/v1/margin/accounts/balance'
        if symbol:
            params['symbol'] = symbol

        def _wrapper(_func):
            @wraps(_func)
            def handle():
                _func(api_key_get(params, path))

            return handle

        return _wrapper
