# -*- coding: utf-8 -*-
from peewee import Model, AutoField, CharField, DateTimeField, IntegerField
from datetime import datetime
from app.database.db import db


class JimengIntlAccount(Model):
    """即梦国际版账号表"""
    id = AutoField(primary_key=True, verbose_name="账号ID")
    session_id = CharField(max_length=255, verbose_name="Session ID")
    points = IntegerField(default=0, verbose_name="积分数量")
    account_type = IntegerField(default=0, verbose_name="账号类型(0无积分账号 1有积分账号)")
    is_deleted = IntegerField(default=0, verbose_name="是否删除(0未删除 1已删除)")
    disabled_at = DateTimeField(null=True, verbose_name="禁用日期")
    created_at = DateTimeField(default=datetime.now, verbose_name="创建时间")

    class Meta:
        database = db
        table_name = "jimeng_intl_account"

    def save(self, *args, **kwargs):
        """重写保存方法"""
        return super().save(*args, **kwargs)

    @classmethod
    def get_all_accounts(cls):
        """获取所有未删除的账号"""
        return cls.select().where(cls.is_deleted == 0).order_by(cls.created_at.desc())

    @classmethod
    def get_account_by_id(cls, account_id):
        """根据ID获取账号"""
        try:
            return cls.get_by_id(account_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def delete_account(cls, account_id) -> bool:
        """删除账号（软删除）"""
        try:
            account = cls.get_by_id(account_id)
            account.is_deleted = 1
            account.disabled_at = datetime.now()
            account.save()
            return True
        except cls.DoesNotExist:
            return False

    @classmethod
    def create_account(cls, session_id: str):
        """创建新账号"""
        return cls.create(session_id=session_id)

    @classmethod
    def get_accounts_by_page(cls, page: int = 1, page_size: int = 20):
        """分页获取账号"""
        query = cls.select().where(cls.is_deleted == 0).order_by(cls.created_at.desc())
        total = query.count()
        rows = query.paginate(page, page_size)
        return list(rows), total

    @classmethod
    def get_available_account(cls):
        """
        获取一个可用的账号（排除今天禁用的和已删除的）

        Returns:
            JimengIntlAccount: 可用的账号，如果没有返回None
        """
        today = datetime.now().date()

        # 优先选择有积分的账号，排除今天禁用的
        account = cls.select().where(
            (cls.account_type == 1) &
            (cls.is_deleted == 0) &
            ((cls.disabled_at.is_null()) | (cls.disabled_at < today))
        ).order_by(cls.points.desc()).first()

        if account:
            return account

        # 如果没有积分账号，选择任意可用账号
        account = cls.select().where(
            (cls.is_deleted == 0) &
            ((cls.disabled_at.is_null()) | (cls.disabled_at < today))
        ).order_by(cls.created_at.asc()).first()

        return account

    @classmethod
    def disable_account_today(cls, account_id: int) -> bool:
        """
        禁用账号（设置禁用日期为今天）

        Args:
            account_id: 账号ID

        Returns:
            bool: 是否成功
        """
        try:
            account = cls.get_by_id(account_id)
            account.disabled_at = datetime.now()
            account.save()
            return True
        except cls.DoesNotExist:
            return False
