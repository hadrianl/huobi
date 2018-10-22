#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/10/22 0022 13:18
# @Author  : Hadrianl 
# @File    : main.py
# @Contact   : 137150224@qq.com

import click
import os
import importlib
from huobitrade import setKey, setUrl, logger
from urllib.parse import urlparse
from huobitrade.handler import TimeHandler
import time
import traceback

@click.group()
def cli():
    ...


@click.command()
@click.option('-f', '--file', default=None, type=click.Path(exists=True), help='策略文件')
@click.option('-a', '--access-key', help='访问密钥')
@click.option('-s', '--secret-key', help='私密密钥')
@click.option('--url', help='火币服务器url，默认为api.huobi.br.com')
@click.option('--reconn', type=click.INT, help='重连次数，默认为-1，即无限重连')
def run(file, access_key, secret_key, **kwargs):
    if file:
        strategy_module = importlib.import_module(os.path.splitext(file)[0])
        init = getattr(strategy_module, 'init', None)
        handle_func = getattr(strategy_module, 'handle_func', None)
        scedule = getattr(strategy_module, 'scedule', None)

    setKey(access_key, secret_key)
    url = kwargs.get('url')
    hostname = 'api.huobi.br.com'
    if url:
        hostname = urlparse(url).hostname
        setUrl('https://' + hostname, 'https://' + hostname)

    reconn = kwargs.get('reconn', -1)
    from huobitrade import HBWebsocket, HBRestAPI
    from huobitrade.datatype import HBMarket, HBAccount, HBMargin
    restapi = HBRestAPI(get_acc=True)
    ws = HBWebsocket(host=hostname, reconn=reconn)
    auth_ws = HBWebsocket(host=hostname, auth=True, reconn=reconn)
    data = HBMarket()
    account = HBAccount()
    margin = HBMargin()
    ws_open = False
    ws_auth = False
    @ws.after_open
    def _open():
        nonlocal ws_open
        click.echo('行情接口连接成功')
        ws_open = True

    @auth_ws.after_auth
    def _auth():
        nonlocal ws_auth
        click.echo('鉴权接口鉴权成功')
        ws_auth = True

    ws.run()
    auth_ws.run()

    for i in range(10):
        time.sleep(3)
        click.echo(f'连接：第{i+1}次连接')
        if ws_open&ws_auth:
            break
    else:
        ws.stop()
        auth_ws.stop()
        raise Exception('连接失败')
    if init:
        init(restapi, ws, auth_ws)

    if handle_func:
        for k, v in handle_func.items():
            if k.split('.')[0].lower() == 'market':
                ws.register_handle_func(k)(v)
            else:
                auth_ws.register_handle_func(k)(v)

    while True:
        try:
            code = click.prompt('huobitrade>>')
            if code == 'exit':
                if click.confirm('是否要退出huobitrade'):
                    break
                else:
                    continue
            else:
                result = eval(code)
                click.echo(result)
        except Exception as e:
            click.echo(traceback.format_exc())

    ws.stop()
    auth_ws.stop()

def entry_point():
    cli.add_command(run)
    cli()
