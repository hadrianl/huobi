#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/5/29 0029 14:10
# @Author  : Hadrianl 
# @File    : setup.py
# @Contact   : 137150224@qq.com

from setuptools import setup, find_packages
__version__ = "0.5.4"

with open("README.md", "r", encoding='utf-8') as rm:
    long_description = rm.read()

requires = ['websocket-client>=0.53',
            'requests',
            'pymongo',
            'pyzmq',
            'pandas',
            'requests-futures',
            'ecdsa',
            'click']

hb_packages = ['huobitrade', 'huobitrade/extra']

setup(name='huobitrade',
      version=__version__,
      description='HuoBi Trading Framwork(python)',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Hadrianl',
      author_email='137150224@qq.com',
      url='https://hadrianl.github.io/huobi/',
      packages=hb_packages,
      entry_points={
          "console_scripts": [
              "huobitrade = huobitrade.main:entry_point"
          ]
      },
      classifiers=(
          "Development Status :: 5 - Production/Stable",
          "Natural Language :: Chinese (Simplified)",
          "Operating System :: MacOS",
          "Operating System :: Microsoft :: Windows",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python :: Implementation :: CPython",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "License :: OSI Approved :: MIT License",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: Software Development :: Version Control :: Git"
      ),
      install_requires=requires)