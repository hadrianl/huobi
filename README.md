# 火币API的Python版
- websocket封装成`HBWebsocket`类，用`run`开启连接线程
- `HBWebsocket`通过注册`Handler`的方式来处理数据，消息通过pub_msg来分发到个各topic下的Handler线程来处理
- restful api基本参照火币网的demo封装成`HBRestAPI`类
- 目前处于开发阶段，估计含有巨量的**BUG**，慎用！

## Notice
- 该封装的函数命名跟火币本身的请求命名表达不太一致
- 包含open, close, high, low的数据命名是kline或ohlc（其中部分有ask和bid，都纳入这类命名）
- 当且仅当数据只有一条逐笔tick（没有ohlc），命名是ticker
- 深度数据则命名为depth

## Lastest
- restapi修改为单例模式


[![PyPI](https://img.shields.io/pypi/v/huobitrade.svg)](https://pypi.org/project/huobitrade/)
![build](https://travis-ci.org/hadrianl/huobi.svg?branch=master)
![license](https://img.shields.io/github/license/hadrianl/huobi.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/huobitrade.svg)


## Installation
```sh
pip install huobitrade
```

## Usage

### WebSocket API
```python
from huobitrade.service import HBWebsocket

hb = HBWebsocket()  # 可以填入url参数，默认是https://api.huobi.br.com
hb.run()  # 开启websocket进程

# --------------------------------------------
hb.sub_kline('ethbtc', '1min')  # 订阅数据
@hb.register_handle_func('market.ethbtc.kline.1min')  # 注册一个处理函数，最好的处理方法应该是实现一个handler
def handle(msg):
    print('handle:', msg)

hb.unregister_handle_func(handle, 'market.ethbtc.kline.1min')  # 释放处理函数

# --------------------------------------------
# websocket请求数据是异步请求回调，所以先注册一个回调处理函数，再请求
@hb.register_onRsp('market.btcusdt.kline.1min')
def OnRsp_print(msg):
    print(msg)

hb.rep_kline('btcusdt', '1min')
hb.unregister_onRsp('market.btcusdt.kline.1min')  # 注销某topic的请求回调处理

```

### Restful API
- restapi需要先用`setKey`设置密钥
- 默认交易和行情url都是https://api.huobi.br.com （调试用）,实盘要设置url用`from huobitrade import setUrl`
```python
from huobitrade.service import HBRestAPI
from huobitrade import setKey

setKey('your acess_key', 'you secret_key')  # setKey很重要，最好在引入其他模块之前先setKey，部分模块要基于密钥
api = HBRestAPI()  # get_acc参数默认为False,初始化不会取得账户ID，需要ID的函数无法使用
# 可用api.set_acc_id('you_account_id')
print(api.get_timestamp())

# 异步请求
api = HBRestAPI(get_acc=True)
klines = api.get_kline('omgeth', _async=True)
symbols = api.get_symbols(_async=True)
results = api.async_request([klines, symbols])
for r in results:
    print(r)
```

### Restful API-Decoration    （Experimental）
- 用装饰器来初始化回调处理函数
```python
from huobitrade.service import HBRestAPI_DEC
from huobitrade import setKey

setKey('your acess_key', 'you secret_key')
api_dec = HBRestAPI_DEC()
@api_dec.get_kline('ethbtc', '1min')  # 装饰器初始化处理函数
def handle_func(msg):
    print('handle:', msg)

handle_func()  # __call__调用函数会请求并用handle_func做回调处理

```

### Message Handler
- handler是用来处理websocket的原始返回消息的，通过继承basehandler实现handle函数以及注册进HBWebsocket相关的topic来使用
```python
from huobitrade.handler import BaseHandler
fromm huobitrade.util import handler_profiler

class MyHandler(BaseHandler):
    def __init__(self, topic, *args, **kwargs):
        BaseHandler.__init__(self, 'just Thread name', topic)

    @handler_profiler('profiler.csv')  #  可以加上这个装饰器来测试handle函数的执行性能,加参数会输出到单独文件
    def handle(self, topic, msg):  # 实现handle来处理websocket推送的msg
        print(topic, msg)


handler = MyHandler('market.ethbtc.kline.1min')  # topic为str或者list
handler.add_topic('market.ethbtc.kline.5min')  # 为handler增加处理topic(remove_topic来删除)
hb.register_handler(handler)  # 通过register来把handler注册到相应的topic


```
- 内置实现了一个mongodb的`DBHandler`
```python
from huobitrade.handler import DBHandler
handler = DBHandler()  # topic为空的话，会对所有topic的msg做处理
hb.register_handler(handler)
```

### Latest Message Handler
- 基于handler函数根据策略复杂度和性能的的不同造成对message的处理时间不一样，可能造成快生产慢消费的情况，增加lastest参数，每次都是handle最新的message
```python
class MyLatestHandler(BaseHandler):
    def __init__(self, topic, *args, **kwargs):
        BaseHandler.__init__(self, 'just Thread name', topic, latest=True)

    @handler_profiler()  #  可以加上这个装饰器来测试handle函数的执行性能
    def handle(self, topic, msg):  # 实现handle来处理websocket推送的msg
        print(topic, msg)
```

### HBData <h3 id="1.3.6"></h2>
- 使用类似topic的方式来取数据,topic的表达方式与火币有不同
```python
from huobitrade import setKey
from huobitrade.datatype import HBData
setKey('acess_key', 'secret_key')
data = HBMarket()  # 行情接口类
account = HBAccount()  # 交易接口类
margin = HBMargin()  # 借贷接口类

data.omgeth
# <Symbol:omgeth-{'base-currency': 'omg', 'quote-currency': 'eth', 'price-precision': 6, 'amount-precision': 4, 'symbol-partition': 'main'}>
data.omgeth.kline
# <<class 'huobitrade.datatype.HBKline'> for omgeth>
data.omgeth.depth
# <<class 'huobitrade.datatype.HBDepth'> for omgeth>
data.omgeth.ticker
# <<class 'huobitrade.datatype.HBTicker'> for omgeth>
data.omgeth.kline._1min_200  # period前面加'_', 后面加数量最大值为1000
data.omgeth.kline.latest
data.omgeth.kline.last_24_hour
data.omgeth.depth.step0  # step0,1,2,3,4,5
data.omgeth.ticker.latest  # 最新的一条tick
data.omgeth.ticker.last_20  # last_1至last_2000
data.all_24h_ohlc  # 当前所有交易对的ticker
account.Detail  # 所有账户明细
account.Pro_XXXXX_balance  # XXXX为account_id,某账户的结余
account.Pro_XXXXX_balance.update()  # 更新账户结余信息
account.Pro_XXXXX_order  # 某账户的订单类
account.Pro_XXXXX_order['order_id']  # 查询某order明细,或者用get方法
account.Pro_XXXXX_order.send(1, 'omgeth', 'buy-limit', 0.001666)  # 发送订单
account.Pro_XXXXX_trade.get_by_id('order_id')  # 某账户的成交类(即火币的matchresults),也可以直接索引
margin.transferIn('ethusdt', 'eth', 1)
ethusdt_margin_info = margin['ethusdt']  # 或者用getBalance
ethusdt_margin_info.balance  # ethusdt交易对的保证金结余信息

```

### Extra
- 交易策略运营相关的模块，wechat推送，rpc远程订阅调用等
详见[extra](https://github.com/hadrianl/huobi/blob/master/huobitrade/extra/log_handler.md)