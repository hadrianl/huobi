# [火币API的Python版](https://hadrianl.github.io/huobi/)
- websocket封装成`HBWebsocket`类，用`run`开启连接线程
- `HBWebsocket`通过注册`Handler`的方式来处理数据，消息通过`pub_msg`来分发到个各`topic`下的`Handler`线程来处理
- 火币的鉴权WS是与普通WS独立的，所以同时使用需要开启两个WS
- restful api基本参照火币网的demo封装成`HBRestAPI`类
- 兼容win，mac，linux，python版本必须3.6或以上，因为使用了大量的f***
- 目前已经稳定使用，后续会基于框架提供如行情持久化，交易数据持久化等`handler`
- 暂时先不维护`Restful API-Decoration`版，所以火币API8月份之后的修改将会导致其失效，有需求的小伙伴可以issues一波，再考虑去维护吧！
- 有疑问或者需要支持和交流的小伙伴可以联系我， QQ：[137150224](http://wpa.qq.com/msgrd?v=3&uin=137150224&site=qq&menu=yes)
- 鉴于小伙伴数量也越来越多，所以建个小群：859745469 ， 方便大家交流

![QQ Group](/QRCode.png)

## Notice
- 该封装的函数命名跟火币本身的请求命名表达不太一致
- 包含open, close, high, low的数据命名是kline（其中部分有ask和bid，都纳入这类命名）
- 当且仅当数据只有一条逐笔tick（没有ohlc），命名是ticker
- 深度数据则命名为depth

## Lastest
- 暂未进行测试
- 更改HBAccount的某些调用方法，主要是由于hadax没有之后，不在需要区分pro和hadax了
- 加入合约的restful请求和websocket订阅
- 删除实验性的HBRestAPI_DEC装饰器类
- 新增huobitrade命令行工具，通过`huobitrade run`运行，详看[huobitrade CLI Tool](#21-huobitrade-cli-tool)

[![PyPI](https://img.shields.io/pypi/v/huobitrade.svg)](https://pypi.org/project/huobitrade/)
[![GitHub forks](https://img.shields.io/github/forks/hadrianl/huobi.svg)](https://github.com/hadrianl/huobi/network)
[![GitHub stars](https://img.shields.io/github/stars/hadrianl/huobi.svg)](https://github.com/hadrianl/huobi/stargazers)
![build](https://travis-ci.org/hadrianl/huobi.svg?branch=master)
![license](https://img.shields.io/github/license/hadrianl/huobi.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/huobitrade.svg)

- [HuoBi Trading](#火币api的python版)
    - [1. Installation](#1-installation)
    - [2. Usage](#2-usage)
        - [2.1 huobitrade CLI Tool](#21-huobitrade-cli-tool)
        - [2.2.1 WebSocket API](#221-websocket-api)
        - [2.2.2 Auth WebSocket API](#222-auth-websocket-api)
        - [2.3 Restful API](#23-restful-api)
        - [2.4 Message Handler](#25-message-handler)
        - [2.5 Latest Message Handler](#26-latest-message-handler)
        - [2.6 HBData](#27-hbdata)
    - [3. Extra](#3-extra)


## 1. Installation
```sh
pip install huobitrade
```

## 2. Usage
- 实现长连订阅策略最核心的部分是实现handler里面的handle函数
    1. 通过`HBWebsocket`实例的`sub`开头的函数订阅需要的topic
    2. 通过继承`BaseHandler`的实例的初始化或者`add_topic`来增加对相关topic，实现`handl`e函数来处理相关topic的消息
    3. 通过`HBWebsocket`实例的`register_handler`来注册`handler`
    4. `handler`初始化中有个`latest`，建议使用depth或者ticker数据来做处理，且策略性能不高的时候使用它
- 基于websocket的接口都是用异步回调的方式来处理
    1. 首先需要用`HBWebsocket`的装饰器`register_onRsp`来绑定实现一个处理相关的topic消息的函数
    2. 再用`req`开头的函数来请求相关topic数据，回调的数据将会交给回调函数处理
- 交易相关的都是用的restful api（因为火币还没推出websocket的交易接口）
    1. `setKey`是必要的，如果需要用到交易相关请求的话，只是请求行情的话可以不设。
    2. `HBRestAPI`是单例类，所以多次初始化也木有啥大问题，如在handler里面初始化
    3. 每个请求都有一个`_async`参数来提供异步请求，建议尽量使用它，具体用法是先初始化数个请求到一个list，再用`async_request`一次性向服务器发起请求
    4. 子账户体系因为刚出，没用过，可能会有问题，有bug欢迎pr
- 另外还提供了几个简单易用的封装类
    1. `HBMarket`, `HBAccount`, `HBMargin`分别是行情，账户和借贷账户类，里面提供了大部分属性调用请求，均基于`HBRestAPI`
    2. 一般情景下应该是可以替代HBRestAPI的使用的
- 最后还提供了数个运营管理的工具
    1. 微信推送handler，可以实现一些交易信息推送之类的，但是建议朋友们慎用，因为鄙人有试过一天推送几千条信息被封禁了半个月微信web端登陆的经历
    2. `rpc`模块，具体用法就不细说了，懂的应该都懂的，看下源码就知道咋用啦
- 最后的最后，其实基于这个项目，还有附带的另外一个可视化web的项目没有放出来
    1. 基于`flask`写的一个用于查询当日成交明细和成交分布图，很丑很简陋
    2. 有兴趣的小伙伴可以联系我

### 2.1 huobitrade CLI Tool
- `huobitrade run -f strategy.py -a access-key -s secret-key`用于启用一个基本简单的策略，其中strategy里应该可以包含一个init和handle_func用于初始化或处理相关topic.连接和鉴权成功后，会进入交互环境，提供6个命名空间来进行交互，包括`restapi` `ws` `auth_ws` `account` `data` `margin`,分别都是huobitrade几个主要类的实例huobi
- `huobitrade test_conn`用于测试是否可以正常连接， `huobitrade doc`打开huobitrade文档
- `huobitrade --help`通过该命令获取帮助


### 2.2.1 WebSocket API
```python
from huobitrade.service import HBWebsocket

hb = HBWebsocket()  # 可以填入url参数，默认是api.huobi.br.com
@hb.after_open  # 使用装饰器注册函数，当ws连接之后会调用函数，可以实现订阅之类的
def sub_depth():
    hb.sub_depth('ethbtc')

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

hb.req_kline('btcusdt', '1min')
hb.unregister_onRsp('market.btcusdt.kline.1min')  # 注销某topic的请求回调处理

```

### 2.2.2 Auth WebSocket API
```python
from huobitrade import setKey
from huobitrade.service import HBWebsocket
setKey('your acess_key', 'you secret_key')
hb = HBWebsocket(auth=True)  # 可以填入url参数，默认是api.huobi.br.com
@hb.after_auth  # 会再鉴权成功通过之后自动调用
def sub_accounts():
    hb.sub_accounts()

hb.run()  # 开启websocket进程

@hb.register_handle_func('accounts')  # 注册一个处理函数，最好的处理方法应该是实现一个handler
def auth_handle(msg):
    print('auth_handle:', msg)

```


### 2.3 Restful API
- restapi需要先用`setKey`设置密钥
- 默认交易和行情url都是https://api.huobi.br.com （调试用）,实盘要用`from huobitrade import setUrl`设置url

```python
from huobitrade.service import HBRestAPI
from huobitrade import setKey
# setUrl('', '')
setKey('your acess_key', 'you secret_key')  # setKey很重要，最好在引入其他模块之前先setKey，鉴权ws和restapi的部分函数是基于密钥
api = HBRestAPI(get_acc=True)  # get_acc参数默认为False,初始化不会取得账户ID，需要ID的函数无法使用.也可用api.set_acc_id('you_account_id')
print(api.get_timestamp())

api = HBRestAPI(get_acc=True) # 异步请求
klines = api.get_kline('omgeth', '1min', _async=True)
symbols = api.get_symbols(_async=True)
results = api.async_request([klines, symbols])
for r in results:
    print(r)
```

### 2.4 Message Handler
- handler是用来处理websocket的原始返回消息的，通过继承basehandler实现handle函数以及注册进HBWebsocket相关的topic来使用

```python
from huobitrade.handler import BaseHandler
from huobitrade.utils import handler_profiler
from huobitrade import setKey
from huobitrade.service import HBWebsocket
setKey('your acess_key', 'you secret_key')
hb = HBWebsocket(auth=True)  # 可以填入url参数，默认是api.huobi.br.com

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
from huobitrade import setKey
from huobitrade.service import HBWebsocket
setKey('your acess_key', 'you secret_key')
hb = HBWebsocket(auth=True)  # 可以填入url参数，默认是api.huobi.br.com
handler = DBHandler()  # topic为空的话，会对所有topic的msg做处理
hb.register_handler(handler)
```

### 2.5 Latest Message Handler
- 基于handler函数根据策略复杂度和性能的的不同造成对message的处理时间不一样，可能造成快生产慢消费的情况，增加lastest参数，每次都是handle最新的message
```python
from huobitrade.handler import BaseHandler
from huobitrade.utils import handler_profiler
class MyLatestHandler(BaseHandler):
    def __init__(self, topic, *args, **kwargs):
        BaseHandler.__init__(self, 'just Thread name', topic, latest=True)

    @handler_profiler()  #  可以加上这个装饰器来测试handle函数的执行性能
    def handle(self, topic, msg):  # 实现handle来处理websocket推送的msg
        print(topic, msg)
```

### 2.6 HBData
- 使用类似topic的方式来取数据,topic的表达方式与火币有不同

```python
from huobitrade import setKey
setKey('acess_key', 'secret_key')
from huobitrade.datatype import HBMarket, HBAccount, HBMargin

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
data.omgeth.kline._1min_200  # period前面加'_', 后面加数量最大值为2000
data.omgeth.kline.last
data.omgeth.kline.last_24_hour
data.omgeth.depth.step0  # step0,1,2,3,4,5
data.omgeth.ticker.last  # 最新的一条tick
data.omgeth.ticker.last_20  # last_1至last_2000
data.all_24h_kline  # 当前所有交易对的ticker
account.Detail  # 所有账户明细
account.balance_XXXX  # XXXX为account_id,某账户的结余, 引用结余信息会自动更新
account.order_XXXX  # 某账户的订单类
account.order_XXXX['order_id']  # 查询某order明细,或者用get方法
account.order_XXXX.send(1, 'omgeth', 'buy-limit', 0.001666)  # 发送订单
account.trade_XXXX.get_by_id('order_id')  # 某账户的成交类(即火币的matchresults),也可以直接索引
margin.transferIn('ethusdt', 'eth', 1)
ethusdt_margin_info = margin['ethusdt']  # 或者用getBalance
ethusdt_margin_info.balance  # ethusdt交易对的保证金结余信息

```

## 3. Extra
- 交易策略运营相关的模块，`wechat推送`，`rpc远程订阅调用`等
详见[extra](https://github.com/hadrianl/huobi/blob/master/huobitrade/extra/log_handler.md)