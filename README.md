# 火币API的Python版
- websocket封装成`HBWebsocket`类，用`run`开启连接线程
- `HBWebsocket`通过注册`Handler`的方式来处理数据，消息通过pub_msg来分发到个各topic下的Handler线程来处理
- restful api基本参照火币网的demo封装成`HBRestAPI`类
- 没有test和debug，估计含有巨量的<font color=red>BUG</font>，慎用！

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
api = HBRestAPI()
print(api.get_timestamp())
```

### Message Handler
- handler是用来处理websocket的原始返回消息的，通过继承basehandler实现handle函数以及注册进HBWebsocket相关的topic来使用
```python
from huobitrade.handler import baseHandler

class MyHandler(baseHandler):
    def __init__(self, *args, **kwargs):
        baseHandler.__init__(self, name='just Thread name')

    def handle(self, msg):  # 实现handle来处理websocket推送的msg
        print(msg)


handler = MyHandler()
hb.register_handler(handler, 'market.ethbtc.kline.1min')  # 通过register来把handler注册到相应的topic
```
- 内置实现了一个mongodb的`DBHandler`
```python
from huobitrade.handler import DBHandler
handler = DBHandler()
hb.register_handler(handler, 'market.ethbtc.kline.1min')
```