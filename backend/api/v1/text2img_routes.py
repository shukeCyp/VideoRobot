# -*- coding: utf-8 -*-
"""
即梦文生图API路由
"""

import os
import json
import requests
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.models.models import JimengText2ImgTask
import subprocess
import platform
import threading
from urllib.parse import urlparse

# 创建蓝图
jimeng_text2img_bp = Blueprint('jimeng_text2img', __name__, url_prefix='/api/jimeng/text2img')

@jimeng_text2img_bp.route('/tasks', methods=['GET'])
def get_text2img_tasks():
    """获取文生图任务列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        status = request.args.get('status', None)
        
        print("获取文生图任务列表，页码: {}, 每页数量: {}, 状态: {}".format(page, page_size, status))
        
        # 构建查询 - 过滤掉空任务
        query = JimengText2ImgTask.select()
        if status is not None:
            query = query.where(JimengText2ImgTask.status == status)
        
        # 分页
        total = query.count()
        tasks = query.order_by(JimengText2ImgTask.create_at.desc()).paginate(page, page_size)
        
        data = []
        for task in tasks:
            images = task.get_images()  # 获取所有图片路径
            data.append({
                'id': task.id,
                'prompt': task.prompt,
                'model': task.model,
                'ratio': task.ratio,
                'quality': task.quality,
                'status': task.status,
                'status_text': task.get_status_text(),
                'account_id': task.account_id,
                'images': images,  # 图片路径列表
                'image_count': len(images),  # 图片数量
                'failure_reason': task.failure_reason,  # 失败原因类型
                'error_message': task.error_message,  # 详细错误信息
                'create_at': task.create_at.strftime('%Y-%m-%d %H:%M:%S'),
                'update_at': task.update_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        print("成功获取任务列表，总数: {}, 当前页任务数: {}".format(total, len(data)))
        return jsonify({
            'success': True,
            'data': data,
            'pagination': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        })
        
    except Exception as e:
        print("获取任务列表失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '获取任务列表失败: {}'.format(str(e))
        }), 500

@jimeng_text2img_bp.route('/tasks', methods=['POST'])
def create_text2img_task():
    """创建文生图任务"""
    try:
        data = request.get_json()
        print("创建新的文生图任务: {}".format(data.get('prompt', '')[:50]))
        
        # 验证必要字段
        required_fields = ['prompt', 'model', 'aspect_ratio', 'quality']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段: {}'.format(field)
                }), 400
        
        # 创建任务（不包含图片路径，这些在任务完成后才填入）
        task = JimengText2ImgTask.create(
            prompt=data['prompt'],
            model=data['model'],
            ratio=data['aspect_ratio'],  # 字段名映射
            quality=data['quality'],
            account_id=data.get('account_id'),
            status=0,  # 默认状态：0-排队中
            # 图片路径字段保持为空，由任务处理器填入
            image1=None,
            image2=None,
            image3=None,
            image4=None
        )
        
        print("任务创建成功，任务ID: {}".format(task.id))
        return jsonify({
            'success': True,
            'data': {
                'id': task.id,
                'status': task.status,
                'status_text': task.get_status_text(),
                'create_at': task.create_at.strftime('%Y-%m-%d %H:%M:%S')
            },
            'message': '任务创建成功'
        })
        
    except Exception as e:
        print("创建任务失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '创建任务失败: {}'.format(str(e))
        }), 500

@jimeng_text2img_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_text2img_task(task_id):
    """删除文生图任务"""
    try:
        task = JimengText2ImgTask.get(JimengText2ImgTask.id == task_id)
        task_prompt = task.prompt[:50] + '...' if len(task.prompt) > 50 else task.prompt
        task.delete_instance()
        
        print("删除任务成功: {}".format(task_prompt))
        return jsonify({
            'success': True,
            'message': '已删除任务: {}'.format(task_prompt)
        })
        
    except JimengText2ImgTask.DoesNotExist:
        print("删除失败：任务不存在，ID: {}".format(task_id))
        return jsonify({
            'success': False,
            'message': '任务不存在'
        }), 404
    except Exception as e:
        print("删除任务失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '删除任务失败: {}'.format(str(e))
        }), 500

@jimeng_text2img_bp.route('/tasks/<int:task_id>/retry', methods=['POST'])
def retry_text2img_task(task_id):
    """重试文生图任务"""
    try:
        task = JimengText2ImgTask.get_by_id(task_id)
        task.status = 0  # 重置为排队状态
        task.save()
        
        print("重试文生图任务: {}".format(task_id))
        return jsonify({
            'success': True,
            'message': '任务已重新加入队列'
        })
        
    except JimengText2ImgTask.DoesNotExist:
        return jsonify({
            'success': False,
            'message': '任务不存在'
        }), 404
    except Exception as e:
        print("重试任务失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '重试任务失败: {}'.format(str(e))
        }), 500

@jimeng_text2img_bp.route('/tasks/batch-retry', methods=['POST'])
def batch_retry_text2img_tasks():
    """批量重试失败的文生图任务"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if task_ids:
            # 如果提供了特定的任务ID列表，只重试这些任务
            retry_count = JimengText2ImgTask.update(status=0).where(
                JimengText2ImgTask.id.in_(task_ids),
                JimengText2ImgTask.status == 3  # 只重试失败的任务
            ).execute()
        else:
            # 如果没有提供任务ID，重试所有失败的任务
            retry_count = JimengText2ImgTask.update(status=0).where(
                JimengText2ImgTask.status == 3  # 只重试失败的任务
            ).execute()
        
        print(f"批量重试文生图任务: {retry_count}个")
        return jsonify({
            'success': True,
            'message': f'已重新加入队列 {retry_count} 个任务',
            'data': {
                'retry_count': retry_count
            }
        })
        
    except Exception as e:
        print(f"批量重试文生图任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量重试失败: {str(e)}'
        }), 500

@jimeng_text2img_bp.route('/stats', methods=['GET'])
def get_text2img_stats():
    """获取文生图任务统计信息"""
    try:
        # 统计时过滤掉空任务
        base_query = JimengText2ImgTask.select()
        total_tasks = base_query.count()
        queued_tasks = base_query.where(JimengText2ImgTask.status == 0).count()  # 排队中
        processing_tasks = base_query.where(JimengText2ImgTask.status == 1).count()  # 生成中
        completed_tasks = base_query.where(JimengText2ImgTask.status == 2).count()  # 已完成
        failed_tasks = base_query.where(JimengText2ImgTask.status == 3).count()  # 失败
        
        print("获取任务统计 - 总数:{}, 排队:{}, 处理中:{}, 已完成:{}, 失败:{}".format(
            total_tasks, queued_tasks, processing_tasks, completed_tasks, failed_tasks))
        
        return jsonify({
            'success': True,
            'data': {
                'total': total_tasks,
                'queued': queued_tasks,
                'processing': processing_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks
            },
            'message': '统计信息获取成功'
        })
        
    except Exception as e:
        print("获取统计信息失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '获取统计信息失败: {}'.format(str(e))
        }), 500

@jimeng_text2img_bp.route('/tasks/batch-delete', methods=['POST'])
def batch_delete_text2img_tasks():
    """批量删除文生图任务"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return jsonify({
                'success': False,
                'message': '未提供任务ID'
            }), 400
        
        # 删除任务
        deleted_count = JimengText2ImgTask.delete().where(JimengText2ImgTask.id.in_(task_ids)).execute()
        
        print(f"批量删除文生图任务: {deleted_count}个")
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个任务'
        })
        
    except Exception as e:
        print(f"批量删除文生图任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量删除失败: {str(e)}'
        }), 500

@jimeng_text2img_bp.route('/tasks/batch-download', methods=['POST'])
def batch_download_images():
    """批量下载任务图片"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return jsonify({
                'success': False,
                'message': '请提供要下载的任务ID列表'
            }), 400
        
        # 获取任务信息
        tasks = list(JimengText2ImgTask.select().where(
            JimengText2ImgTask.id.in_(task_ids),
            JimengText2ImgTask.status == 2  # 只下载已完成的任务
        ))
        
        if not tasks:
            return jsonify({
                'success': False,
                'message': '没有找到可下载的已完成任务'
            }), 400
        
        # 收集所有图片URL
        all_images = []
        for task in tasks:
            images = task.get_images()
            for i, img_url in enumerate(images):
                if img_url:
                    all_images.append({
                        'task_id': task.id,
                        'image_index': i + 1,
                        'url': img_url,
                        'filename': f'task_{task.id}_image_{i + 1}.jpg'
                    })
        
        if not all_images:
            return jsonify({
                'success': False,
                'message': '选中的任务没有图片可下载'
            }), 400
        
        # 在后台线程中选择文件夹并下载
        def download_in_background():
            try:
                # 使用系统原生对话框选择文件夹
                download_dir = None
                system = platform.system()
                
                if system == "Darwin":  # macOS
                    try:
                        print("正在调用macOS文件选择器...")
                        # 使用osascript调用macOS原生文件选择器
                        applescript = '''
                        tell application "Finder"
                            activate
                            set selectedFolder to choose folder with prompt "选择图片下载文件夹" default location (path to downloads folder)
                            return POSIX path of selectedFolder
                        end tell
                        '''
                        result = subprocess.run([
                            'osascript', '-e', applescript
                        ], capture_output=True, text=True, timeout=60)
                        
                        print(f"文件选择器返回码: {result.returncode}")
                        print(f"文件选择器输出: {result.stdout}")
                        print(f"文件选择器错误: {result.stderr}")
                        
                        if result.returncode == 0 and result.stdout.strip():
                            download_dir = result.stdout.strip()
                            print(f"用户选择了文件夹: {download_dir}")
                        elif result.returncode == 1:
                            print("用户取消了文件夹选择")
                            return
                        else:
                            print(f"文件选择器异常退出，返回码: {result.returncode}")
                    except subprocess.TimeoutExpired:
                        print("文件选择器超时，用户可能没有响应")
                        return
                    except Exception as e:
                        print(f"macOS文件选择器失败: {str(e)}")
                        
                elif system == "Windows":  # Windows
                    try:
                        print("正在调用Windows文件选择器...")
                        # 使用PowerShell调用Windows文件选择器，添加更详细的错误处理
                        ps_script = """
                        try {
                            Add-Type -AssemblyName System.Windows.Forms
                            $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
                            $folderBrowser.Description = "选择图片下载文件夹"
                            $folderBrowser.SelectedPath = [Environment]::GetFolderPath("MyDocuments")
                            $folderBrowser.ShowNewFolderButton = $true
                            $result = $folderBrowser.ShowDialog()
                            if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
                                Write-Output $folderBrowser.SelectedPath
                                exit 0
                            } else {
                                Write-Output "CANCELLED"
                                exit 1
                            }
                        } catch {
                            Write-Error $_.Exception.Message
                            exit 2
                        }
                        """
                        result = subprocess.run([
                            'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
                        ], capture_output=True, text=True, timeout=60, encoding='utf-8')
                        
                        print(f"PowerShell返回码: {result.returncode}")
                        print(f"PowerShell输出: {result.stdout}")
                        print(f"PowerShell错误: {result.stderr}")
                        
                        if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "CANCELLED":
                            download_dir = result.stdout.strip()
                            print(f"用户选择了文件夹: {download_dir}")
                        elif result.returncode == 1:
                            print("用户取消了文件夹选择")
                            return
                        else:
                            print(f"PowerShell执行失败，返回码: {result.returncode}")
                    except subprocess.TimeoutExpired:
                        print("Windows文件选择器超时，用户可能没有响应")
                        return
                    except Exception as e:
                        print(f"Windows文件选择器失败: {str(e)}")
                        
                else:  # Linux
                    try:
                        # 尝试使用zenity
                        result = subprocess.run([
                            'zenity', '--file-selection', '--directory', 
                            '--title=选择图片下载文件夹'
                        ], capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            download_dir = result.stdout.strip()
                    except Exception as e:
                        print(f"Linux文件选择器失败: {str(e)}")
                
                # 如果原生对话框失败，使用默认下载目录
                if not download_dir:
                    download_dir = os.path.expanduser("~/Downloads")
                    print(f"文件选择器失败，使用默认下载目录: {download_dir}")
                
                # 确保目录存在
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir, exist_ok=True)
                
                print(f"开始下载 {len(all_images)} 张图片到: {download_dir}")
                
                # 创建以当前时间命名的子文件夹
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                batch_folder = os.path.join(download_dir, f"jimeng_images_{timestamp}")
                os.makedirs(batch_folder, exist_ok=True)
                
                # 准备下载信息
                file_infos = []
                for img_info in all_images:
                    file_infos.append({
                        'url': img_info['url'],
                        'file_path': os.path.join(batch_folder, img_info['filename']),
                        'filename': img_info['filename']
                    })
                
                # 使用带重试机制的批量下载
                from utils.download_util import batch_download_files
                download_result = batch_download_files(
                    file_infos=file_infos,
                    max_retries=5,
                    delay_between_downloads=1.0,
                    timeout=30
                )
                
                success_count = download_result['success_count']
                error_count = download_result['failed_count']
                
                print(f"批量下载完成: 成功 {success_count} 张，失败 {error_count} 张")
                print(f"文件保存位置: {batch_folder}")
                
            except Exception as e:
                print(f"批量下载过程出错: {str(e)}")
        
        # 在后台线程中执行下载
        download_thread = threading.Thread(target=download_in_background)
        download_thread.daemon = True
        download_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'开始下载 {len(all_images)} 张图片，请选择下载文件夹',
            'data': {
                'total_images': len(all_images),
                'tasks_count': len(tasks)
            }
        })
        
    except Exception as e:
        print(f"批量下载失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量下载失败: {str(e)}'
        }), 500

@jimeng_text2img_bp.route('/tasks/batch-download-v2', methods=['POST'])
def batch_download_images_v2():
    """批量下载任务图片v2 - 为每个任务创建单独文件夹"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])

        if not task_ids:
            return jsonify({
                'success': False,
                'message': '请提供要下载的任务ID列表'
            }), 400

        # 获取任务信息
        tasks = list(JimengText2ImgTask.select().where(
            JimengText2ImgTask.id.in_(task_ids),
            JimengText2ImgTask.status == 2  # 只下载已完成的任务
        ))

        if not tasks:
            return jsonify({
                'success': False,
                'message': '没有找到可下载的已完成任务'
            }), 400

        # 在后台线程中选择文件夹并下载
        def download_in_background():
            try:
                # 使用系统原生对话框选择文件夹
                download_dir = None
                system = platform.system()

                if system == "Darwin":  # macOS
                    try:
                        print("正在调用macOS文件选择器...")
                        # 使用osascript调用macOS原生文件选择器
                        applescript = '''
                        tell application "Finder"
                            activate
                            set selectedFolder to choose folder with prompt "选择批量下载文件夹" default location (path to downloads folder)
                            return POSIX path of selectedFolder
                        end tell
                        '''
                        result = subprocess.run([
                            'osascript', '-e', applescript
                        ], capture_output=True, text=True, timeout=60)

                        if result.returncode == 0 and result.stdout.strip():
                            download_dir = result.stdout.strip()
                            print(f"用户选择了文件夹: {download_dir}")
                        elif result.returncode == 1:
                            print("用户取消了文件夹选择")
                            return
                        else:
                            print(f"文件选择器异常退出，返回码: {result.returncode}")
                    except subprocess.TimeoutExpired:
                        print("文件选择器超时，用户可能没有响应")
                        return
                    except Exception as e:
                        print(f"macOS文件选择器失败: {str(e)}")

                elif system == "Windows":  # Windows
                    try:
                        print("正在调用Windows文件选择器...")
                        # 使用PowerShell调用Windows文件选择器
                        ps_script = """
                        try {
                            Add-Type -AssemblyName System.Windows.Forms
                            $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
                            $folderBrowser.Description = "选择批量下载文件夹"
                            $folderBrowser.SelectedPath = [Environment]::GetFolderPath("MyDocuments")
                            $folderBrowser.ShowNewFolderButton = $true
                            $result = $folderBrowser.ShowDialog()
                            if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
                                Write-Output $folderBrowser.SelectedPath
                                exit 0
                            } else {
                                Write-Output "CANCELLED"
                                exit 1
                            }
                        } catch {
                            Write-Error $_.Exception.Message
                            exit 2
                        }
                        """
                        result = subprocess.run([
                            'powershell', '-ExecutionPolicy', 'Bypass', '-Command', ps_script
                        ], capture_output=True, text=True, timeout=60, encoding='utf-8')

                        if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "CANCELLED":
                            download_dir = result.stdout.strip()
                            print(f"用户选择了文件夹: {download_dir}")
                        elif result.returncode == 1:
                            print("用户取消了文件夹选择")
                            return
                        else:
                            print(f"PowerShell执行失败，返回码: {result.returncode}")
                    except subprocess.TimeoutExpired:
                        print("Windows文件选择器超时，用户可能没有响应")
                        return
                    except Exception as e:
                        print(f"Windows文件选择器失败: {str(e)}")

                else:  # Linux
                    try:
                        # 尝试使用zenity
                        result = subprocess.run([
                            'zenity', '--file-selection', '--directory',
                            '--title=选择批量下载文件夹'
                        ], capture_output=True, text=True, timeout=30)

                        if result.returncode == 0:
                            download_dir = result.stdout.strip()
                    except Exception as e:
                        print(f"Linux文件选择器失败: {str(e)}")

                # 如果原生对话框失败，使用默认下载目录
                if not download_dir:
                    download_dir = os.path.expanduser("~/Downloads")
                    print(f"文件选择器失败，使用默认下载目录: {download_dir}")

                # 确保目录存在
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir, exist_ok=True)

                print(f"开始批量下载 {len(tasks)} 个任务到: {download_dir}")

                # 在选择的路径下创建时间日期文件夹
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                batch_folder = os.path.join(download_dir, f"批量下载_{timestamp}")
                os.makedirs(batch_folder, exist_ok=True)
                print(f"创建批量下载文件夹: {batch_folder}")

                total_success = 0
                total_failed = 0

                # 为每个任务创建单独文件夹
                for task in tasks:
                    try:
                        # 获取提示词并处理文件夹名称
                        prompt = task.prompt or f"task_{task.id}"

                        # 适配中英文冒号，根据中英文冒号分割提示词，取后面的部分作为文件夹名
                        if ':' in prompt or '：' in prompt:
                            # 优先使用英文冒号，如果没有则使用中文冒号
                            if ':' in prompt:
                                folder_name = prompt.split(':', 1)[1].strip()
                            else:
                                folder_name = prompt.split('：', 1)[1].strip()
                        else:
                            # 如果没有中英文冒号，使用前20个字符作为文件夹名
                            folder_name = prompt[:20].strip()

                        # 清理文件夹名，移除不支持的字符
                        import re
                        folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
                        folder_name = folder_name.strip()

                        # 如果文件夹名为空，使用默认名称
                        if not folder_name:
                            folder_name = f"task_{task.id}"

                        # 创建任务文件夹
                        task_folder = os.path.join(batch_folder, folder_name)
                        os.makedirs(task_folder, exist_ok=True)

                        # 获取图片并下载
                        images = task.get_images()
                        if images:
                            # 准备下载信息
                            file_infos = []
                            for i, img_url in enumerate(images):
                                if img_url:
                                    # 图片命名规范：文件夹名称_序号
                                    filename = f"{folder_name}_{i+1}.jpg"
                                    file_path = os.path.join(task_folder, filename)
                                    file_infos.append({
                                        'url': img_url,
                                        'file_path': file_path,
                                        'filename': filename
                                    })

                            # 下载图片
                            if file_infos:
                                from utils.download_util import batch_download_files
                                download_result = batch_download_files(
                                    file_infos=file_infos,
                                    max_retries=3,
                                    delay_between_downloads=0.5,
                                    timeout=30
                                )

                                total_success += download_result['success_count']
                                total_failed += download_result['failed_count']

                                print(f"任务 {task.id} 下载完成: 成功 {download_result['success_count']} 张，失败 {download_result['failed_count']} 张")
                                print(f"文件夹: {task_folder}")
                            else:
                                print(f"任务 {task.id} 没有有效图片")
                        else:
                            print(f"任务 {task.id} 没有图片")

                    except Exception as e:
                        print(f"处理任务 {task.id} 时出错: {str(e)}")
                        total_failed += 1

                print(f"批量下载v2完成: 总共成功 {total_success} 张图片，失败 {total_failed} 张")
                print(f"文件保存位置: {download_dir}")

            except Exception as e:
                print(f"批量下载v2过程出错: {str(e)}")

        # 在后台线程中执行下载
        download_thread = threading.Thread(target=download_in_background)
        download_thread.daemon = True
        download_thread.start()

        return jsonify({
            'success': True,
            'message': f'开始批量下载 {len(tasks)} 个任务，将在选择的路径下创建时间文件夹，每个任务一个子文件夹',
            'data': {
                'tasks_count': len(tasks)
            }
        })

    except Exception as e:
        print(f"批量下载v2失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量下载v2失败: {str(e)}'
        }), 500

@jimeng_text2img_bp.route('/tasks/delete-before-today', methods=['DELETE'])
def delete_tasks_before_today():
    """删除今日前的所有文生图任务"""
    try:
        from datetime import datetime, timedelta
        import pytz

        # 获取今日开始时间（凌晨0点）
        beijing_tz = pytz.timezone('Asia/Shanghai')
        today_start = datetime.now(beijing_tz).replace(hour=0, minute=0, second=0, microsecond=0)

        # 查询今日前的任务
        before_today_tasks = JimengText2ImgTask.select().where(
            JimengText2ImgTask.create_at < today_start
        )

        count = before_today_tasks.count()

        if count == 0:
            return jsonify({
                'success': True,
                'message': '没有今日前的任务需要删除',
                'data': {'deleted_count': 0}
            })

        # 删除任务
        deleted_count = JimengText2ImgTask.delete().where(
            JimengText2ImgTask.create_at < today_start
        ).execute()

        print(f"删除了 {deleted_count} 个今日前的文生图任务")

        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个今日前的任务',
            'data': {'deleted_count': deleted_count}
        })

    except Exception as e:
        print(f"删除今日前任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除今日前任务失败: {str(e)}'
        }), 500

