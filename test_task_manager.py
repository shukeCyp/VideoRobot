#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器测试脚本

测试即梦图片任务的扫描和执行功能

使用方法:
    python test_task_manager.py --create-task  # 创建测试任务
    python test_task_manager.py --run-manager  # 启动任务管理器
"""
import sys
import os
import time
import argparse

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.models.jimeng_image_task import JimengImageTask
from app.models.jimeng_account import JimengAccount
from app.managers.global_task_manager import get_global_task_manager
from app.utils.logger import log
from app.database.init_db import init_database


def create_test_task():
    """创建测试任务"""
    log.info("="*60)
    log.info("创建测试任务")
    log.info("="*60)

    # 获取第一个账号
    accounts = JimengAccount.get_all_accounts()

    if not accounts:
        log.error("❌ 没有可用的即梦账号,请先添加账号")
        return False

    account = list(accounts)[0]
    log.info(f"使用账号: {account.nickname} (ID: {account.id})")

    # 创建测试任务
    task = JimengImageTask.create_task(
        prompt="一只可爱的小猫坐在窗台上,阳光洒在它身上,温暖而治愈",
        account_id=account.id,
        image_model="",
        aspect_ratio="1:1",
        resolution="高清 2K"
    )

    log.info(f"✅ 测试任务创建成功!")
    log.info(f"   任务ID: {task.id}")
    log.info(f"   提示词: {task.prompt}")
    log.info(f"   状态: {task.status}")
    log.info("="*60)

    return True


def run_task_manager():
    """运行任务管理器"""
    log.info("="*60)
    log.info("启动任务管理器")
    log.info("="*60)

    # 获取任务管理器
    manager = get_global_task_manager()

    # 设置参数
    manager.set_max_workers(1)  # 测试时使用单线程
    manager.set_poll_interval(5)  # 5秒轮询一次

    # 连接信号
    def on_task_started(task_type, task_id):
        log.info(f"📋 任务开始: {task_type} - ID={task_id}")

    def on_task_finished(task_type, task_id, success):
        status = "✅ 成功" if success else "❌ 失败"
        log.info(f"📋 任务完成: {task_type} - ID={task_id} - {status}")

    def on_status_changed(message):
        log.info(f"💡 状态变更: {message}")

    manager.task_started.connect(on_task_started)
    manager.task_finished.connect(on_task_finished)
    manager.status_changed.connect(on_status_changed)

    # 启动管理器
    log.info("启动任务管理器...")
    manager.start()

    try:
        # 等待任务执行
        log.info("任务管理器正在运行,按 Ctrl+C 停止...")
        while manager.isRunning():
            time.sleep(1)

    except KeyboardInterrupt:
        log.info("\n收到停止信号")

    finally:
        # 停止管理器
        log.info("停止任务管理器...")
        manager.stop()
        manager.wait()
        log.info("任务管理器已停止")

    log.info("="*60)


def show_pending_tasks():
    """显示待执行的任务"""
    log.info("="*60)
    log.info("待执行任务列表")
    log.info("="*60)

    tasks = JimengImageTask.select().where(
        JimengImageTask.status == 'pending'
    ).order_by(JimengImageTask.created_at.asc())

    task_list = list(tasks)

    if not task_list:
        log.info("没有待执行的任务")
    else:
        for i, task in enumerate(task_list, 1):
            log.info(f"{i}. ID={task.id}, 提示词: {task.prompt[:50]}...")
            log.info(f"   账号ID: {task.account_id}, 状态: {task.status}")
            log.info(f"   创建时间: {task.created_at}")

    log.info("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='任务管理器测试工具')
    parser.add_argument('--create-task', action='store_true', help='创建测试任务')
    parser.add_argument('--run-manager', action='store_true', help='运行任务管理器')
    parser.add_argument('--show-tasks', action='store_true', help='显示待执行任务')

    args = parser.parse_args()

    # 初始化数据库
    init_database()

    if args.create_task:
        create_test_task()
    elif args.run_manager:
        run_task_manager()
    elif args.show_tasks:
        show_pending_tasks()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
