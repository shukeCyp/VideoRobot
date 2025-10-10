# -*- coding: utf-8 -*-
from peewee import Model, AutoField, CharField, IntegerField, DateTimeField, TextField
from datetime import datetime
from app.database.db import db


class JimengAccount(Model):
    """即梦账号表"""
    id = AutoField(primary_key=True, verbose_name="账号ID")
    avatar = CharField(max_length=500, null=True, verbose_name="头像URL")
    nickname = CharField(max_length=100, verbose_name="昵称")
    points = IntegerField(default=0, verbose_name="积分")
    vip_type = CharField(max_length=50, default="普通会员", verbose_name="会员类型")
    vip_expire_time = DateTimeField(null=True, verbose_name="会员到期时间")
    cookies = TextField(verbose_name="Cookies")
    created_at = DateTimeField(default=datetime.now, verbose_name="创建时间")
    updated_at = DateTimeField(default=datetime.now, verbose_name="更新时间")

    class Meta:
        database = db
        table_name = "jimeng_account"

    def save(self, *args, **kwargs):
        """重写保存方法，自动更新updated_at"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    @classmethod
    def get_all_accounts(cls):
        """获取所有账号"""
        return cls.select().order_by(cls.created_at.desc())

    @classmethod
    def get_account_by_id(cls, account_id):
        """根据ID获取账号"""
        try:
            return cls.get_by_id(account_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def delete_account(cls, account_id):
        """删除账号"""
        try:
            account = cls.get_by_id(account_id)
            account.delete_instance()
            return True
        except cls.DoesNotExist:
            return False