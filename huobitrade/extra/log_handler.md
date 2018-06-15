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