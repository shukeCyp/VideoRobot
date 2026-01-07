# -*- coding: utf-8 -*-
"""
更新提示对话框
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QApplication
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from qfluentwidgets import (
    MessageBox, PrimaryPushButton,
    PushButton, BodyLabel, SubtitleLabel, InfoBar, InfoBarPosition
)
from app.utils.logger import log


class UpdateDialog(MessageBox):
    """更新提示对话框"""

    def __init__(self, update_info: dict, parent=None):
        super().__init__("发现新版本", "", parent)

        self.update_info = update_info
        self.parent_widget = parent

        # 设置内容
        self._setup_content()

        # 设置按钮
        self.yesButton.setText("去下载")
        self.cancelButton.setVisible(False)  # 隐藏取消按钮

        # 连接信号
        self.yesButton.clicked.connect(self.open_github_release)

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

        content += "<b>发现新版本，请点击\"去下载\"更新</b>"

        self.contentLabel.setText(content)

    def open_github_release(self):
        """打开 GitHub 发布页面"""
        try:
            release_url = self.update_info.get("html_url")

            if not release_url:
                log.error("未找到发布页面链接")
                InfoBar.error(
                    title="错误",
                    content="无法获取发布页面链接",
                    parent=self.parent_widget,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                return

            log.info(f"打开 GitHub 发布页面: {release_url}")

            # 使用系统默认浏览器打开链接
            QDesktopServices.openUrl(QUrl(release_url))

            # 关闭对话框
            self.accept()

        except Exception as e:
            error_msg = f"打开链接失败: {str(e)}"
            log.error(error_msg)
            InfoBar.error(
                title="错误",
                content=error_msg,
                parent=self.parent_widget,
                position=InfoBarPosition.TOP,
                duration=3000
            )

