# -*- coding: utf-8 -*-
from peewee import Model, AutoField, IntegerField, CharField, TextField, DateTimeField, ForeignKeyField
from datetime import datetime
from app.database.db import db
from app.models.jimeng_intl_account import JimengIntlAccount
import json


class JimengIntlVideoTask(Model):
    """即梦国际版视频任务模型"""
    id = AutoField(primary_key=True)

    # 提示词
    prompt = TextField()

    # 视频比例: 16:9, 9:16, 1:1 等
    ratio = CharField(max_length=20, default="16:9")

    # 视频模型
    model = CharField(max_length=50, default="pixverse-v4.5")

    # 视频时长: 5s, 8s
    duration = CharField(max_length=10, default="5s")

    # 视频质量: 720p, 1080p
    quality = CharField(max_length=20, default="720p")


    # 任务状态: 0-排队中, 1-生成中, 2-已完成, 3-失败
    status = IntegerField(default=0)

    # 关联账号
    account_id = ForeignKeyField(JimengIntlAccount, null=True, backref='intl_video_tasks')

    # 输入图片（首帧图/末帧图）JSON格式
    input_images = TextField(null=True)

    # 输出视频 JSON格式
    output_videos = TextField(null=True)

    # 错误码和消息
    code = CharField(max_length=50, null=True)
    message = TextField(null=True)

    # 时间戳
    create_at = DateTimeField(default=datetime.now)
    update_at = DateTimeField(default=datetime.now)

    # 软删除标记
    isdel = IntegerField(default=0)

    class Meta:
        database = db
        table_name = "jimeng_intl_video_task"

    def save(self, *args, **kwargs):
        self.update_at = datetime.now()
        return super().save(*args, **kwargs)

    def get_input_images(self):
        """获取输入图片列表"""
        if not self.input_images:
            return []
        try:
            return json.loads(self.input_images)
        except Exception:
            return []

    def set_input_images(self, paths):
        """设置输入图片列表"""
        if paths:
            self.input_images = json.dumps(paths, ensure_ascii=False)
        else:
            self.input_images = None

    def get_output_videos(self):
        """获取输出视频列表"""
        if not self.output_videos:
            return []
        try:
            return json.loads(self.output_videos)
        except Exception:
            return []

    def set_output_videos(self, paths):
        """设置输出视频列表"""
        if paths:
            self.output_videos = json.dumps(paths, ensure_ascii=False)
        else:
            self.output_videos = None

    @classmethod
    def create_task(cls, prompt: str, account_id: int = None, ratio: str = "16:9",
                    model: str = "jimeng-video-3.0", duration: str = "5s",
                    quality: str = "1080p", input_images=None, **kwargs):
        """创建视频任务"""
        if account_id is not None:
            acc = JimengIntlAccount.select().where(
                (JimengIntlAccount.id == account_id) & (JimengIntlAccount.is_deleted == 0)
            ).first()
            if not acc:
                raise ValueError("invalid account_id")

        input_json = None
        if input_images:
            input_json = json.dumps(input_images, ensure_ascii=False)

        return cls.create(
            prompt=prompt,
            account_id=account_id,
            ratio=ratio,
            model=model,
            duration=duration,
            quality=quality,
            status=0,
            input_images=input_json
        )

    @classmethod
    def get_tasks_by_page(cls, page: int = 1, page_size: int = 20):
        """分页获取任务列表"""
        query = cls.select().where(cls.isdel == 0).order_by(cls.create_at.desc())
        total = query.count()
        rows = query.paginate(page, page_size)
        return list(rows), total

    @classmethod
    def get_task_by_id(cls, task_id: int):
        """根据ID获取任务"""
        try:
            inst = cls.get_by_id(task_id)
            if inst.isdel == 1:
                return None
            return inst
        except cls.DoesNotExist:
            return None

    @classmethod
    def mark_deleted(cls, task_id: int) -> bool:
        """软删除任务"""
        try:
            inst = cls.get_by_id(task_id)
            inst.isdel = 1
            inst.update_at = datetime.now()
            inst.save()
            return True
        except cls.DoesNotExist:
            return False
