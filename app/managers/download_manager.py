# -*- coding: utf-8 -*-
"""
全局下载线程池管理器
"""
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Optional, Any
import threading
from app.utils.logger import log
from app.utils.config_manager import get_config_manager

# 默认下载线程数
DEFAULT_DOWNLOAD_THREADS = 3
# 配置键名
CONFIG_KEY_DOWNLOAD_THREADS = "download_threads"


class DownloadManager:
    """全局下载线程池管理器"""

    def __init__(self):
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()
        self._max_workers = DEFAULT_DOWNLOAD_THREADS

    def _load_config(self):
        """从配置中加载线程数"""
        config_manager = get_config_manager()
        self._max_workers = config_manager.get_int(
            CONFIG_KEY_DOWNLOAD_THREADS,
            DEFAULT_DOWNLOAD_THREADS
        )
        log.debug(f"下载线程池配置: max_workers={self._max_workers}")

    def _ensure_executor(self):
        """确保线程池已创建"""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._load_config()
                    self._executor = ThreadPoolExecutor(
                        max_workers=self._max_workers,
                        thread_name_prefix="download_"
                    )
                    log.info(f"下载线程池已创建: max_workers={self._max_workers}")

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        """
        提交下载任务到线程池

        Args:
            fn: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Future: 任务的Future对象
        """
        self._ensure_executor()
        return self._executor.submit(fn, *args, **kwargs)

    def get_max_workers(self) -> int:
        """获取最大线程数"""
        self._ensure_executor()
        return self._max_workers

    def set_max_workers(self, max_workers: int):
        """
        设置最大线程数（需要重启线程池生效）

        Args:
            max_workers: 最大线程数
        """
        if max_workers < 1:
            max_workers = 1
        if max_workers > 20:
            max_workers = 20

        # 保存到配置
        config_manager = get_config_manager()
        config_manager.set(CONFIG_KEY_DOWNLOAD_THREADS, max_workers)

        self._max_workers = max_workers
        log.info(f"下载线程池配置已更新: max_workers={max_workers}")

        # 重新创建线程池
        self.restart()

    def restart(self):
        """重启线程池"""
        with self._lock:
            if self._executor is not None:
                log.info("正在关闭下载线程池...")
                self._executor.shutdown(wait=False)
                self._executor = None

            self._load_config()
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="download_"
            )
            log.info(f"下载线程池已重启: max_workers={self._max_workers}")

    def shutdown(self, wait: bool = True):
        """
        关闭线程池

        Args:
            wait: 是否等待任务完成
        """
        with self._lock:
            if self._executor is not None:
                log.info("正在关闭下载线程池...")
                self._executor.shutdown(wait=wait)
                self._executor = None
                log.info("下载线程池已关闭")

    def get_status(self) -> dict:
        """获取线程池状态"""
        return {
            "max_workers": self._max_workers,
            "is_running": self._executor is not None
        }


# 全局单例
_download_manager: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """获取下载管理器单例"""
    global _download_manager
    if _download_manager is None:
        _download_manager = DownloadManager()
    return _download_manager
