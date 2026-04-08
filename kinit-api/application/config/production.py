# -*- coding: utf-8 -*-
# @version        : 1.0
# @Create Time    : 2021/10/19 15:47
# @File           : production.py
# @IDE            : PyCharm
# @desc           : 数据库生产配置文件

import os

"""
Mysql 数据库配置项
数据库链路配置说明：mysql+asyncmy://用户名:密码@地址:端口/数据库名
"""
MYSQL_DRIVER = os.getenv('MYSQL_DRIVER', 'asyncmy')
MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_DB = os.getenv('MYSQL_DB', 'kinit')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
SQLALCHEMY_DATABASE_URL = (
    f"mysql+{MYSQL_DRIVER}://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

"""
Redis 数据库配置
"""
REDIS_DB_ENABLE = str(os.getenv('REDIS_DB_ENABLE', 'false')).lower() == 'true'
REDIS_DB_URL = os.getenv('REDIS_DB_URL', 'redis://:123456@127.0.0.1:6379/1')

"""
MongoDB 数据库配置
"""
MONGO_DB_ENABLE = str(os.getenv('MONGO_DB_ENABLE', 'false')).lower() == 'true'
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'kinit')
MONGO_DB_URL = os.getenv('MONGO_DB_URL', f'mongodb://kinit:123456@127.0.0.1:27017/?authSource={MONGO_DB_NAME}')

ALIYUN_OSS = {
    'accessKeyId': os.getenv('ALIYUN_OSS_ACCESS_KEY_ID', 'accessKeyId'),
    'accessKeySecret': os.getenv('ALIYUN_OSS_ACCESS_KEY_SECRET', 'accessKeySecret'),
    'endpoint': os.getenv('ALIYUN_OSS_ENDPOINT', 'endpoint'),
    'bucket': os.getenv('ALIYUN_OSS_BUCKET', 'bucket'),
    'baseUrl': os.getenv('ALIYUN_OSS_BASE_URL', 'baseUrl')
}

IP_PARSE_ENABLE = str(os.getenv('IP_PARSE_ENABLE', 'false')).lower() == 'true'
IP_PARSE_TOKEN = os.getenv('IP_PARSE_TOKEN', 'IP_PARSE_TOKEN')
