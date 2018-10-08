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
from huobitrade import HBRestAPI, setKey, HBWebsocket
import json
setKey('', '')

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def backtest():
    return render_template('index.html')

@socketio.on('connect', namespace='/ws')
def init_echarts():
    session.api = HBRestAPI(get_acc=True)
    session.ws = HBWebsocket()
    session.auws = HBWebsocket(auth=True)


@socketio.on('get_klines', namespace='/ws')
def get_klines(msg):
    klines = session.api.get_kline(msg['symbol'], msg['period'])
    print(klines)
    socketio.emit('klines', klines, namespace='/ws')

@socketio.on('sub_kline', namespace='/ws')
def sub_kline(symbol, period):
    session.ws.sub_kline(symbol, period)
    @g.ws.register_handle_func(f'market.{symbol}.kline.{period}')
    def push_kline(msg):
        kline = msg['tick']
        socketio.emit('kline_tick', kline, namespace='/ws')

@socketio.on('sub_account', namespace='/ws')
def sub_account():
    session.auws.sub_accounts()
    @g.auws.register_handle_func(f'accounts')
    def push_account(msg):
        account = msg['data']
        socketio.emit('account', account, namespace='/ws')

@socketio.on('sub_orders', namespace='/ws')
def sub_orders(symbol):
    session.auws.sub_orders(symbol)
    @g.auws.register_handle_func(f'orders')
    def push_orders(msg):
        orders = msg['data']
        socketio.emit('orders', orders, namespace='/ws')



if __name__ == '__main__':
    import sys
    socketio.run(app, debug=True, port=8989)
