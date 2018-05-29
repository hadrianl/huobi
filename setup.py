#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/29 0029 14:10
# @Author  : Hadrianl 
# @File    : setup.py
# @Contact   : 137150224@qq.com

from setuptools import setup, find_packages

requires = ['websocket-client',
            'requests',
            'pymongo']

setup(name='huobi_trade',
      version='0.1.0',
      description='huobi_api for python',
      author='Hadrianl',
      autor_email='137150224@qq.com',
      url='https://github.com/hadrianl/huobi',
      packages=find_packages(),
      install_requires=requires)