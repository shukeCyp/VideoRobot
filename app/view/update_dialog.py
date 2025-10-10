# -*- coding: utf-8 -*-
"""
更新提示对话框
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    MessageBox, ProgressBar, PrimaryPushButton,
    PushButton, BodyLabel, SubtitleLabel, InfoBar, InfoBarPosition
)
from app.utils.update_manager import get_update_manager
from app.utils.logger import log


class UpdateDialog(MessageBox):
    """更新提示对话框"""

    def __init__(self, app_update, parent=None):
        super().__init__("发现新版本", "", parent)

        self.app_update = app_update
        self.update_thread = None
        self.parent_widget = parent

        # 设置内容
        self._setup_content()

        # 设置按钮
        self.yesButton.setText("立即更新")
        self.cancelButton.setText("稍后提醒")

        # 连接信号
        self.yesButton.clicked.connect(self.start_download)

        # 添加进度条(隐藏)
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setVisible(False)
        self.textLayout.addWidget(self.progress_bar)

    def _setup_content(self):
        """设置对话框内容"""
        version = self.app_update.version

        content = f"<b>最新版本:</b> v{version}<br>"
        content += f"<b>当前版本:</b> v{self.app_update.current_version}<br><br>"
        content += "<b>点击\"立即更新\"开始下载更新</b>"

        self.textLabel.setText(content)

    def start_download(self):
        """开始下载更新"""
        # 禁用按钮
        self.yesButton.setEnabled(False)
        self.cancelButton.setEnabled(False)
        self.yesButton.setText("下载中...")

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 获取更新线程
        manager = get_update_manager()
        self.update_thread = manager.update_thread

        if self.update_thread:
            # 连接信号
            self.update_thread.download_progress.connect(self.on_download_progress)
            self.update_thread.download_complete.connect(self.on_download_complete)
            self.update_thread.error_occurred.connect(self.on_error)

            # 开始下载
            self.update_thread.download_update()

    def on_download_progress(self, percent):
        """下载进度回调"""
        self.progress_bar.setValue(percent)
        self.yesButton.setText(f"下载中... {percent}%")

    def on_download_complete(self):
        """下载完成"""
        self.progress_bar.setValue(100)
        self.yesButton.setText("下载完成")

        # 显示安装提示
        w = MessageBox(
            "准备安装更新",
            "更新已下载完成，应用将关闭并安装更新，然后自动重启。\n\n确认立即安装吗？",
            self.parent_widget
        )
        w.yesButton.setText("立即安装")
        w.cancelButton.setText("稍后安装")

        if w.exec():
            # 用户确认安装
            log.info("用户确认安装更新")
            self.accept()

            # 解压并重启
            if self.update_thread:
                self.update_thread.extract_and_restart()
        else:
            # 用户取消，关闭对话框
            self.reject()

    def on_error(self, error_msg):
        """下载错误"""
        log.error(f"更新失败: {error_msg}")

        # 恢复按钮状态
        self.yesButton.setEnabled(True)
        self.cancelButton.setEnabled(True)
        self.yesButton.setText("重试")
        self.progress_bar.setVisible(False)

        # 显示错误提示
        if self.parent_widget:
            InfoBar.error(
                title="更新失败",
                content=error_msg,
                parent=self.parent_widget,
                position=InfoBarPosition.TOP,
                duration=5000
            )
