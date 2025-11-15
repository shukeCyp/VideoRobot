from peewee import Model, AutoField, IntegerField, CharField, TextField, DateTimeField, ForeignKeyField
from datetime import datetime
from app.database.db import db
from app.models.jimeng_intl_account import JimengIntlAccount
import json


class JimengIntlImageTask(Model):
    id = AutoField(primary_key=True)

    prompt = TextField()
    model = CharField(max_length=100, default="Image 3.1")
    ratio = CharField(max_length=20, default="1:1")
    quality = CharField(max_length=20, default="1K")

    status = IntegerField(default=0)

    account_id = ForeignKeyField(JimengIntlAccount, null=True, backref='intl_image_tasks')

    input_images = TextField(null=True)
    output_images = TextField(null=True)

    task_id = CharField(max_length=100, null=True)

    code = CharField(max_length=50, null=True)
    message = TextField(null=True)

    create_at = DateTimeField(default=datetime.now)
    update_at = DateTimeField(default=datetime.now)

    isdel = IntegerField(default=0)

    class Meta:
        database = db
        table_name = "jimeng_intl_image_task"

    def save(self, *args, **kwargs):
        self.update_at = datetime.now()
        return super().save(*args, **kwargs)

    def get_input_images(self):
        if not self.input_images:
            return []
        try:
            return json.loads(self.input_images)
        except Exception:
            return []

    def set_input_images(self, paths):
        if paths:
            self.input_images = json.dumps(paths, ensure_ascii=False)
        else:
            self.input_images = None

    def get_output_images(self):
        if not self.output_images:
            return []
        try:
            return json.loads(self.output_images)
        except Exception:
            return []

    def set_output_images(self, paths):
        if paths:
            self.output_images = json.dumps(paths, ensure_ascii=False)
        else:
            self.output_images = None

    @classmethod
    def create_task(cls, prompt: str, account_id: int = None, model: str = "Image 3.1",
                    ratio: str = "1:1", quality: str = "1K", input_images=None):
        if account_id is not None:
            acc = JimengIntlAccount.select().where((JimengIntlAccount.id == account_id) & (JimengIntlAccount.isdel == 0)).first()
            if not acc:
                raise ValueError("invalid account_id")
        input_json = None
        if input_images:
            input_json = json.dumps(input_images, ensure_ascii=False)
        return cls.create(
            prompt=prompt,
            account_id=account_id,
            model=model,
            ratio=ratio,
            quality=quality,
            status=0,
            input_images=input_json
        )

    @classmethod
    def get_tasks_by_page(cls, page: int = 1, page_size: int = 20):
        query = cls.select().where(cls.isdel == 0).order_by(cls.create_at.desc())
        total = query.count()
        rows = query.paginate(page, page_size)
        return list(rows), total

    @classmethod
    def get_task_by_id(cls, task_id: int):
        try:
            inst = cls.get_by_id(task_id)
            if inst.isdel == 1:
                return None
            return inst
        except cls.DoesNotExist:
            return None

    @classmethod
    def mark_deleted(cls, task_id: int) -> bool:
        try:
            inst = cls.get_by_id(task_id)
            inst.isdel = 1
            inst.update_at = datetime.now()
            inst.save()
            return True
        except cls.DoesNotExist:
            return False
