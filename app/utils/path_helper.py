# -*- coding: utf-8 -*-
import os
import platform


def get_app_data_dir():
    """获取应用数据目录"""
    system = platform.system()
    app_name = "VideoRobot"

    if system == "Windows":
        # Windows: C:\Users\用户名\AppData\Roaming\VideoRobot
        base_dir = os.getenv("APPDATA")
        app_dir = os.path.join(base_dir, app_name)
    elif system == "Darwin":  # macOS
        # macOS: ~/Library/Application Support/VideoRobot
        base_dir = os.path.expanduser("~/Library/Application Support")
        app_dir = os.path.join(base_dir, app_name)
    else:  # Linux
        # Linux: ~/.local/share/VideoRobot
        base_dir = os.path.expanduser("~/.local/share")
        app_dir = os.path.join(base_dir, app_name)

    # 创建目录（如果不存在）
    if not os.path.exists(app_dir):
        os.makedirs(app_dir, exist_ok=True)

    return app_dir


def get_database_path():
    """获取数据库文件路径"""
    app_dir = get_app_data_dir()
    return os.path.join(app_dir, "video_robot.db")


def get_logs_dir():
    """获取日志目录"""
    app_dir = get_app_data_dir()
    logs_dir = os.path.join(app_dir, "logs")

    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)

    return logs_dir