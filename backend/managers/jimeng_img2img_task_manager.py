# -*- coding: utf-8 -*-
"""
即梦图生图任务管理器 - 管理即梦图生图任务状态并执行任务
"""

import threading
import time
import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.models.models import JimengImg2ImgTask, JimengAccount
from backend.utils.jimeng_img2img import JimengImg2ImgExecutor
from backend.utils.config_util import get_automation_max_threads, get_hide_window
from backend.config.settings import TASK_PROCESSOR_INTERVAL, TASK_PROCESSOR_ERROR_WAIT

def run_async_safe(coro):
    """安全地运行异步协程，处理事件循环冲突"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，在新线程中创建新的事件循环
            import threading
            result = None
            exception = None
            
            def run_in_thread():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(coro)
                    new_loop.close()
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
            return result
        else:
            return asyncio.run(coro)
    except RuntimeError:
        # 如果没有事件循环，直接使用 asyncio.run
        return asyncio.run(coro)

class TaskManagerStatus(Enum):
    """任务管理器状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class JimengImg2ImgTaskManager:
    """即梦图生图任务管理器"""
    
    def __init__(self):
        self.status = TaskManagerStatus.STOPPED
        self.thread = None
        self.executor = None
        self.max_threads = 1  # 默认线程数
        self.active_tasks = {}  # 存储正在执行的任务信息 {thread_id: task_info}
        self._task_id_counter = 0  # 用于分配线程ID
        
        # 统计信息
        self.stats = {
            'start_time': None,
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'last_task_time': None
        }
        
        # 锁对象
        self.stats_lock = threading.Lock()
        self.tasks_lock = threading.Lock()
        
        # 全局线程池引用（用于兼容全局任务管理器）
        self.global_executor = None
    
    def set_global_executor(self, executor):
        """设置全局线程池（兼容全局任务管理器）"""
        self.global_executor = executor
        print("即梦图生图已设置全局线程池")
    
    def start(self):
        """启动任务管理器"""
        if self.status == TaskManagerStatus.RUNNING:
            print("即梦图生图任务管理器已在运行中")
            return False
        
        self.status = TaskManagerStatus.RUNNING
        self.stats['start_time'] = datetime.now()
        self.max_threads = get_automation_max_threads()
        
        # 创建线程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_threads, thread_name_prefix="JimengImg2Img")
        
        # 启动主循环线程
        self.thread = threading.Thread(target=self._task_loop, daemon=True)
        self.thread.start()
        
        print(f"即梦图生图任务管理器已启动，最大线程数: {self.max_threads}")
        return True
    
    def stop(self):
        """停止任务管理器"""
        if self.status == TaskManagerStatus.STOPPED:
            print("即梦图生图任务管理器已停止")
            return False
        
        print("正在停止即梦图生图任务管理器...")
        self.status = TaskManagerStatus.STOPPED
        
        # 关闭线程池
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        
        # 等待主线程结束
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        print("即梦图生图任务管理器已停止")
        return True
    
    def pause(self):
        """暂停任务管理器"""
        if self.status == TaskManagerStatus.RUNNING:
            self.status = TaskManagerStatus.PAUSED
            print("即梦图生图任务管理器已暂停")
    
    def resume(self):
        """恢复任务管理器"""
        if self.status == TaskManagerStatus.PAUSED:
            self.status = TaskManagerStatus.RUNNING
            print("即梦图生图任务管理器已恢复")
    
    def get_status(self) -> Dict:
        """获取任务管理器状态"""
        with self.stats_lock:
            # 获取任务统计
            total_tasks = JimengImg2ImgTask.select().count()
            queued_tasks = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 0).count()
            processing_tasks = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 1).count()
            completed_tasks = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 2).count()
            failed_tasks = JimengImg2ImgTask.select().where(JimengImg2ImgTask.status == 3).count()
            
            return {
                'manager_status': self.status.value,
                'max_threads': self.max_threads,
                'active_threads': len(self.active_tasks),
                'active_tasks': list(self.active_tasks.values()),
                'stats': {
                    'total_tasks': total_tasks,
                    'queued_tasks': queued_tasks,
                    'processing_tasks': processing_tasks,
                    'completed_tasks': completed_tasks,
                    'failed_tasks': failed_tasks,
                    **self.stats
                }
            }
    
    def _task_loop(self):
        """主任务循环"""
        print("即梦图生图任务管理器主循环已启动")
        
        while self.status != TaskManagerStatus.STOPPED:
            try:
                if self.status == TaskManagerStatus.PAUSED:
                    time.sleep(1)
                    continue
                
                # 获取待处理的任务
                pending_tasks = self._get_pending_tasks()
                
                if not pending_tasks:
                    time.sleep(TASK_PROCESSOR_INTERVAL)
                    continue
                
                # 提交任务到线程池
                futures = []
                for task in pending_tasks[:self.max_threads - len(self.active_tasks)]:
                    future = self.executor.submit(self._process_task, task)
                    futures.append((future, task))
                
                # 等待任务完成（非阻塞）
                time.sleep(TASK_PROCESSOR_INTERVAL)
                
            except Exception as e:
                print(f"即梦图生图任务循环错误: {str(e)}")
                with self.stats_lock:
                    self.stats['error_count'] += 1
                time.sleep(TASK_PROCESSOR_ERROR_WAIT)
        
        print("即梦图生图任务管理器主循环已结束")
    
    def _get_pending_tasks(self) -> List[JimengImg2ImgTask]:
        """获取待处理的任务"""
        try:
            # 获取排队中的任务，按创建时间排序
            tasks = list(JimengImg2ImgTask.select().where(
                JimengImg2ImgTask.status == 0  # 排队中
            ).order_by(JimengImg2ImgTask.create_at).limit(self.max_threads))
            
            return tasks
        except Exception as e:
            print(f"获取待处理任务失败: {str(e)}")
            return []
    
    def _process_task(self, task: JimengImg2ImgTask):
        """处理单个任务"""
        thread_id = self._get_next_task_id()
        
        # 记录任务开始
        with self.tasks_lock:
            self.active_tasks[thread_id] = {
                'id': thread_id,
                'task_id': task.id,
                'task_type': 'img2img',
                'prompt': task.prompt[:50] + '...' if len(task.prompt) > 50 else task.prompt,
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'processing'
            }
        
        try:
            print(f"[线程{thread_id}] 开始处理图生图任务 {task.id}: {task.prompt[:50]}...")
            
            # 更新任务状态为生成中
            task.update_status(1)
            
            # 获取可用账号
            account = self._get_available_account()
            if not account:
                raise Exception("没有可用的账号")
            
            # 执行任务
            result = self._execute_task(task, account, thread_id)
            
            if result['success']:
                # 任务成功
                task.update_status(2)
                if result.get('images'):
                    task.set_images(result['images'])
                
                # 添加任务记录
                try:
                    from backend.models.models import JimengTaskRecord
                    record = JimengTaskRecord.create(
                        account_id=account.id,
                        task_type=4,  # 图生图任务类型
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    print(f"[线程{thread_id}] 添加图生图任务记录成功，记录ID: {record.id}")
                except Exception as e:
                    print(f"[线程{thread_id}] 添加任务记录失败: {str(e)}")
                
                with self.stats_lock:
                    self.stats['success_count'] += 1
                    self.stats['last_task_time'] = datetime.now()
                
                print(f"[线程{thread_id}] 任务 {task.id} 完成成功")
            else:
                # 任务失败
                error_code = result.get('error_code', 'UNKNOWN_ERROR')
                error_message = result.get('message', '未知错误')
                task.set_failure(error_code, error_message)
                
                with self.stats_lock:
                    self.stats['error_count'] += 1
                
                print(f"[线程{thread_id}] 任务 {task.id} 执行失败: {error_message}")
        
        except Exception as e:
            print(f"[线程{thread_id}] 任务 {task.id} 处理异常: {str(e)}")
            task.set_failure('PROCESSING_ERROR', str(e))
            
            with self.stats_lock:
                self.stats['error_count'] += 1
        
        finally:
            # 清理任务记录
            with self.tasks_lock:
                if thread_id in self.active_tasks:
                    del self.active_tasks[thread_id]
            
            with self.stats_lock:
                self.stats['total_processed'] += 1
    
    def _execute_task(self, task: JimengImg2ImgTask, account: JimengAccount, thread_id: int) -> Dict:
        """执行具体的图生图任务"""
        try:
            # 创建执行器
            executor = JimengImg2ImgExecutor(headless=get_hide_window())
            
            # 准备任务参数
            input_images = task.get_input_images()
            if not input_images:
                return {
                    'success': False,
                    'error_code': 'NO_INPUT_IMAGES',
                    'message': '没有输入图片'
                }
            
            task_params = {
                'prompt': task.prompt,
                'model': task.model,
                'input_images': input_images,
                'username': account.account,
                'password': account.password,
                'cookies': account.cookies
            }
            
            # 只有当ratio不为None时才传递aspect_ratio参数
            if task.ratio is not None:
                task_params['aspect_ratio'] = task.ratio
            
            # 更新任务状态
            with self.tasks_lock:
                if thread_id in self.active_tasks:
                    self.active_tasks[thread_id]['status'] = 'executing'
            
            # 执行任务
            result = run_async_safe(executor.run(**task_params))
            
            # 转换结果格式以匹配任务管理器期望的格式
            if result.code == 200 and result.data:
                return {
                    'success': True,
                    'images': result.data,
                    'account_id': account.id,
                    'cookies': result.cookies if hasattr(result, 'cookies') else None
                }
            else:
                return {
                    'success': False,
                    'error_code': result.code,
                    'message': result.message or '图生图任务执行失败'
                }
            
        except Exception as e:
            print(f"执行图生图任务异常: {str(e)}")
            return {
                'success': False,
                'error_code': 'EXECUTION_ERROR',
                'message': str(e)
            }
    
    def _get_available_account(self, preferred_account_id: Optional[int] = None) -> Optional[JimengAccount]:
        """获取可用的账号"""
        try:
            from datetime import date
            today = date.today()
            
            # 如果指定了账号ID，优先使用指定账号
            if preferred_account_id:
                try:
                    account = JimengAccount.get_by_id(preferred_account_id)
                    # 检查该账号今日图片生成使用次数（包括文生图和图生图）
                    from backend.models.models import JimengTaskRecord
                    today_usage = JimengTaskRecord.select().where(
                        (JimengTaskRecord.account_id == account.id) &
                        (JimengTaskRecord.task_type.in_([1, 4])) &  # 1=文生图, 4=图生图
                        (JimengTaskRecord.created_at >= today)
                    ).count()
                    
                    if today_usage < 50:  # 每日图生图限制50次
                        return account
                except:
                    pass
            
            # 获取所有账号
            accounts = list(JimengAccount.select())
            if not accounts:
                print("没有配置的即梦账号")
                return None
            
            # 查找今日使用次数最少且未达上限的账号
            available_accounts = []
            min_usage = float('inf')
            
            for account in accounts:
                # 统计今日该账号的图片生成使用次数（包括文生图和图生图）
                from backend.models.models import JimengTaskRecord
                today_usage = JimengTaskRecord.select().where(
                    (JimengTaskRecord.account_id == account.id) &
                    (JimengTaskRecord.task_type.in_([1, 4])) &  # 1=文生图, 4=图生图
                    (JimengTaskRecord.created_at >= today)
                ).count()
                
                print(f"账号 {account.account} 今日图片生成已使用: {today_usage}/50 次")
                
                # 检查是否还有可用次数
                if today_usage < 50:  # 每日图片生成限制50次
                    if today_usage < min_usage:
                        # 发现更少使用次数的账号，重置列表
                        min_usage = today_usage
                        available_accounts = [account]
                    elif today_usage == min_usage:
                        # 使用次数相同，加入候选列表
                        available_accounts.append(account)
            
            if available_accounts:
                # 在相同使用次数的账号中随机选择一个
                selected_account = random.choice(available_accounts)
                print(f"选择账号: {selected_account.account} (今日已使用{min_usage}次)")
                return selected_account
            else:
                print("所有账号今日图片生成次数已用完")
                return None
            
        except Exception as e:
            print(f"获取可用账号失败: {str(e)}")
            return None
    
    def _get_next_task_id(self) -> int:
        """获取下一个任务ID"""
        self._task_id_counter += 1
        return self._task_id_counter

# 创建全局实例
jimeng_img2img_task_manager = JimengImg2ImgTaskManager() 