# EXTRA
- 此目录用于增加一些与交易策略运营相关的模块

## Logging Handler
- 额外的日志handler
### WeChat Handler
- 增加一个微信的日志handler，推送日志消息到设定的群聊中
```python
from huobitrade.extra.logging_handler import WeChatHandler
from huobitrade.utils import logger
wechat_handler = WeChatHandler('chatroom name')  # 默认的level是TRADE_INFO（60）,enableCmdQR用于调整二维码，详见itchat
wechat_handler.run()
logger.addHandler(wechat_handler)
logger.log(TRADE_INFO,'wechat_handler testing!')
@wechat_handler.client.msg_register(TEXT, isGroupChat=True)
def reply(msg):
    if msg['isAt']:
        wechat_handler.send_log(f'HELLO {msg["FromUserName"}')
```

## RPC
- 远程调用
## RPCServer
- 实现了一个订阅端口和请求端口，已封装在RPCServerHandler里面
```python
from huobitrade import logger
logger.setLevel('DEBUG')
from huobitrade import setKey
setKey("", "")
from huobitrade.service import HBWebsocket, HBRestAPI
from huobitrade.handler import RPCServerHandler
import time
ws = HBWebsocket()
api = HBRestAPI(get_acc=True)
ws.run()
time.sleep(1)
ws.sub_tick('omgeth')
rpc = RPCServerHandler()
rpc.register_func('getTime', api.get_timestamp)  # 把函数注册到rpcFunc里面，就可以实现远程调用
ws.register_handler(rpc)
```

##
-
```python
from huobitrade.extra.rpc import RPCClient
from huobitrade import logger
logger.setLevel('DEBUG')
rpcclient = RPCClient('localhost', 'localhost')
rpcclient.subscribe('')  # 订阅topic,如果是''的话，则接受所有topic
rpcclient.startSUB()  # 开启订阅线程，用handle函数来处理，需要继承RPCClient重载handle函数实现
rpcclient.getTime()  # Server端已经注册的函数，可以直接调用

```