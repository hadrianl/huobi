# 火币API的Python版
- websocket封装成HBWebsocket类，用`run`开启连接线程
- restful api基本参照火币网的demo封装HBRestAPI
- 没有test和debug，估计含有巨量的BUG，慎用！

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