#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/8/7 0007 17:17
# @Author  : Hadrianl 
# @File    : VisualApp
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask, render_template, g, session
from flask_socketio import SocketIO
import json
from huobitrade import HBRestAPI, setKey, HBWebsocket, logger
import json
setKey('', '')

app = Flask(__name__)
socketio = SocketIO(app)
# logger.setLevel('DEBUG')

@app.route('/')
def backtest():
    return render_template('index.html')

@app.route('/data/get_symbols')
def get_symbols():
    api = HBRestAPI()
    symbols = api.get_symbols()['data']
    return json.dumps(symbols)

@socketio.on('connect', namespace='/ws')
def connect():
    api = session.__dict__.setdefault('api', HBRestAPI(get_acc=True))
    ws = session.__dict__.setdefault('ws', HBWebsocket())
    auws = session.__dict__.setdefault('auws', HBWebsocket(auth=True))
    session.api = HBRestAPI(get_acc=True)
    # session.ws = HBWebsocket()
    # session.auws = HBWebsocket(auth=True)
    if not ws._active:
        ws.run()
    if not auws._active:
        @auws.after_auth
        def sub():
            auws.sub_accounts()
            auws.sub_orders()

        @auws.register_handle_func(f'accounts')
        def push_account(msg):
            print(msg)
            accounts = msg['data']
            socketio.emit('accounts', accounts, namespace='/ws')

        @session.auws.register_handle_func(f'orders.*')
        def push_orders(msg):
            orders = msg['data']
            socketio.emit('orders', orders, namespace='/ws')

        auws.run()

@socketio.on('disconnect', namespace='/ws')
def disconnect():
    session.ws.stop()
    session.auws.stop()


@socketio.on('get_klines', namespace='/ws')
def get_klines(msg):
    ret = session.api.get_kline(msg['symbol'], msg['period'], 600)
    klines = ret['data']
    socketio.emit('klines', klines, namespace='/ws')

@socketio.on('sub_kline', namespace='/ws')
def sub_kline(msg):
    session.ws.sub_kline(msg['symbol'], msg['period'])
    @session.ws.register_handle_func(f"market.{msg['symbol']}.kline.{msg['period']}")
    def push_kline(msg):
        kline = msg['tick']
        socketio.emit('kline_tick', kline, namespace='/ws')

@socketio.on('unsub_kline', namespace='/ws')
def unsub_kline(msg):
    session.ws.unsub_kline(msg['symbol'], msg['period'])
    session.ws.unregister_handle_func('push_kline', f"market.{msg['symbol']}.kline.{msg['period']}")

# @socketio.on('sub_accounts', namespace='/ws')
# def sub_accounts():
#     session.auws.sub_accounts()
#     session.auws.after_auth(session.auws.sub_accounts)
#     @session.auws.register_handle_func(f'accounts')
#     def push_account(msg):
#         print(msg)
#         accounts = msg['data']
#         socketio.emit('accounts', accounts, namespace='/ws')

# @socketio.on('sub_orders', namespace='/ws')
# def sub_orders(symbol):
#     session.auws.sub_orders(symbol)
#     @session.auws.register_handle_func(f'orders')
#     def push_orders(msg):
#         orders = msg['data']
#         socketio.emit('orders', orders, namespace='/ws')



if __name__ == '__main__':
    import sys
    socketio.run(app, debug=False, port=8989)
