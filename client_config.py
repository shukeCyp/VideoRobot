# -*- coding: utf-8 -*-
"""
PyUpdater 客户端配置
"""
from client_config import ClientConfig

class ClientConfig(object):
    PUBLIC_KEY = 'PLACE_YOUR_PUBLIC_KEY_HERE'
    APP_NAME = '视频机器人'
    COMPANY_NAME = 'ShukeAI'
    HTTP_TIMEOUT = 30
    MAX_DOWNLOAD_RETRIES = 3
    UPDATE_URLS = ['https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/']
