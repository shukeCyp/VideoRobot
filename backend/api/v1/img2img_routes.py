# -*- coding: utf-8 -*-
"""
即梦图生图API路由
"""

import os
import json
import requests
import asyncio
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.models.models import JimengImg2ImgTask
import subprocess
import platform
import threading
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import uuid

# 创建蓝图
jimeng_img2img_bp = Blueprint('jimeng_img2img', __name__, url_prefix='/api/jimeng/img2img')

def allowed_file(filename):
    """检查文件类型是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@jimeng_img2img_bp.route('/tasks', methods=['GET'])
def get_img2img_tasks():
    """获取图生图任务列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        status = request.args.get('status', None)
        
        print("获取图生图任务列表，页码: {}, 每页数量: {}, 状态: {}".format(page, page_size, status))
        
        # 构建查询 - 过滤掉空任务
        query = JimengImg2ImgTask.select()
        if status is not None:
            query = query.where(JimengImg2ImgTask.status == status)
        
        # 分页
        total = query.count()
        tasks = query.order_by(JimengImg2ImgTask.create_at.desc()).paginate(page, page_size)
        
        data = []
        for task in tasks:
            input_images = task.get_input_images()
            output_images = task.get_images()
            
            data.append({
                'id': task.id,
                'prompt': task.prompt,
                'model': task.model,
                'ratio': task.ratio,
                'status': task.status,
                'status_text': task.get_status_text(),
                'account_id': task.account_id,
                'input_images': input_images,
                'output_images': output_images,
                'task_id': task.task_id,
                'retry_count': task.retry_count,
                'max_retry': task.max_retry,
                'failure_reason': task.failure_reason,
                'error_message': task.error_message,
                'create_at': task.create_at.strftime('%Y-%m-%d %H:%M:%S'),
                'update_at': task.update_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': data,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
        
    except Exception as e:
        print("获取任务列表失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '获取任务列表失败: {}'.format(str(e))
        }), 500

@jimeng_img2img_bp.route('/stats', methods=['GET'])
def get_img2img_stats():
    """获取图生图任务统计"""
    try:
        # 统计各状态的任务数量
        total = JimengImg2ImgTask.select().count()
        queued = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 0).count()
        processing = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 1).count()
        completed = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 2).count()
        failed = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 3).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'queued': queued,
                'processing': processing,
                'completed': completed,
                'failed': failed
            }
        })
        
    except Exception as e:
        print("获取统计信息失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '获取统计信息失败: {}'.format(str(e))
        }), 500

@jimeng_img2img_bp.route('/tasks', methods=['POST'])
def create_img2img_task():
    """创建图生图任务"""
    try:
        # 检查是否有文件上传
        if 'images' not in request.files:
            return jsonify({
                'success': False,
                'message': '请选择要上传的图片'
            }), 400
        
        files = request.files.getlist('images')
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                'success': False,
                'message': '请选择要上传的图片'
            }), 400
        
        # 检查文件格式
        for file in files:
            if file.filename != '' and not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'message': '不支持的图片格式，请上传PNG、JPG、JPEG、GIF、BMP或WebP格式的图片'
                }), 400
        
        # 获取表单数据
        prompt = request.form.get('prompt', '').strip()
        model = request.form.get('model', 'Nano Banana')
        aspect_ratio = request.form.get('aspect_ratio')
        # 如果用户没有选择比例或传递空字符串，则设置为None
        if not aspect_ratio or aspect_ratio.strip() == '':
            aspect_ratio = None
        
        # 验证图片数量
        valid_files = [f for f in files if f.filename != '']
        if model == 'Nano Banana':
            if len(valid_files) > 3:
                return jsonify({
                    'success': False,
                    'message': 'Nano Banana模型最多支持3张图片'
                }), 400
        else:
            if len(valid_files) > 1:
                return jsonify({
                    'success': False,
                    'message': f'{model}模型只支持1张图片'
                }), 400
        
        if not prompt:
            return jsonify({
                'success': False,
                'message': '请输入提示词'
            }), 400
        
        # 保存上传的图片
        saved_images = []
        tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        
        for file in files:
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
                file_path = os.path.join(tmp_dir, unique_filename)
                file.save(file_path)
                saved_images.append(file_path)
        
        # 创建任务
        task = JimengImg2ImgTask.create(
            prompt=prompt,
            model=model,
            ratio=aspect_ratio,
            status=0,  # 默认状态：0-排队中
            # 输出图片路径字段保持为空，由任务处理器填入
            image1=None,
            image2=None,
            image3=None,
            image4=None
        )
        
        # 设置输入图片
        task.set_input_images(saved_images)
        
        print("图生图任务创建成功，任务ID: {}".format(task.id))
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

@jimeng_img2img_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_img2img_task(task_id):
    """删除图生图任务"""
    try:
        task = JimengImg2ImgTask.get_by_id(task_id)
        
        # 删除输入图片文件
        input_images = task.get_input_images()
        for image_path in input_images:
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"删除输入图片文件: {image_path}")
                except Exception as e:
                    print(f"删除输入图片文件失败: {image_path}, 错误: {e}")
        
        # 删除输出图片文件
        output_images = task.get_images()
        for image_path in output_images:
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"删除输出图片文件: {image_path}")
                except Exception as e:
                    print(f"删除输出图片文件失败: {image_path}, 错误: {e}")
        
        task.delete_instance()
        
        return jsonify({
            'success': True,
            'message': '任务删除成功'
        })
        
    except JimengImg2ImgTask.DoesNotExist:
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

@jimeng_img2img_bp.route('/tasks/<int:task_id>/retry', methods=['POST'])
def retry_img2img_task(task_id):
    """重试图生图任务"""
    try:
        task = JimengImg2ImgTask.get_by_id(task_id)
        
        if task.can_retry():
            task.retry_task()
            return jsonify({
                'success': True,
                'message': '任务已重新排队'
            })
        else:
            return jsonify({
                'success': False,
                'message': '任务不能重试'
            }), 400
            
    except JimengImg2ImgTask.DoesNotExist:
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

@jimeng_img2img_bp.route('/tasks/batch-delete', methods=['POST'])
def batch_delete_img2img_tasks():
    """批量删除图生图任务"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return jsonify({
                'success': False,
                'message': '请选择要删除的任务'
            }), 400
        
        deleted_count = 0
        for task_id in task_ids:
            try:
                task = JimengImg2ImgTask.get_by_id(task_id)
                
                # 删除输入图片文件
                input_images = task.get_input_images()
                for image_path in input_images:
                    if image_path and os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            print(f"删除输入图片文件失败: {image_path}, 错误: {e}")
                
                # 删除输出图片文件
                output_images = task.get_images()
                for image_path in output_images:
                    if image_path and os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            print(f"删除输出图片文件失败: {image_path}, 错误: {e}")
                
                task.delete_instance()
                deleted_count += 1
                
            except JimengImg2ImgTask.DoesNotExist:
                continue
            except Exception as e:
                print(f"删除任务 {task_id} 失败: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'成功删除 {deleted_count} 个任务'
        })
        
    except Exception as e:
        print("批量删除任务失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '批量删除任务失败: {}'.format(str(e))
        }), 500

@jimeng_img2img_bp.route('/tasks/batch-download', methods=['POST'])
def batch_download_img2img_tasks():
    """批量下载图生图任务的生成图片"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return jsonify({
                'success': False,
                'message': '请选择要下载的任务'
            }), 400
        
        def select_folder_and_download():
            try:
                # 调用原生文件夹选择对话框
                folder_path = None
                system = platform.system()
                
                if system == "Darwin":  # macOS
                    result = subprocess.run([
                        'osascript', '-e',
                        'tell application "Finder" to set folder_path to (choose folder with prompt "选择图片保存文件夹") as string',
                        '-e',
                        'return POSIX path of folder_path'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        folder_path = result.stdout.strip()
                        
                elif system == "Windows":  # Windows
                    print("正在调用Windows文件选择器...")
                    ps_script = """
                    try {
                        Add-Type -AssemblyName System.Windows.Forms
                        $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
                        $folderBrowser.Description = "选择图片保存文件夹"
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
                        folder_path = result.stdout.strip()
                        print(f"用户选择了文件夹: {folder_path}")
                    elif result.returncode == 1:
                        print("用户取消了文件夹选择")
                        return
                        
                elif system == "Linux":  # Linux
                    result = subprocess.run([
                        'zenity', '--file-selection', '--directory',
                        '--title=选择图片保存文件夹'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        folder_path = result.stdout.strip()
                
                if not folder_path:
                    print("用户取消了文件夹选择")
                    return
                
                print(f"选择的保存文件夹: {folder_path}")
                
                if not os.path.exists(folder_path):
                    print(f"文件夹不存在: {folder_path}")
                    return
                
                # 获取要下载的任务
                tasks = JimengImg2ImgTask.select().where(
                    JimengImg2ImgTask.id.in_(task_ids),
                    JimengImg2ImgTask.status == 2  # 已完成
                )
                
                # 准备下载信息
                file_infos = []
                for task in tasks:
                    images = task.get_images()
                    for i, image_url in enumerate(images):
                        if image_url and image_url.strip():
                            # 生成文件名，从URL获取文件扩展名
                            if image_url.endswith('.png'):
                                ext = 'png'
                            elif image_url.endswith('.jpg') or image_url.endswith('.jpeg'):
                                ext = 'jpg'
                            else:
                                ext = 'png'  # 默认为png
                            filename = f"img2img_task_{task.id}_{i+1}.{ext}"
                            file_infos.append({
                                'url': image_url,
                                'filename': filename
                            })
                
                if not file_infos:
                    print("没有找到可下载的图片")
                    return
                
                # 创建批量下载文件夹
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                batch_folder = os.path.join(folder_path, f"jimeng_img2img_{timestamp}")
                os.makedirs(batch_folder, exist_ok=True)
                
                # 下载文件
                success_count = 0
                for file_info in file_infos:
                    try:
                        # 下载图片
                        response = requests.get(file_info['url'], timeout=30)
                        response.raise_for_status()
                        
                        # 保存文件
                        dest_path = os.path.join(batch_folder, file_info['filename'])
                        with open(dest_path, 'wb') as f:
                            f.write(response.content)
                        
                        success_count += 1
                        print(f"下载文件: {file_info['filename']}")
                    except Exception as e:
                        print(f"下载文件失败: {file_info['filename']}, 错误: {e}")
                
                print(f"批量下载完成，成功下载 {success_count} 个文件到: {batch_folder}")
                
            except Exception as e:
                print(f"批量下载过程中出错: {e}")
        
        # 在后台线程中执行下载
        thread = threading.Thread(target=select_folder_and_download)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '正在选择下载文件夹...'
        })
        
    except Exception as e:
        print("批量下载失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '批量下载失败: {}'.format(str(e))
        }), 500 