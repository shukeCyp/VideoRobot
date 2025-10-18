#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request
from flask_cors import CORS
import time
import threading
from datetime import datetime

# 导入核心模块
from backend.core.database import init_database
from backend.core.middleware import before_request, after_request
from backend.core.global_task_manager import global_task_manager
from backend.models.models import JimengAccount, JimengText2ImgTask, JimengImg2ImgTask, JimengImg2VideoTask, JimengDigitalHumanTask, QingyingImage2VideoTask
from backend.utils.config_util import ConfigUtil
# from backend.utils.retry_util import start_auto_retry_scheduler  # 暂时注释掉

# 导入路由蓝图
from backend.api.v1.common_routes import common_bp
from backend.api.v1.accounts_routes import jimeng_accounts_bp
from backend.api.v1.qingying_accounts_routes import qingying_accounts_bp
from backend.api.v1.text2img_routes import jimeng_text2img_bp
from backend.api.v1.img2img_routes import jimeng_img2img_bp
from backend.api.v1.img2video_routes import jimeng_img2video_bp
from backend.api.v1.digital_human_routes import jimeng_digital_human_bp
from backend.api.v1.qingying_img2video_routes import qingying_img2video_bp
from backend.api.v1.config_routes import config_bp
from backend.api.v1.task_manager_routes import task_manager_bp
from backend.api.v1.prompt_routes import prompt_bp

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 注册中间件
app.before_request(before_request)
app.after_request(after_request)

# 初始化数据库
init_database()

# 等待数据库初始化完全完成
time.sleep(0.5)

# 初始化默认配置
ConfigUtil.init_default_configs()

def reset_processing_tasks():
    """重置所有生成中的任务为排队状态"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            print("检查并重置生成中的任务...")
            
            # 重置文生图任务
            text2img_reset_count = 0
            processing_text2img_tasks = JimengText2ImgTask.select().where(
                JimengText2ImgTask.status == 1  # 生成中
            )
            
            for task in processing_text2img_tasks:
                task.update_status(0)  # 重置为排队状态
                text2img_reset_count += 1
            
            # 重置图生图任务
            img2img_reset_count = 0
            processing_img2img_tasks = JimengImg2ImgTask.select().where(
                JimengImg2ImgTask.status == 1  # 生成中
            )
            
            for task in processing_img2img_tasks:
                task.update_status(0)  # 重置为排队状态
                img2img_reset_count += 1
            
            # 重置图生视频任务
            img2video_reset_count = 0
            processing_img2video_tasks = JimengImg2VideoTask.select().where(
                JimengImg2VideoTask.status == 1  # 生成中
            )
            
            for task in processing_img2video_tasks:
                task.update_status(0)  # 重置为排队状态
                img2video_reset_count += 1
            
            # 重置数字人任务
            digital_human_reset_count = 0
            processing_digital_human_tasks = JimengDigitalHumanTask.select().where(
                JimengDigitalHumanTask.status == 1  # 生成中
            )
            
            for task in processing_digital_human_tasks:
                task.update_status(0)  # 重置为排队状态
                digital_human_reset_count += 1
            
            # 重置清影图生视频任务
            qingying_img2video_reset_count = 0
            processing_qingying_img2video_tasks = QingyingImage2VideoTask.select().where(
                QingyingImage2VideoTask.status == 1  # 生成中
            )
            
            for task in processing_qingying_img2video_tasks:
                task.update_status(0)  # 重置为排队状态
                qingying_img2video_reset_count += 1
            
            total_reset = text2img_reset_count + img2img_reset_count + img2video_reset_count + digital_human_reset_count + qingying_img2video_reset_count
            if total_reset > 0:
                print(f"重置了 {text2img_reset_count} 个文生图任务, {img2img_reset_count} 个图生图任务, {img2video_reset_count} 个图生视频任务, {digital_human_reset_count} 个数字人任务和 {qingying_img2video_reset_count} 个清影图生视频任务为排队状态")
            else:
                print("没有需要重置的生成中任务")
            
            return  # 成功完成，退出重试循环
                
        except Exception as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"数据库被锁定，重置任务第 {attempt + 1} 次重试，等待 {retry_delay} 秒...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                print(f"重置生成中任务失败: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"第 {attempt + 1} 次重试，等待 {retry_delay} 秒...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    print("重置任务失败，但继续启动服务...")
                    break

# 在启动任务管理器之前重置任务状态
reset_processing_tasks()

# 等待任务重置完成
time.sleep(1.0)

# 注册蓝图路由
app.register_blueprint(common_bp)
app.register_blueprint(jimeng_accounts_bp)
app.register_blueprint(qingying_accounts_bp)
app.register_blueprint(jimeng_text2img_bp)
app.register_blueprint(jimeng_img2img_bp)
app.register_blueprint(jimeng_img2video_bp)
app.register_blueprint(jimeng_digital_human_bp)
app.register_blueprint(qingying_img2video_bp)
app.register_blueprint(config_bp)
app.register_blueprint(task_manager_bp)
app.register_blueprint(prompt_bp)

# 等待路由注册完成
time.sleep(0.5)

# 启动全局任务管理器
global_task_manager.start()
print("全局任务管理器已启动")

# 启动自动重试调度器
    # start_auto_retry_scheduler()  # 暂时注释掉
print("自动重试调度器已启动")

if __name__ == '__main__':
    print("VideoRobot后端服务启动中...")
    print("数据库连接成功")
    print("API服务运行在: http://localhost:8888")
    print("可用路由:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            print("  {} [{}]".format(rule.rule, methods))
    app.run(debug=False, host='0.0.0.0', port=8888)