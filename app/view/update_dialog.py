# -*- coding: utf-8 -*-
"""
更新提示对话框
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QApplication
from qfluentwidgets import (
    MessageBox, ProgressBar, PrimaryPushButton,
    PushButton, BodyLabel, SubtitleLabel, InfoBar, InfoBarPosition
)
from app.utils.logger import log


class UpdateDialog(MessageBox):
    """更新提示对话框"""

    def __init__(self, update_info: dict, parent=None):
        super().__init__("发现新版本", "", parent)

        self.update_info = update_info
        self.download_thread = None
        self.installer_path = None
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
        version = self.update_info.get("version", "未知")
        current_version = self.update_info.get("current_version", "未知")
        release_notes = self.update_info.get("release_notes", "")

        content = f"<b>最新版本:</b> v{version}<br>"
        content += f"<b>当前版本:</b> v{current_version}<br><br>"

        if release_notes:
            # 提取前5行更新说明
            notes_lines = release_notes.split('\n')[:5]
            content += "<b>更新内容:</b><br>"
            for line in notes_lines:
                if line.strip():
                    content += f"• {line.strip()}<br>"
            content += "<br>"

        content += "<b>点击\"立即更新\"开始下载</b>"

        self.textLabel.setText(content)

    def start_download(self):
        """开始下载更新"""
        try:
            from app.utils.update_manager import get_update_manager

            # 禁用按钮
            self.yesButton.setEnabled(False)
            self.cancelButton.setEnabled(False)
            self.yesButton.setText("下载中...")

            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            log.info("开始下载更新包...")

            # 获取下载URL
            download_url = self.update_info.get("download_url")

            if not download_url:
                self.on_error("未找到下载链接")
                return

            # 开始下载
            manager = get_update_manager()
            self.download_thread = manager.download_update(download_url)

            # 连接信号
            self.download_thread.download_progress.connect(self.on_download_progress)
            self.download_thread.download_complete.connect(self.on_download_complete)
            self.download_thread.error_occurred.connect(self.on_error)

            # 启动下载
            self.download_thread.start()

        except Exception as e:
            error_msg = f"启动下载失败: {str(e)}"
            log.error(error_msg)
            self.on_error(error_msg)

    def on_download_progress(self, downloaded: int, total: int, percent: int):
        """下载进度回调"""
        self.progress_bar.setValue(percent)
        self.yesButton.setText(f"下载中... {percent}%")

    def on_download_complete(self, installer_path: str):
        """下载完成"""
        self.progress_bar.setValue(100)
        self.yesButton.setText("下载完成")
        self.installer_path = installer_path

        log.info(f"更新包下载完成: {installer_path}")

        # 显示安装提示
        w = MessageBox(
            "下载完成",
            f"更新包已下载到:\n{installer_path}\n\n点击\"打开\"启动安装程序",
            self.parent_widget
        )
        w.yesButton.setText("打开")
        w.cancelButton.setText("稍后安装")

        if w.exec():
            # 用户确认安装
            self.accept()

            # 启动安装程序
            from app.utils.update_manager import get_update_manager
            manager = get_update_manager()

            if manager.install_update(installer_path):
                log.info("安装程序已启动，应用即将退出")

                # 显示提示
                InfoBar.success(
                    title="正在安装更新",
                    content="请按照安装向导完成更新",
                    parent=self.parent_widget,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )

                # 延迟退出应用
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(2000, lambda: QApplication.quit())
            else:
                InfoBar.error(
                    title="启动失败",
                    content="无法启动安装程序，请手动打开",
                    parent=self.parent_widget,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
        else:
            # 用户取消，关闭对话框
            self.reject()

    def on_error(self, error_msg: str):
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
