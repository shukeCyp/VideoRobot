# -*- coding: utf-8 -*-
"""
GitHub Release 更新管理模块
直接使用 GitHub API，无需第三方库
"""
import os
import sys
import json
import hashlib
import zipfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Tuple
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from app.version import __version__, __app_name__
from app.utils.logger import log


class UpdateChecker(QThread):
    """更新检查线程"""
    update_available = pyqtSignal(dict)  # 有更新可用
    no_update = pyqtSignal()  # 无更新
    error_occurred = pyqtSignal(str)  # 发生错误

    def __init__(self, repo_owner: str, repo_name: str, parent=None):
        super().__init__(parent)
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = __version__

    def run(self):
        """检查更新"""
        try:
            log.info(f"检查更新中... 当前版本: {self.current_version}")

            # GitHub API URL
            api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"

            # 请求最新版本信息
            response = requests.get(
                api_url,
                timeout=10,
                headers={"Accept": "application/vnd.github.v3+json"}
            )

            if response.status_code != 200:
                self.error_occurred.emit(f"获取版本信息失败: HTTP {response.status_code}")
                return

            release_info = response.json()

            # 解析版本号
            remote_version = release_info.get("tag_name", "").lstrip("v")

            if not remote_version:
                self.error_occurred.emit("无法解析远程版本号")
                return

            # 比较版本号
            if self._compare_version(remote_version, self.current_version) > 0:
                log.info(f"发现新版本: {remote_version}")

                # 构建更新信息
                update_info = {
                    "version": remote_version,
                    "current_version": self.current_version,
                    "release_notes": release_info.get("body", ""),
                    "published_at": release_info.get("published_at", ""),
                    "html_url": release_info.get("html_url", "")
                }

                self.update_available.emit(update_info)
            else:
                log.info("当前已是最新版本")
                self.no_update.emit()

        except requests.exceptions.Timeout:
            self.error_occurred.emit("检查更新超时，请检查网络连接")
        except Exception as e:
            error_msg = f"检查更新失败: {str(e)}"
            log.error(error_msg)
            self.error_occurred.emit(error_msg)

    def _compare_version(self, v1: str, v2: str) -> int:
        """比较版本号"""
        try:
            # 移除版本号前缀 (V 或 v)
            v1 = v1.lstrip('vV')
            v2 = v2.lstrip('vV')

            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]

            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0

                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1

            return 0
        except Exception as e:
            log.error(f"版本号比较失败: {str(e)}")
            return 0


class UpdateManager:
    """更新管理器"""

    def __init__(self, repo_owner: str = "YOUR_GITHUB_USERNAME", repo_name: str = "YOUR_REPO_NAME"):
        """
        初始化更新管理器

        Args:
            repo_owner: GitHub 用户名或组织名
            repo_name: 仓库名
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.update_checker = None

    def check_for_updates(self) -> UpdateChecker:
        """检查更新"""
        if self.update_checker and self.update_checker.isRunning():
            log.warning("更新检查已在进行中")
            return self.update_checker

        self.update_checker = UpdateChecker(self.repo_owner, self.repo_name)
        return self.update_checker

    def get_current_version(self) -> str:
        """获取当前版本"""
        return __version__


# 全局单例
_update_manager = None


def get_update_manager(repo_owner: str = "YOUR_GITHUB_USERNAME",
                       repo_name: str = "YOUR_REPO_NAME") -> UpdateManager:
    """
    获取更新管理器单例

    Args:
        repo_owner: GitHub 用户名或组织名
        repo_name: 仓库名
    """
    global _update_manager
    if _update_manager is None:
        _update_manager = UpdateManager(repo_owner, repo_name)
    return _update_manager
