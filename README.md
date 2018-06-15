# 火币API的Python版
- websocket封装成`HBWebsocket`类，用`run`开启连接线程
- `HBWebsocket`通过注册`Handler`的方式来处理数据，消息通过pub_msg来分发到个各topic下的Handler线程来处理
- restful api基本参照火币网的demo封装成`HBRestAPI`类
- 没有test和debug，估计含有巨量的**BUG**，慎用！

## Lastest
- 加入了datatype类，方便数据的请求调用,详看HBData(#1.3.6)


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

```

### Restful API
- restapi需要先用`setKey`设置密钥
- 默认交易和行情url都是https://api.huobi.br.com （调试用）,实盘要设置url用`from huobitrade import setUrl`
```python
from huobitrade.service import HBRestAPI
from huobitrade import setKey

setKey('your acess_key', 'you secret_key')
api = HBRestAPI()  # get_acc参数默认为False,初始化不会取得账户ID，需要ID的函数无法使用
# 可用api.set_acc_id('you_account_id')
print(api.get_timestamp())
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

    @handler_profiler  #  可以加上这个装饰器来测试handle函数的执行性能
    def handle(self, msg):  # 实现handle来处理websocket推送的msg
        print(msg)


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

    @handler_profiler  #  可以加上这个装饰器来测试handle函数的执行性能
    def handle(self, msg):  # 实现handle来处理websocket推送的msg
        print(msg)
```

### HBData <h3 id="1.3.6"></h2>
- 使用类似topic的方式来取数据,topic的表达方式与火币有不同
```python
from huobitrade import setKey
from huobitrade.datatype import HBData
setKey('acess_key', 'secret_key')
data = HBData()

data.omgeth
# <Symbol:omgeth-{'base-currency': 'omg', 'quote-currency': 'eth', 'price-precision': 6, 'amount-precision': 4, 'symbol-partition': 'main'}>
data.omgeth.kline
# <<class 'huobitrade.datatype.HBKline'> for omgeth>
data.omgeth.depth
# <<class 'huobitrade.datatype.HBDepth'> for omgeth>
data.omgeth.ticker
# <<class 'huobitrade.datatype.HBTicker'> for omgeth>
data.omgeth.kline._1min  # period前面加'_'
data.omgeth.kline.latest
data.omgeth.kline.last_24_hour
data.omgeth.depth.step0  # step0,1,2,3,4,5
data.omgeth.ticker.latest
data.omgeth.ticker.last20  # last1至last2000
```