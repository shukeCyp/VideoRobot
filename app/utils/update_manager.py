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

                # 查找适合当前平台的安装包
                download_url = self._find_download_url(release_info)

                if not download_url:
                    self.error_occurred.emit("未找到适合当前平台的安装包")
                    return

                # 构建更新信息
                update_info = {
                    "version": remote_version,
                    "current_version": self.current_version,
                    "download_url": download_url,
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

    def _find_download_url(self, release_info: dict) -> Optional[str]:
        """查找适合当前平台的下载链接"""
        assets = release_info.get("assets", [])

        platform = sys.platform
        arch = "x64"  # 默认64位

        # 根据平台查找对应的安装包
        keywords = {
            "win32": [".exe", "windows", "win"],
            "darwin": [".dmg", ".pkg", "macos", "mac"],
            "linux": [".deb", ".rpm", ".AppImage", "linux"]
        }

        platform_keywords = keywords.get(platform, [])

        for asset in assets:
            name = asset.get("name", "").lower()
            download_url = asset.get("browser_download_url", "")

            # 检查是否匹配当前平台
            if any(kw in name for kw in platform_keywords):
                return download_url

        # 如果没找到，返回第一个资源
        if assets:
            return assets[0].get("browser_download_url", "")

        return None


class UpdateDownloader(QThread):
    """更新下载线程"""
    download_progress = pyqtSignal(int, int, int)  # downloaded, total, percentage
    download_complete = pyqtSignal(str)  # 文件路径
    error_occurred = pyqtSignal(str)  # 错误信息

    def __init__(self, download_url: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.download_dir = Path.home() / "Downloads"

    def run(self):
        """下载更新"""
        try:
            log.info(f"开始下载更新: {self.download_url}")

            # 生成本地文件路径
            filename = os.path.basename(self.download_url)
            local_file = self.download_dir / filename

            # 下载文件
            response = requests.get(self.download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))

            downloaded = 0
            with open(local_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 发送进度
                        if total_size > 0:
                            percentage = int((downloaded / total_size) * 100)
                            self.download_progress.emit(downloaded, total_size, percentage)

            log.info(f"下载完成: {local_file}")
            self.download_complete.emit(str(local_file))

        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            log.error(error_msg)
            self.error_occurred.emit(error_msg)


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
        self.update_downloader = None

    def check_for_updates(self) -> UpdateChecker:
        """检查更新"""
        if self.update_checker and self.update_checker.isRunning():
            log.warning("更新检查已在进行中")
            return self.update_checker

        self.update_checker = UpdateChecker(self.repo_owner, self.repo_name)
        return self.update_checker

    def download_update(self, download_url: str) -> UpdateDownloader:
        """下载更新"""
        if self.update_downloader and self.update_downloader.isRunning():
            log.warning("更新下载已在进行中")
            return self.update_downloader

        self.update_downloader = UpdateDownloader(download_url)
        return self.update_downloader

    def install_update(self, installer_path: str) -> bool:
        """
        安装更新

        Args:
            installer_path: 安装包路径

        Returns:
            bool: 是否成功启动安装程序
        """
        try:
            if not os.path.exists(installer_path):
                log.error(f"安装包不存在: {installer_path}")
                return False

            log.info(f"启动安装程序: {installer_path}")

            if sys.platform == "win32":
                # Windows: 直接打开安装程序
                os.startfile(installer_path)
            elif sys.platform == "darwin":
                # macOS: 打开安装包
                subprocess.Popen(["open", installer_path])
            else:
                # Linux: 使用 xdg-open
                subprocess.Popen(["xdg-open", installer_path])

            return True

        except Exception as e:
            log.error(f"启动安装程序失败: {str(e)}")
            return False

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
