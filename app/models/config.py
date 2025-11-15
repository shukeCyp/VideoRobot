# -*- coding: utf-8 -*-
from peewee import Model, CharField
from app.database.db import db


class Config(Model):
    """配置表"""
    key = CharField(unique=True, max_length=255, verbose_name="配置键")
    value = CharField(max_length=1000, verbose_name="配置值")

    class Meta:
        database = db
        table_name = "config"

    @classmethod
    def get_value(cls, key, default=None):
        """获取配置值"""
        try:
            config = cls.get(cls.key == key)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value):
        """设置配置值"""
        config, created = cls.get_or_create(key=key, defaults={"value": value})
        if not created:
            config.value = value
            config.save()
        return config