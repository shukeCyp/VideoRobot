# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from app.utils.logger import log


class BaseTaskExecutor(ABC):
    """任务执行器基类"""

    def __init__(self):
        self.task_type = self.get_task_type()

    @abstractmethod
    def get_task_type(self):
        """
        获取任务类型名称

        Returns:
            str: 任务类型名称
        """
        pass

    @abstractmethod
    def get_pending_tasks(self, limit=10):
        """
        获取待执行的任务列表

        Args:
            limit: 最多获取的任务数量

        Returns:
            list: 任务列表
        """
        pass

    @abstractmethod
    def execute_task(self, task):
        """
        执行单个任务

        Args:
            task: 任务对象

        Returns:
            bool: 执行是否成功
        """
        pass

    @abstractmethod
    def update_task_status(self, task, status, error_message=""):
        """
        更新任务状态

        Args:
            task: 任务对象
            status: 新状态
            error_message: 错误信息（可选）
        """
        pass

    def run_task(self, task):
        """
        运行任务的包装方法，处理状态更新和异常捕获

        Args:
            task: 任务对象
        """
        try:
            log.info(f"[{self.task_type}] 开始执行任务: {task.id}")

            # 更新状态为处理中
            self.update_task_status(task, "processing")

            # 执行任务
            success = self.execute_task(task)

            if success:
                log.info(f"[{self.task_type}] 任务执行成功: {task.id}")
                self.update_task_status(task, "success")
            else:
                log.warning(f"[{self.task_type}] 任务执行失败: {task.id}")
                self.update_task_status(task, "failed", "执行失败")

        except Exception as e:
            log.error(f"[{self.task_type}] 任务执行异常: {task.id}, 错误: {e}")
            self.update_task_status(task, "failed", str(e))
