# -*- coding: utf-8 -*-
"""
即梦图片任务执行器
负责执行即梦图片生成任务
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.managers.base_task_executor import BaseTaskExecutor
from app.models.jimeng_image_task import JimengImageTask
from app.robot.jimeng.image_generator import JimengImageRobot
from app.utils.logger import log


class JimengImageTaskExecutor(BaseTaskExecutor):
    """即梦图片任务执行器"""

    def __init__(self):
        super().__init__()

    def get_task_type(self):
        """获取任务类型名称"""
        return "JimengImage"

    def get_pending_tasks(self, limit=10):
        """
        获取待执行的任务列表

        Args:
            limit: 最多获取的任务数量

        Returns:
            list: 任务列表
        """
        try:
            # 查询 pending 状态的任务,按创建时间排序
            tasks = JimengImageTask.select().where(
                JimengImageTask.status == 'pending'
            ).order_by(
                JimengImageTask.created_at.asc()
            ).limit(limit)

            task_list = list(tasks)

            if task_list:
                log.info(f"获取到 {len(task_list)} 个待执行的即梦图片任务")

            return task_list

        except Exception as e:
            log.error(f"获取待执行任务失败: {str(e)}")
            return []

    def execute_task(self, task):
        """
        执行单个任务

        Args:
            task: JimengImageTask任务对象

        Returns:
            bool: 执行是否成功
        """
        try:
            log.info(f"开始执行任务 ID={task.id}, 提示词: {task.prompt[:50]}...")

            # 更新任务状态为处理中
            self.update_task_status(task, 'processing')

            # 检查是否有关联的账号
            if not task.account_id:
                raise Exception("任务未指定账号ID")

            # 使用 asyncio 运行异步任务
            result = asyncio.run(self._execute_async(task))

            if result['success']:
                # 更新任务状态为成功,并保存图片路径
                JimengImageTask.update_task_outputs(task.id, result['images'])
                log.info(f"任务 ID={task.id} 执行成功,生成了 {len(result['images'])} 张图片")
                return True
            else:
                # 更新任务状态为失败
                self.update_task_status(task, 'failed', result['message'])
                log.error(f"任务 ID={task.id} 执行失败: {result['message']}")
                return False

        except Exception as e:
            error_msg = f"执行任务异常: {str(e)}"
            log.error(error_msg)
            self.update_task_status(task, 'failed', error_msg)
            return False

    async def _execute_async(self, task):
        """
        异步执行任务

        Args:
            task: JimengImageTask任务对象

        Returns:
            dict: 执行结果
        """
        robot = None

        try:
            # 创建机器人实例
            robot = JimengImageRobot(task.account_id)

            # 初始化
            if not await robot.init():
                return {
                    'success': False,
                    'message': '初始化机器人失败',
                    'images': []
                }

            # 启动浏览器(使用无头模式提高效率)
            if not await robot.launch_browser(headless=True):
                return {
                    'success': False,
                    'message': '启动浏览器失败',
                    'images': []
                }

            # 打开即梦页面
            if not await robot.navigate_to_image_gen():
                return {
                    'success': False,
                    'message': '打开页面失败,可能Cookie已失效',
                    'images': []
                }

            # 执行图片生成
            result = await robot.generate_image(
                prompt=task.prompt,
                image_model=task.image_model,
                aspect_ratio=task.aspect_ratio,
                resolution=task.resolution
            )

            return result

        except Exception as e:
            log.error(f"异步执行任务失败: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'images': []
            }

        finally:
            # 确保关闭浏览器
            if robot:
                await robot.close()

    def update_task_status(self, task, status, error_message=""):
        """
        更新任务状态

        Args:
            task: 任务对象
            status: 新状态
            error_message: 错误信息（可选）
        """
        try:
            JimengImageTask.update_task_status(task.id, status, error_message)
            log.debug(f"任务 ID={task.id} 状态已更新为: {status}")
        except Exception as e:
            log.error(f"更新任务状态失败: {str(e)}")
