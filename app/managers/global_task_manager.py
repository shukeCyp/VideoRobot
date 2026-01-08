# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor
import time
from app.utils.logger import log
from app.utils.config_manager import get_config_manager

# 默认任务管理器线程数
DEFAULT_TASK_MANAGER_THREADS = 50
# 配置键名
CONFIG_KEY_TASK_MANAGER_THREADS = "task_manager_threads"


class GlobalTaskManager(QThread):
    """全局任务管理器"""

    # 信号
    task_started = pyqtSignal(str, int)  # 任务类型, 任务ID
    task_finished = pyqtSignal(str, int, bool)  # 任务类型, 任务ID, 是否成功
    status_changed = pyqtSignal(str)  # 状态消息

    def __init__(self, max_workers=None, poll_interval=5):
        """
        初始化任务管理器

        Args:
            max_workers: 线程池最大工作线程数，如不传则从配置读取
            poll_interval: 轮询间隔（秒）
        """
        super().__init__()

        # 从配置读取线程数
        if max_workers is None:
            config_manager = get_config_manager()
            max_workers = config_manager.get_int(
                CONFIG_KEY_TASK_MANAGER_THREADS,
                DEFAULT_TASK_MANAGER_THREADS
            )

        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.is_running = False

        # 线程池
        self.thread_pool = None

        # 注册所有任务执行器
        self.executors = []
        self.register_executors()

    def register_executors(self):
        """注册所有任务执行器"""
        # 注册即梦国际版图片生成任务执行器
        from app.managers.jimeng_intl_image_task_executor import JimengIntlImageTaskExecutor
        self.executors.append(JimengIntlImageTaskExecutor())

        # 注册即梦国际版视频生成任务执行器
        from app.managers.jimeng_intl_video_task_executor import JimengIntlVideoTaskExecutor
        self.executors.append(JimengIntlVideoTaskExecutor())

        log.info(f"已注册 {len(self.executors)} 个任务执行器")

    def set_max_workers(self, max_workers, save_config=True):
        """
        设置线程池最大工作线程数

        Args:
            max_workers: 最大工作线程数
            save_config: 是否保存到配置
        """
        # 限制范围
        if max_workers < 1:
            max_workers = 1
        if max_workers > 200:
            max_workers = 200

        self.max_workers = max_workers

        # 保存到配置
        if save_config:
            config_manager = get_config_manager()
            config_manager.set(CONFIG_KEY_TASK_MANAGER_THREADS, max_workers)

        if self.thread_pool:
            # 重新创建线程池
            self.thread_pool.shutdown(wait=False)
            self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
            log.info(f"任务管理器线程池大小已更新为: {self.max_workers}")

    def set_poll_interval(self, interval):
        """
        设置轮询间隔

        Args:
            interval: 间隔秒数
        """
        self.poll_interval = interval
        log.info(f"轮询间隔已更新为: {self.poll_interval}秒")

    def run(self):
        """主循环：轮询检查并执行任务"""
        self.is_running = True
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

        log.info(f"任务管理器启动，线程池大小: {self.max_workers}, 轮询间隔: {self.poll_interval}秒")
        self.status_changed.emit("任务管理器已启动")

        while self.is_running:
            try:
                log.debug(f"开始扫描任务，当前执行器数量: {len(self.executors)}")

                # TODO: 轮询所有执行器，检查是否有待执行的任务
                # 1. 遍历所有执行器
                # 2. 调用每个执行器的 get_pending_tasks()
                # 3. 如果有待执行任务，提交到线程池执行
                # 4. 注意控制并发数量

                total_pending = 0

                # 示例框架代码：
                for executor in self.executors:
                    executor_type = executor.get_task_type()
                    log.debug(f"正在扫描 {executor_type} 类型的任务")

                    # 获取待执行任务
                    pending_tasks = executor.get_pending_tasks(limit=self.max_workers)

                    if pending_tasks:
                        log.info(f"发现 {len(pending_tasks)} 个待处理的 {executor_type} 任务")
                        total_pending += len(pending_tasks)

                    # 提交任务到线程池
                    for task in pending_tasks:
                        # TODO: 检查线程池是否还有空闲，避免提交过多任务
                        log.debug(f"提交任务到线程池: {executor_type} - 任务ID: {getattr(task, 'id', 'unknown')}")
                        self.submit_task(executor, task)

                if total_pending == 0:
                    log.debug("本次扫描未发现待处理任务")

                # 等待一段时间后再次轮询
                log.debug(f"等待 {self.poll_interval} 秒后进行下次扫描")
                time.sleep(self.poll_interval)

            except Exception as e:
                log.error(f"任务管理器运行错误: {e}")
                time.sleep(self.poll_interval)

        # 关闭线程池
        self.thread_pool.shutdown(wait=True)
        log.info("任务管理器已停止")
        self.status_changed.emit("任务管理器已停止")

    def submit_task(self, executor, task):
        """
        提交任务到线程池

        Args:
            executor: 任务执行器
            task: 任务对象
        """
        try:
            task_id = getattr(task, 'id', None)
            task_type = executor.get_task_type()

            log.info(f"提交任务到线程池: {task_type} - ID={task_id}")

            # 发送任务开始信号
            self.task_started.emit(task_type, task_id)

            # 提交到线程池执行
            future = self.thread_pool.submit(executor.execute_task, task)

            # 添加完成回调
            def task_done_callback(f):
                try:
                    success = f.result()
                    log.info(f"任务完成: {task_type} - ID={task_id}, 成功={success}")
                    self.task_finished.emit(task_type, task_id, success)
                except Exception as e:
                    log.error(f"任务执行异常: {task_type} - ID={task_id}, 错误={str(e)}")
                    self.task_finished.emit(task_type, task_id, False)

            future.add_done_callback(task_done_callback)

        except Exception as e:
            log.error(f"提交任务失败: {str(e)}")

    def stop(self):
        """停止任务管理器"""
        log.info("正在停止任务管理器...")
        self.is_running = False

    def get_status(self):
        """
        获取任务管理器状态

        Returns:
            dict: 状态信息
        """
        # TODO: 返回当前运行状态、线程池状态、各类型任务统计等
        return {
            'is_running': self.is_running,
            'max_workers': self.max_workers,
            'poll_interval': self.poll_interval,
            'executor_count': len(self.executors)
        }


# 全局单例
_global_task_manager = None


def get_global_task_manager():
    """获取全局任务管理器单例"""
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = GlobalTaskManager()
    return _global_task_manager
