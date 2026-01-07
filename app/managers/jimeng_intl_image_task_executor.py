# -*- coding: utf-8 -*-
from app.models.jimeng_intl_image_task import JimengIntlImageTask
from app.models.jimeng_intl_account import JimengIntlAccount
from app.client.jimeng_api_client import get_jimeng_api_client
from app.utils.logger import log
from datetime import datetime


class JimengIntlImageTaskExecutor:
    """即梦国际版图片生成任务执行器"""

    def __init__(self):
        """初始化执行器"""
        self.client = get_jimeng_api_client()

    def get_task_type(self) -> str:
        """获取任务类型"""
        return "jimeng_intl_image"

    def get_pending_tasks(self, limit: int = 10) -> list:
        """
        获取待执行的任务

        Args:
            limit: 最多获取的任务数量

        Returns:
            list: 待执行任务列表
        """
        try:
            # 获取状态为0（排队中）的任务
            tasks = JimengIntlImageTask.select().where(
                (JimengIntlImageTask.status == 0) &
                (JimengIntlImageTask.isdel == 0)
            ).order_by(JimengIntlImageTask.create_at.asc()).limit(limit)

            pending_list = list(tasks)
            if pending_list:
                log.info(f"扫描到 {len(pending_list)} 个待处理的国际版图片生成任务")
            return pending_list

        except Exception as e:
            log.error(f"获取待执行任务失败: {e}")
            return []

    def execute_task(self, task: JimengIntlImageTask) -> bool:
        """
        执行图片生成任务

        Args:
            task: 任务对象

        Returns:
            bool: 是否执行成功
        """
        try:
            task_id = task.id
            log.info(f"开始执行国际版图片生成任务: ID={task_id}")

            # 更新任务状态为生成中（1）
            task.status = 1
            task.update_at = datetime.now()
            task.save()
            log.debug(f"任务 {task_id} 状态已更新为: 生成中")

            # 获取账号信息
            if not task.account_id:
                log.warning(f"任务 {task_id} 没有绑定账号，使用随机可用账号")
                account = JimengIntlAccount.get_available_account()
                if not account:
                    raise ValueError("没有可用的账号")
                task.account_id = account.id
            else:
                account = JimengIntlAccount.get_account_by_id(task.account_id)
                if not account:
                    raise ValueError(f"账号不存在: {task.account_id}")

            # 获取参考图片
            image_paths = task.get_input_images()

            # 调用API生成图片
            log.debug(f"任务 {task_id} 调用API生成图片，参考图片数: {len(image_paths) if image_paths else 0}")
            result = self.client.generate_image(
                token=account.session_id,
                prompt=task.prompt,
                image_paths=image_paths,
                ratio=task.ratio,
                model=task.model,
                resolution=task.resolution
            )

            if not result:
                raise ValueError("API返回空结果")

            log.debug(f"任务 {task_id} API返回结果类型: {type(result).__name__}")
            log.debug(f"任务 {task_id} API返回结果键: {result.keys() if isinstance(result, dict) else 'N/A'}")

            # 检查是否积分不足
            code = result.get("code")
            if code == -2001:
                log.warning(f"账号 {account.id} 积分不足，禁用该账号今天")
                JimengIntlAccount.disable_account_today(account.id)
                # 重置任务状态为排队中，等待下次使用其他账号执行
                task.status = 0
                task.account_id = None
                task.message = "账号积分不足，已重新排队"
                task.update_at = datetime.now()
                task.save()
                log.info(f"任务 {task_id} 已重新排队，等待其他账号执行")
                return False

            # 保存结果
            task.status = 2  # 已完成
            task.code = str(code) if code else "0"
            task.message = result.get("message", "生成成功")

            # 提取生成的图片URL
            output_urls = []
            if "data" in result and isinstance(result["data"], list):
                for item in result["data"]:
                    if isinstance(item, dict) and "url" in item:
                        output_urls.append(item["url"])
                        log.debug(f"任务 {task_id} 提取到图片URL: {item['url'][:80]}...")

            # 检查是否成功获取输出图片
            if not output_urls:
                # 未获取到输出图片，标记为失败
                log.warning(f"任务 {task_id} 未发现输出图片，标记为失败")
                task.status = 3  # 失败
                task.code = "no_output"
                task.message = "API返回成功但未生成图片"
                task.update_at = datetime.now()
                task.save()
                return False

            # 保存输出图片URL到数据库
            log.info(f"任务 {task_id} 成功生成 {len(output_urls)} 张图片")
            task.set_output_images(output_urls)

            task.update_at = datetime.now()
            task.save()

            log.info(f"任务 {task_id} 执行成功，状态已更新为: 已完成")
            return True

        except Exception as e:
            log.error(f"任务 {task.id} 执行失败: {e}")
            try:
                # 更新任务状态为失败（3）
                task.status = 3
                task.code = "error"
                task.message = str(e)
                task.update_at = datetime.now()
                task.save()
                log.debug(f"任务 {task.id} 状态已更新为: 失败")
            except Exception as save_error:
                log.error(f"保存任务失败状态出错: {save_error}")
            return False

    def _get_available_account(self) -> JimengIntlAccount:
        """
        获取一个可用的账号（已废弃，使用 JimengIntlAccount.get_available_account()）

        Returns:
            JimengIntlAccount: 可用的账号，如果没有返回None
        """
        return JimengIntlAccount.get_available_account()
