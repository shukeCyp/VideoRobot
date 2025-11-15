# -*- coding: utf-8 -*-
"""
日志管理工具类
提供日志大小查询、清除日志、打包日志等功能
"""
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
from app.utils.path_helper import get_logs_dir
from app.utils.logger import log


class LogManager:
    """日志管理器"""

    def __init__(self):
        self.logs_dir = get_logs_dir()

    def get_log_size(self) -> Tuple[int, str]:
        """
        获取日志文件夹的总大小

        Returns:
            Tuple[int, str]: (字节数, 格式化后的大小字符串)
        """
        total_size = 0

        if not os.path.exists(self.logs_dir):
            return 0, "0 B"

        # 遍历日志目录下的所有文件
        for root, dirs, files in os.walk(self.logs_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)

        # 格式化大小
        formatted_size = self._format_size(total_size)

        return total_size, formatted_size

    def _format_size(self, size_bytes: int) -> str:
        """
        格式化文件大小

        Args:
            size_bytes: 字节数

        Returns:
            str: 格式化后的大小字符串（如 "1.5 MB"）
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def clear_logs(self) -> Tuple[bool, str]:
        """
        清除所有日志文件

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            if not os.path.exists(self.logs_dir):
                return True, "日志目录不存在，无需清除"

            deleted_count = 0
            total_size = 0

            # 遍历并删除所有日志文件
            for root, dirs, files in os.walk(self.logs_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1

            formatted_size = self._format_size(total_size)
            message = f"成功清除 {deleted_count} 个日志文件，释放空间 {formatted_size}"
            log.info(message)

            return True, message

        except Exception as e:
            error_msg = f"清除日志失败: {str(e)}"
            log.error(error_msg)
            return False, error_msg

    def pack_logs(self, output_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        打包所有日志文件为 ZIP 压缩包

        Args:
            output_path: 输出路径，如果为 None 则使用默认路径

        Returns:
            Tuple[bool, str]: (是否成功, 消息/压缩包路径)
        """
        try:
            if not os.path.exists(self.logs_dir):
                return False, "日志目录不存在"

            # 检查是否有日志文件
            log_files = []
            for root, dirs, files in os.walk(self.logs_dir):
                for file in files:
                    log_files.append(os.path.join(root, file))

            if not log_files:
                return False, "没有日志文件可以打包"

            # 生成压缩包文件名
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"logs_backup_{timestamp}.zip"
                output_path = os.path.join(os.path.expanduser("~"), "Desktop", zip_filename)

            # 创建 ZIP 压缩包
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in log_files:
                    # 计算相对路径
                    arcname = os.path.relpath(file_path, self.logs_dir)
                    zipf.write(file_path, arcname)

            # 获取压缩包大小
            zip_size = os.path.getsize(output_path)
            formatted_size = self._format_size(zip_size)

            message = f"成功打包 {len(log_files)} 个日志文件\n保存路径: {output_path}\n压缩包大小: {formatted_size}"
            log.info(f"日志打包成功: {output_path}")

            return True, output_path

        except Exception as e:
            error_msg = f"打包日志失败: {str(e)}"
            log.error(error_msg)
            return False, error_msg

    def get_log_files_count(self) -> int:
        """
        获取日志文件数量

        Returns:
            int: 日志文件数量
        """
        count = 0

        if not os.path.exists(self.logs_dir):
            return 0

        for root, dirs, files in os.walk(self.logs_dir):
            count += len(files)

        return count


# 创建全局单例
_log_manager_instance = None


def get_log_manager() -> LogManager:
    """获取日志管理器单例"""
    global _log_manager_instance
    if _log_manager_instance is None:
        _log_manager_instance = LogManager()
    return _log_manager_instance
