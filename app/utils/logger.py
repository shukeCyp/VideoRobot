# -*- coding: utf-8 -*-
import sys
from loguru import logger
from app.utils.path_helper import get_logs_dir
import os


def setup_logger():
    """配置日志系统"""
    # 移除默认的日志处理器
    logger.remove()

    # 添加控制台输出（彩色）
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG"
    )

    # 获取日志目录
    logs_dir = get_logs_dir()

    # 添加文件输出（普通日志）
    logger.add(
        os.path.join(logs_dir, "video_robot_{time:YYYY-MM-DD}.log"),
        rotation="00:00",  # 每天午夜轮换
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )

    # 添加错误日志文件
    logger.add(
        os.path.join(logs_dir, "error_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention="60 days",  # 错误日志保留60天
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR"
    )

    logger.info(f"日志系统初始化完成，日志目录: {logs_dir}")

    return logger


# 导出logger实例
log = setup_logger()