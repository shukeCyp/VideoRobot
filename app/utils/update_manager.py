# -*- coding: utf-8 -*-
"""
PyUpdater 更新管理模块
"""
import sys
from PyQt5.QtCore import QThread, pyqtSignal
from pyupdater.client import Client
from client_config import ClientConfig
from app.version import __version__, __app_name__
from app.utils.logger import log


class UpdateThread(QThread):
    """更新检查线程"""
    update_available = pyqtSignal(object)  # 有更新可用
    no_update = pyqtSignal()  # 无更新
    download_progress = pyqtSignal(int)  # 下载进度
    download_complete = pyqtSignal()  # 下载完成
    error_occurred = pyqtSignal(str)  # 发生错误

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = Client(ClientConfig())
        self.app_update = None

    def run(self):
        """检查更新"""
        try:
            log.info(f"检查更新中... 当前版本: {__version__}")

            # 刷新更新信息
            self.client.refresh()

            # 检查是否有新版本
            self.app_update = self.client.update_check(
                __app_name__,
                __version__
            )

            if self.app_update:
                log.info(f"发现新版本: {self.app_update.version}")
                self.update_available.emit(self.app_update)
            else:
                log.info("当前已是最新版本")
                self.no_update.emit()

        except Exception as e:
            error_msg = f"检查更新失败: {str(e)}"
            log.error(error_msg)
            self.error_occurred.emit(error_msg)

    def download_update(self):
        """下载更新"""
        if not self.app_update:
            self.error_occurred.emit("没有可用的更新")
            return

        try:
            log.info("开始下载更新...")

            # 下载更新(带进度回调)
            success = self.app_update.download(progress_hooks=[self._progress_callback])

            if success:
                log.info("更新下载完成")
                self.download_complete.emit()
            else:
                self.error_occurred.emit("下载更新失败")

        except Exception as e:
            error_msg = f"下载更新时出错: {str(e)}"
            log.error(error_msg)
            self.error_occurred.emit(error_msg)

    def _progress_callback(self, status):
        """下载进度回调"""
        if 'percent_complete' in status:
            percent = int(status['percent_complete'])
            self.download_progress.emit(percent)
            log.debug(f"下载进度: {percent}%")

    def extract_and_restart(self):
        """解压并重启应用"""
        if not self.app_update:
            self.error_occurred.emit("没有可用的更新")
            return

        try:
            log.info("准备安装更新并重启...")

            # 解压更新
            if self.app_update.extract_restart():
                log.info("更新安装成功，应用将重启")
                # 重启会自动执行，应用会关闭
            else:
                self.error_occurred.emit("安装更新失败")

        except Exception as e:
            error_msg = f"安装更新时出错: {str(e)}"
            log.error(error_msg)
            self.error_occurred.emit(error_msg)


class UpdateManager:
    """更新管理器"""

    def __init__(self):
        self.update_thread = None

    def check_for_updates(self):
        """检查更新"""
        if self.update_thread and self.update_thread.isRunning():
            log.warning("更新检查已在进行中")
            return None

        self.update_thread = UpdateThread()
        return self.update_thread

    def get_current_version(self):
        """获取当前版本"""
        return __version__


# 全局单例
_update_manager = None


def get_update_manager():
    """获取更新管理器单例"""
    global _update_manager
    if _update_manager is None:
        _update_manager = UpdateManager()
    return _update_manager
