# -*- coding: utf-8 -*-
from peewee import SqliteDatabase
from app.utils.path_helper import get_database_path

# 数据库文件路径
DB_PATH = get_database_path()

# 创建数据库实例
db = SqliteDatabase(DB_PATH)