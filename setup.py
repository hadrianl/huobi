#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/29 0029 14:10
# @Author  : Hadrianl 
# @File    : setup.py
# @Contact   : 137150224@qq.com

from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as rm:
    long_description = rm.read()

requires = ['websocket-client',
            'requests',
            'pymongo']

setup(name='huobitrade',
      version='0.1.7',
      description='huobi_api for python',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Hadrianl',
      autor_email='137150224@qq.com',
      url='https://github.com/hadrianl/huobi',
      packages=find_packages(),
      classifiers=("Programming Language :: Python :: 3.6",
                   "License :: OSI Approved :: MIT License"),
      install_requires=requires)