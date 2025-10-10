# -*- coding: utf-8 -*-
from peewee import *
from datetime import datetime
import json
from app.database.db import db


class JimengImageTask(Model):
    """即梦图片生成任务表"""

    id = AutoField(primary_key=True)
    account_id = IntegerField(null=True, help_text="关联的即梦账号ID")

    # 输入参数
    prompt = TextField(help_text="提示词")
    input_image_path = TextField(null=True, help_text="输入图片路径（JSON数组）")
    image_model = CharField(max_length=100, default="", help_text="图片模型")
    aspect_ratio = CharField(max_length=50, default="1:1", help_text="分辨率比例，如 1:1, 16:9, 9:16")
    resolution = CharField(max_length=50, default="高清 2K", help_text="分辨率，高清 2K、超清 4K")

    # 任务状态
    status = CharField(max_length=50, default="pending", help_text="任务状态：pending-等待中, processing-处理中, success-成功, failed-失败")
    task_id = CharField(max_length=200, null=True, help_text="即梦平台返回的任务ID")
    error_message = TextField(default="", help_text="失败原因")

    # 输出结果 - 四张图片路径
    output_image_1 = CharField(max_length=500, null=True, help_text="输出图片1路径")
    output_image_2 = CharField(max_length=500, null=True, help_text="输出图片2路径")
    output_image_3 = CharField(max_length=500, null=True, help_text="输出图片3路径")
    output_image_4 = CharField(max_length=500, null=True, help_text="输出图片4路径")

    # 时间戳
    created_at = DateTimeField(default=datetime.now, help_text="创建时间")
    updated_at = DateTimeField(default=datetime.now, help_text="更新时间")

    class Meta:
        database = db
        table_name = 'jimeng_image_tasks'

    def save(self, *args, **kwargs):
        """保存时自动更新时间"""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    def get_input_image_paths(self):
        """获取输入图片路径列表"""
        if not self.input_image_path:
            return []
        try:
            return json.loads(self.input_image_path)
        except:
            return []

    def set_input_image_paths(self, paths):
        """设置输入图片路径列表"""
        if paths:
            self.input_image_path = json.dumps(paths, ensure_ascii=False)
        else:
            self.input_image_path = None

    @classmethod
    def create_task(cls, prompt, account_id=None, input_image_paths=None,
                    image_model="", aspect_ratio="1:1", resolution="1024x1024"):
        """
        创建新任务

        Args:
            prompt: 提示词
            account_id: 账号ID
            input_image_paths: 输入图片路径列表
            image_model: 图片模型
            aspect_ratio: 分辨率比例
            resolution: 分辨率

        Returns:
            JimengImageTask对象
        """
        # 将图片路径列表转换为JSON
        input_image_json = None
        if input_image_paths:
            input_image_json = json.dumps(input_image_paths, ensure_ascii=False)

        task = cls.create(
            prompt=prompt,
            account_id=account_id,
            input_image_path=input_image_json,
            image_model=image_model,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            status="pending"
        )
        return task

    @classmethod
    def get_tasks_by_page(cls, page=1, page_size=20, status=None):
        """
        分页获取任务列表

        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            status: 状态筛选（可选）

        Returns:
            (tasks列表, 总数)
        """
        query = cls.select().order_by(cls.created_at.desc())

        if status:
            query = query.where(cls.status == status)

        total = query.count()
        tasks = query.paginate(page, page_size)

        return list(tasks), total

    @classmethod
    def get_task_by_id(cls, task_id):
        """
        根据ID获取任务

        Args:
            task_id: 任务ID

        Returns:
            JimengImageTask对象或None
        """
        try:
            return cls.get_by_id(task_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def update_task_status(cls, task_id, status, error_message=""):
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（可选）

        Returns:
            bool
        """
        try:
            task = cls.get_by_id(task_id)
            task.status = status
            if error_message:
                task.error_message = error_message
            task.save()
            return True
        except cls.DoesNotExist:
            return False

    @classmethod
    def update_task_outputs(cls, task_id, output_paths):
        """
        更新任务输出图片路径

        Args:
            task_id: 任务ID
            output_paths: 图片路径列表（最多4张）

        Returns:
            bool
        """
        try:
            task = cls.get_by_id(task_id)

            if len(output_paths) > 0:
                task.output_image_1 = output_paths[0]
            if len(output_paths) > 1:
                task.output_image_2 = output_paths[1]
            if len(output_paths) > 2:
                task.output_image_3 = output_paths[2]
            if len(output_paths) > 3:
                task.output_image_4 = output_paths[3]

            task.status = "success"
            task.save()
            return True
        except cls.DoesNotExist:
            return False

    @classmethod
    def delete_task(cls, task_id):
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool
        """
        try:
            task = cls.get_by_id(task_id)
            task.delete_instance()
            return True
        except cls.DoesNotExist:
            return False

    def get_output_images(self):
        """
        获取所有输出图片路径列表

        Returns:
            图片路径列表
        """
        paths = []
        if self.output_image_1:
            paths.append(self.output_image_1)
        if self.output_image_2:
            paths.append(self.output_image_2)
        if self.output_image_3:
            paths.append(self.output_image_3)
        if self.output_image_4:
            paths.append(self.output_image_4)
        return paths

    def __str__(self):
        return f"JimengImageTask(id={self.id}, prompt={self.prompt[:30]}..., status={self.status})"
