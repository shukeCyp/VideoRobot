from peewee import Model, AutoField, CharField, TextField, DateTimeField, IntegerField
from datetime import datetime
from app.database.db import db


class JimengIntlAccount(Model):
    id = AutoField(primary_key=True)
    account = CharField(max_length=100)
    password = CharField(max_length=200)
    cookies = TextField(null=True)
    createdate = DateTimeField(default=datetime.now)
    updatedate = DateTimeField(default=datetime.now)
    isdel = IntegerField(default=0)

    class Meta:
        database = db
        table_name = "jimeng_intl_account"

    def save(self, *args, **kwargs):
        self.updatedate = datetime.now()
        return super().save(*args, **kwargs)

    @classmethod
    def create_account(cls, account: str, password: str, cookies: str = None):
        existing = cls.select().where((cls.account == account) & (cls.isdel == 0)).first()
        if existing:
            raise ValueError("account already exists")
        return cls.create(account=account, password=password, cookies=cookies)

    @classmethod
    def get_all_accounts(cls):
        return cls.select().where(cls.isdel == 0).order_by(cls.createdate.desc())

    @classmethod
    def get_by_id(cls, account_id: int):
        try:
            return cls.get_by_id(account_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def delete_account(cls, account_id: int) -> bool:
        try:
            inst = cls.get_by_id(account_id)
            inst.isdel = 1
            inst.updatedate = datetime.now()
            inst.save()
            return True
        except cls.DoesNotExist:
            return False

    @classmethod
    def get_accounts_by_page(cls, page: int = 1, page_size: int = 20):
        query = cls.select().where(cls.isdel == 0).order_by(cls.createdate.desc())
        total = query.count()
        rows = query.paginate(page, page_size)
        return list(rows), total

    @classmethod
    def delete_all(cls) -> int:
        return cls.update(isdel=1, updatedate=datetime.now()).execute()
