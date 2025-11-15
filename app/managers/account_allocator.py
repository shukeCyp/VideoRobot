# -*- coding: utf-8 -*-
"""
账号分配管理器
负责为任务自动分配合适的账号
"""
from typing import Optional
from app.models.jimeng_account import JimengAccount
from app.models.jimeng_image_task import JimengImageTask
from app.utils.logger import log


class AccountAllocator:
    """账号分配管理器"""

    def __init__(self):
        """初始化"""
        self.allocation_strategy = "round_robin"  # 分配策略: round_robin(轮询), least_busy(最少任务)

    def set_strategy(self, strategy: str):
        """
        设置分配策略

        Args:
            strategy: 策略名称 (round_robin, least_busy)
        """
        if strategy in ['round_robin', 'least_busy']:
            self.allocation_strategy = strategy
            log.info(f"账号分配策略已设置为: {strategy}")
        else:
            log.warning(f"未知的分配策略: {strategy}, 保持当前策略")

    def allocate_account(self) -> Optional[JimengAccount]:
        """
        为任务分配账号

        Returns:
            JimengAccount: 分配的账号对象, 如果没有可用账号则返回None
        """
        if self.allocation_strategy == "round_robin":
            return self._allocate_round_robin()
        elif self.allocation_strategy == "least_busy":
            return self._allocate_least_busy()
        else:
            return self._allocate_round_robin()

    def _allocate_round_robin(self) -> Optional[JimengAccount]:
        """
        轮询分配策略
        按账号ID顺序依次分配,循环使用

        Returns:
            JimengAccount: 分配的账号
        """
        try:
            # 获取所有账号
            accounts = list(JimengAccount.get_all_accounts())

            if not accounts:
                log.warning("没有可用的即梦账号")
                return None

            # 获取最近一次分配的账号
            last_task = JimengImageTask.select().where(
                JimengImageTask.account_id.is_null(False)
            ).order_by(JimengImageTask.created_at.desc()).first()

            if not last_task:
                # 如果没有历史任务,返回第一个账号
                account = accounts[0]
                log.info(f"[轮询分配] 首次分配账号: {account.nickname} (ID: {account.id})")
                return account

            # 找到下一个账号
            last_account_id = last_task.account_id
            account_ids = [acc.id for acc in accounts]

            try:
                current_index = account_ids.index(last_account_id)
                next_index = (current_index + 1) % len(accounts)
            except ValueError:
                # 上次使用的账号已被删除,从第一个开始
                next_index = 0

            account = accounts[next_index]
            log.info(f"[轮询分配] 分配账号: {account.nickname} (ID: {account.id})")
            return account

        except Exception as e:
            log.error(f"轮询分配账号失败: {str(e)}")
            return None

    def _allocate_least_busy(self) -> Optional[JimengAccount]:
        """
        最少任务优先策略
        分配当前正在处理任务数最少的账号

        Returns:
            JimengAccount: 分配的账号
        """
        try:
            # 获取所有账号
            accounts = list(JimengAccount.get_all_accounts())

            if not accounts:
                log.warning("没有可用的即梦账号")
                return None

            # 统计每个账号的处理中任务数
            account_tasks = {}
            for account in accounts:
                # 统计该账号的 processing 状态任务数
                processing_count = JimengImageTask.select().where(
                    (JimengImageTask.account_id == account.id) &
                    (JimengImageTask.status == 'processing')
                ).count()

                account_tasks[account.id] = {
                    'account': account,
                    'processing_count': processing_count
                }

            # 找出任务数最少的账号
            min_tasks = min(account_tasks.values(), key=lambda x: x['processing_count'])
            account = min_tasks['account']

            log.info(f"[最少任务分配] 分配账号: {account.nickname} (ID: {account.id}), "
                    f"当前处理中任务数: {min_tasks['processing_count']}")

            return account

        except Exception as e:
            log.error(f"最少任务分配失败: {str(e)}")
            return None

    def allocate_and_assign(self, task: JimengImageTask) -> bool:
        """
        为任务分配账号并保存

        Args:
            task: 任务对象

        Returns:
            bool: 是否分配成功
        """
        try:
            # 如果任务已经有账号,跳过分配
            if task.account_id:
                log.debug(f"任务 ID={task.id} 已有账号 (ID: {task.account_id}), 跳过分配")
                return True

            # 分配账号
            account = self.allocate_account()

            if not account:
                log.error(f"无法为任务 ID={task.id} 分配账号")
                return False

            # 更新任务的账号ID
            task.account_id = account.id
            task.save()

            log.info(f"✅ 任务 ID={task.id} 已分配账号: {account.nickname} (ID: {account.id})")
            return True

        except Exception as e:
            log.error(f"分配并保存账号失败: {str(e)}")
            return False

    def get_account_stats(self):
        """
        获取账号使用统计

        Returns:
            list: 账号统计信息列表
        """
        try:
            accounts = list(JimengAccount.get_all_accounts())
            stats = []

            for account in accounts:
                # 统计各状态任务数
                pending_count = JimengImageTask.select().where(
                    (JimengImageTask.account_id == account.id) &
                    (JimengImageTask.status == 'pending')
                ).count()

                processing_count = JimengImageTask.select().where(
                    (JimengImageTask.account_id == account.id) &
                    (JimengImageTask.status == 'processing')
                ).count()

                success_count = JimengImageTask.select().where(
                    (JimengImageTask.account_id == account.id) &
                    (JimengImageTask.status == 'success')
                ).count()

                failed_count = JimengImageTask.select().where(
                    (JimengImageTask.account_id == account.id) &
                    (JimengImageTask.status == 'failed')
                ).count()

                stats.append({
                    'account_id': account.id,
                    'nickname': account.nickname,
                    'pending': pending_count,
                    'processing': processing_count,
                    'success': success_count,
                    'failed': failed_count,
                    'total': pending_count + processing_count + success_count + failed_count
                })

            return stats

        except Exception as e:
            log.error(f"获取账号统计失败: {str(e)}")
            return []


# 全局单例
_account_allocator = None


def get_account_allocator() -> AccountAllocator:
    """获取账号分配管理器单例"""
    global _account_allocator
    if _account_allocator is None:
        _account_allocator = AccountAllocator()
    return _account_allocator
