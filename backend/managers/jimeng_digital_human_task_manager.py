"""
即梦数字人任务管理器
基于新的BaseTaskExecutor架构
"""
import asyncio
import logging
import threading
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime, date
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.utils.jimeng_ditigal_human import JimengDigitalHumanExecutor
from backend.models.models import JimengAccount, JimengTaskRecord, JimengDigitalHumanTask
from backend.utils.base_task_executor import ErrorCode
from backend.core.database import db as database
from backend.utils.config_util import get_automation_max_threads, get_hide_window
from backend.config.settings import TASK_PROCESSOR_INTERVAL, TASK_PROCESSOR_ERROR_WAIT

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class JimengDigitalHumanTaskManagerStatus(Enum):
    """即梦数字人任务管理器状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class JimengDigitalHumanTaskManager:
    def __init__(self):
        self.platform_name = "即梦数字人"
        self.status = JimengDigitalHumanTaskManagerStatus.STOPPED
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.processing_tasks = {}  # 正在处理的任务ID -> 任务信息
        self.stats = {
            'start_time': None,
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'last_scan_time': None,
            'error_count': 0
        }
        self._lock = threading.Lock()
        self.global_executor = None  # 全局线程池引用
        self.active_futures = {}  # 活跃的Future对象
        self.running_tasks = {}
    
    def set_global_executor(self, executor):
        """设置全局线程池"""
        self.global_executor = executor
        logger.info(f"{self.platform_name}已设置全局线程池")
    
    def start(self) -> bool:
        """启动数字人任务管理器"""
        if self.status == JimengDigitalHumanTaskManagerStatus.RUNNING:
            logger.info(f"{self.platform_name}任务管理器已经在运行中")
            return False
            
        logger.info(f"启动{self.platform_name}任务管理器...")
        
        if not self.global_executor:
            logger.error(f"{self.platform_name}任务管理器启动失败：未设置全局线程池")
            return False
        
        self.stop_event.clear()
        self.status = JimengDigitalHumanTaskManagerStatus.RUNNING
        self.stats['start_time'] = datetime.now()
        
        # 启动扫描工作线程
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        logger.info(f"{self.platform_name}任务管理器启动成功")
        return True
    
    def stop(self) -> bool:
        """停止数字人任务管理器"""
        if self.status == JimengDigitalHumanTaskManagerStatus.STOPPED:
            logger.info(f"{self.platform_name}任务管理器已经停止")
            return False
            
        logger.info(f"正在停止{self.platform_name}任务管理器...")
        self.status = JimengDigitalHumanTaskManagerStatus.STOPPED
        self.stop_event.set()
        
        # 清空活跃任务
        with self._lock:
            self.active_futures.clear()
            self.processing_tasks.clear()
        
        # 等待扫描工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
            
        logger.info(f"{self.platform_name}任务管理器已停止")
        return True
    
    def pause(self) -> bool:
        """暂停数字人任务管理器"""
        if self.status == JimengDigitalHumanTaskManagerStatus.RUNNING:
            self.status = JimengDigitalHumanTaskManagerStatus.PAUSED
            logger.info(f"数字人任务管理器已暂停")
            return True
        return False
    
    def resume(self) -> bool:
        """恢复数字人任务管理器"""
        if self.status == JimengDigitalHumanTaskManagerStatus.PAUSED:
            self.status = JimengDigitalHumanTaskManagerStatus.RUNNING
            logger.info(f"数字人任务管理器已恢复")
            return True
        return False
    
    def _worker_loop(self):
        """工作线程主循环"""
        logger.info(f"{self.platform_name}任务扫描线程已启动")
        
        # 初始延迟，等待数据库操作完全稳定
        logger.info(f"{self.platform_name}任务扫描线程等待数据库稳定...")
        time.sleep(5.0)
        logger.info(f"{self.platform_name}开始扫描任务...")
        
        while not self.stop_event.is_set():
            try:
                # 更新扫描时间
                self.stats['last_scan_time'] = datetime.now()
                
                # 如果是暂停状态，跳过扫描
                if self.status == JimengDigitalHumanTaskManagerStatus.PAUSED:
                    time.sleep(TASK_PROCESSOR_INTERVAL)
                    continue
                
                # 扫描待处理任务
                self._scan_and_process_tasks()
                
                # 清理已完成的任务记录
                self._cleanup_finished_tasks()
                
                # 等待下次扫描
                time.sleep(TASK_PROCESSOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"{self.platform_name}任务扫描异常: {str(e)}")
                self.stats['error_count'] += 1
                self.status = JimengDigitalHumanTaskManagerStatus.ERROR
                time.sleep(TASK_PROCESSOR_ERROR_WAIT)
                self.status = JimengDigitalHumanTaskManagerStatus.RUNNING  # 自动恢复
        
        logger.info(f"{self.platform_name}任务扫描线程已结束")
    
    def _scan_and_process_tasks(self):
        """扫描并处理待处理任务"""
        try:
            if not self.global_executor or self.global_executor._shutdown:
                return
                
            # 获取配置的最大线程数
            max_threads = get_automation_max_threads()
            
            # 获取当前活跃的任务数量
            with self._lock:
                active_count = len([f for f in self.active_futures.values() if not f.done()])
            
            if active_count >= max_threads:
                return
            
            # 计算可以启动的新任务数量
            available_slots = max_threads - active_count
            
            # 查找排队中的数字人任务
            pending_tasks = JimengDigitalHumanTask.select().where(
                JimengDigitalHumanTask.status == 0
            ).order_by(JimengDigitalHumanTask.create_at).limit(available_slots)
            
            for task in pending_tasks:
                # 检查是否已经在处理中
                if task.id in self.processing_tasks:
                    continue
                
                # 提交任务到线程池
                self._submit_task_to_pool(task)
                
        except Exception as e:
            logger.error(f"{self.platform_name}扫描任务失败: {str(e)}")
    
    def _submit_task_to_pool(self, task):
        """提交任务到全局线程池"""
        try:
            if not self.global_executor:
                logger.error(f"无法提交任务：全局线程池未设置")
                return
                
            # 通过全局任务管理器提交任务，以便正确跟踪线程状态
            from backend.core.global_task_manager import global_task_manager
            future = global_task_manager.submit_task(
                self.platform_name,
                self._process_single_task,
                task,
                task_id=task.id,
                task_type='数字人',
                prompt=f"图片:{task.image_path}, 音频:{task.audio_path}"
            )
            
            # 记录处理信息
            with self._lock:
                self.processing_tasks[task.id] = {
                    'future': future,
                    'start_time': datetime.now(),
                    'status': 'starting',
                    'task': task
                }
                self.active_futures[task.id] = future
            
            # 添加完成回调
            future.add_done_callback(lambda f: self._on_task_completed(task.id, f))
            
            logger.info(f"提交{self.platform_name}任务到线程池，任务ID: {task.id}")
            
        except Exception as e:
            logger.error(f"提交{self.platform_name}任务到线程池失败，错误: {str(e)}")
    
    def _on_task_completed(self, task_id, future):
        """任务完成回调"""
        try:
            with self._lock:
                if task_id in self.processing_tasks:
                    self.processing_tasks[task_id]['status'] = 'finished'
                    self.processing_tasks[task_id]['end_time'] = datetime.now()
                    
                # 从活跃futures中移除
                if task_id in self.active_futures:
                    del self.active_futures[task_id]
                    
            logger.info(f"{self.platform_name}任务执行完成，任务ID: {task_id}")
            
        except Exception as e:
            logger.error(f"处理{self.platform_name}任务完成回调失败: {str(e)}")
    
    def _process_single_task(self, task):
        """处理单个数字人任务"""
        try:
            # 更新处理状态
            with self._lock:
                if task.id in self.processing_tasks:
                    self.processing_tasks[task.id]['status'] = 'processing'
            
            logger.info(f"开始处理{self.platform_name}任务，ID: {task.id}")
            
            # 更新任务状态为处理中
            task.status = 1
            task.start_time = datetime.now()
            task.save()
            
            # 执行具体的任务处理逻辑
            result = run_async_safe(self._execute_digital_human_task(task))
            
            if result['success']:
                # 任务成功
                if 'video_url' in result and result['video_url']:
                    task.video_url = result['video_url']
                
                if 'account_id' in result:
                    task.account_id = result['account_id']
                    
                    # 更新账号cookies
                    if 'cookies' in result and result['cookies']:
                        run_async_safe(self.update_account_cookies(result['account_id'], result['cookies']))
                
                task.status = 2  # 已完成
                task.save()
                
                logger.info(f"{self.platform_name}任务完成，ID: {task.id}")
                with self._lock:
                    self.stats['successful'] += 1
            else:
                # 任务失败，但仍要更新cookies - 账号使用记录已在_execute_digital_human_task中处理
                if 'account_id' in result:
                    # 更新账号cookies（即使失败也要更新）
                    if 'cookies' in result and result['cookies']:
                        run_async_safe(self.update_account_cookies(result['account_id'], result['cookies']))
                
                # 检查是否需要重试（600/900错误码）
                error_code = result.get('code', 'OTHER_ERROR')
                if error_code in [600, 900]:
                    # 设置失败状态和原因
                    task.set_failure(error_code, result.get('error', '未知错误'))
                    
                    # 检查是否可以重试
                    if task.can_retry():
                        # 重试任务，重新进入排队状态
                        if task.retry_task():
                            logger.info(f"{self.platform_name}任务重试，ID: {task.id}，重试次数: {task.retry_count}/{task.max_retry}")
                            # 不增加失败计数，因为任务重新排队了
                        else:
                            logger.error(f"{self.platform_name}任务重试失败，ID: {task.id}，已达最大重试次数")
                            with self._lock:
                                self.stats['failed'] += 1
                    else:
                        logger.error(f"{self.platform_name}任务不可重试，ID: {task.id}，原因: {result.get('error', '未知错误')}")
                        with self._lock:
                            self.stats['failed'] += 1
                elif error_code == 800:
                    # 800错误码：生成失败，账号使用记录已在执行方法中处理
                    task.set_failure(error_code, result.get('error', '未知错误'))
                    logger.error(f"{self.platform_name}任务生成失败，ID: {task.id}，原因: {result.get('error', '未知错误')}")
                    with self._lock:
                        self.stats['failed'] += 1
                else:
                    # 非600/900/800错误，直接设置失败
                    task.set_failure(error_code, result.get('error', '未知错误'))
                    
                    logger.error(f"{self.platform_name}任务失败，ID: {task.id}，原因: {result.get('error', '未知错误')}")
                    with self._lock:
                        self.stats['failed'] += 1
            
            with self._lock:
                self.stats['total_processed'] += 1
            
        except Exception as e:
            logger.error(f"处理{self.platform_name}任务异常，ID: {task.id}，错误: {str(e)}")
            try:
                task.set_failure('OTHER_ERROR', str(e))
                with self._lock:
                    self.stats['failed'] += 1
                    self.stats['total_processed'] += 1
            except:
                pass
    
    def _cleanup_finished_tasks(self):
        """清理已完成的任务记录"""
        with self._lock:
            # 清理已完成的处理任务记录
            finished_tasks = [
                task_id for task_id, info in self.processing_tasks.items()
                if info.get('status') == 'finished'
            ]
            
            for task_id in finished_tasks:
                del self.processing_tasks[task_id]
                
            # 清理已完成的futures
            finished_futures = [
                task_id for task_id, future in self.active_futures.items()
                if future.done()
            ]
            
            for task_id in finished_futures:
                if task_id in self.active_futures:
                    del self.active_futures[task_id]
    
    async def _execute_digital_human_task(self, task) -> Dict:
        """
        执行即梦数字人任务的具体逻辑
        
        参数:
            task: JimengDigitalHumanTask 对象
        
        返回值:
            Dict: 执行结果
        """
        
        logger.info(f"开始执行数字人任务，任务ID: {task.id}")
        logger.info(f"任务对象类型: {type(task)}")
        logger.info(f"任务对象属性: {dir(task)}")
        logger.info(f"任务参数: image_path='{task.image_path}', audio_path='{task.audio_path}'")
        
        try:
            # 获取可用账号
            available_account = self._get_available_account('digital_human')
            if not available_account:
                return {'success': False, 'error': '没有可用的即梦账号或账号使用次数已达上限', 'account_id': None}
            
            logger.info(f"使用账号: {available_account.account}")
            
            # 获取浏览器隐藏配置
            headless = get_hide_window()
            
            # 使用数字人执行器
            executor = JimengDigitalHumanExecutor(headless=headless)
            result = await executor.run(
                image_path=task.image_path,
                audio_path=task.audio_path,
                username=available_account.account,
                password=available_account.password,
                cookies=available_account.cookies
            )
            
            if result.code == 200 and result.data:
                # 更新账号使用次数
                await self.add_task_record(available_account.id, 3)  # 3=数字人
                
                return {
                    'success': True, 
                    'video_url': result.data,
                    'account_id': available_account.id,
                    'cookies': result.cookies
                }
            else:
                error_msg = result.message or "即梦平台数字人生成失败"
                error_code = result.code
                
                # 如果是700（任务ID等待超时）或800（生成失败），需要更新账号使用记录
                if error_code in [700, 800]:
                    logger.info(f"错误码 {error_code}，更新账号使用情况")
                    await self.add_task_record(available_account.id, 3)  # 3=数字人
                
                return {
                    'success': False, 
                    'error': error_msg, 
                    'account_id': available_account.id, 
                    'should_create_empty_task': error_code in [700, 800], 
                    'code': error_code,
                    'cookies': result.cookies
                }
                
        except Exception as e:
            logger.error(f"即梦数字人任务执行异常: {str(e)}")
            return {'success': False, 'error': f'任务执行异常: {str(e)}'}
    
    async def add_task_record(self, account_id: int, task_type: int = 3, 
                            task_id: Optional[str] = None) -> Optional[int]:
        """添加任务记录到数据库 (task_type: 3=数字人)"""
        try:
            record = JimengTaskRecord.create(
                account_id=account_id,
                task_type=task_type,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"添加任务记录成功，记录ID: {record.id}")
            return record.id
            
        except Exception as e:
            logger.error(f"添加任务记录失败: {str(e)}")
            return None
    
    async def update_account_cookies(self, account_id: int, cookies: str):
        """更新账号的cookies"""
        try:
            # 确保在数据库事务中执行
            with database.atomic():
                account = JimengAccount.get_by_id(account_id)
                old_cookies = account.cookies
                account.cookies = cookies
                account.updated_at = datetime.now()
                account.save()
                
                logger.info(f"更新账号cookies成功，账号ID: {account_id}, 旧cookies长度: {len(old_cookies) if old_cookies else 0}, 新cookies长度: {len(cookies)}")
            
        except JimengAccount.DoesNotExist:
            logger.error(f"更新账号cookies失败: 账号不存在，ID: {account_id}")
            raise
        except Exception as e:
            logger.error(f"更新账号cookies失败，账号ID: {account_id}, 错误: {str(e)}")
            raise
    
    async def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取账号信息"""
        try:
            account = JimengAccount.get_by_id(account_id)
            return {
                'id': account.id,
                'username': account.account,
                'password': account.password,
                'cookies': account.cookies,
                'created_at': account.created_at,
                'updated_at': account.updated_at
            }
            
        except JimengAccount.DoesNotExist:
            logger.error(f"账号不存在: {account_id}")
            return None
        except Exception as e:
            logger.error(f"获取账号信息失败: {str(e)}")
            return None
    
    def _get_available_account(self, task_type='digital_human'):
        """
        获取可用的即梦账号
        
        参数:
            task_type: 任务类型 ('text2img', 'img2video', 'digital_human')
        
        规则：
        - 图片生成：每个账号每天可生成50次
        - 视频生成：每个账号每天可生成1次
        - 数字人生成：每个账号每天可生成1次
        - 优先选择使用次数最少的账号
        """
        try:
            import random
            from datetime import date
            today = date.today()
            
            # 查询所有账号
            accounts = list(JimengAccount.select())
            if not accounts:
                logger.error("没有配置的即梦账号")
                return None
            
            # 根据任务类型设置每日限制
            daily_limits = {
                'text2img': 50,      # 图片生成每天50次
                'img2video': 2,      # 视频生成每天1次
                'digital_human': 1   # 数字人生成每天1次
            }
            
            daily_limit = daily_limits.get(task_type, 1)
            
            # 查找今日使用次数最少且未达上限的账号，在相同使用次数中随机选择
            available_accounts = []
            min_usage = float('inf')
            
            for account in accounts:
                # 统计今日该账号的指定类型任务使用次数（查询账号记录表）
                task_type_map = {
                    'text2img': 1,      # 文生图
                    'img2video': 2,     # 图生视频
                    'digital_human': 3  # 数字人
                }
                
                task_type_id = task_type_map.get(task_type, 3)
                
                # 查询今日该账号该类型的任务记录数量
                today_usage = JimengTaskRecord.select().where(
                    (JimengTaskRecord.account_id == account.id) &
                    (JimengTaskRecord.task_type == task_type_id) &
                    (JimengTaskRecord.created_at >= today)
                ).count()
                
                logger.info(f"账号 {account.account} 今日{task_type}已使用: {today_usage}/{daily_limit} 次")
                
                # 检查是否还有可用次数
                if today_usage < daily_limit:
                    if today_usage < min_usage:
                        # 发现更少使用次数的账号，重置列表
                        min_usage = today_usage
                        available_accounts = [account]
                    elif today_usage == min_usage:
                        # 使用次数相同，加入候选列表
                        available_accounts.append(account)
            
            if available_accounts:
                # 在使用次数最少的账号中随机选择
                selected_account = random.choice(available_accounts)
                logger.info(f"随机选择账号: {selected_account.account} (今日{task_type}已使用: {min_usage}/{daily_limit})")
                return selected_account
            else:
                logger.error(f"所有账号今日{task_type}使用次数已达上限")
                return None
                
        except Exception as e:
            logger.error(f"获取可用账号失败: {str(e)}")
            return None
    
    async def execute_task(self, task_id: str, text: str, voice: str = "default", 
                          avatar: str = "default", account_id: int = None, headless: bool = True) -> Dict[str, Any]:
        """执行数字人生成任务"""
        try:
            logger.info(f"开始执行数字人生成任务: {task_id}")
            
            # 获取账号信息
            account_info = None
            if account_id:
                account_info = await self.get_account_by_id(account_id)
                if not account_info:
                    return {
                        "code": 400,
                        "data": None,
                        "message": "指定的账号不存在"
                    }
            else:
                # 如果没有指定账号，自动选择可用账号
                available_account = self._get_available_account('digital_human')
                if available_account:
                    account_id = available_account.id
                    account_info = {
                        'id': available_account.id,
                        'username': available_account.account,
                        'password': available_account.password,
                        'cookies': available_account.cookies,
                        'created_at': available_account.created_at,
                        'updated_at': available_account.updated_at
                    }
                    logger.info(f"自动选择账号: {available_account.account}")
                else:
                    return {
                        "code": 400,
                        "data": None,
                        "message": "没有可用的即梦账号或账号使用次数已达上限"
                    }
            
            # 不再在开始时添加任务记录，而是在成功时添加
            
            # 创建执行器并执行任务
            executor = JimengDigitalHumanExecutor(headless=headless)
            
            # 准备执行参数
            execute_params = {
                'text': text,
                'voice': voice,
                'avatar': avatar
            }
            
            # 如果有账号信息，添加认证参数
            if account_info:
                execute_params['username'] = account_info['username']
                execute_params['password'] = account_info['password']
                if account_info['cookies']:
                    execute_params['cookies'] = account_info['cookies']
            
            # 执行任务
            result = await executor.run(**execute_params)
            
            # 处理结果并更新cookies
            if result.code == ErrorCode.SUCCESS.value:
                # 任务成功
                # 更新cookies
                if account_info and result.cookies:
                    try:
                        await self.update_account_cookies(account_id, result.cookies)
                    except Exception as e:
                        logger.error(f"数字人任务执行成功但cookie更新失败，任务ID: {task_id}, 错误: {str(e)}")
                
                # 添加任务记录
                if account_info:
                    await self.add_task_record(
                        account_id=account_id,
                        task_type=3  # 数字人
                    )
                
                logger.info(f"数字人生成任务执行成功: {task_id}")
                return {
                    "code": 200,
                    "data": result.data,
                    "message": "数字人生成任务执行成功"
                }
                
            elif result.code == ErrorCode.TASK_ID_NOT_OBTAINED.value:
                # 创建任务成功但未获取到task_id
                # 仍然要更新cookies
                if account_info and result.cookies:
                    try:
                        await self.update_account_cookies(account_id, result.cookies)
                    except Exception as e:
                        logger.error(f"数字人任务部分成功但cookie更新失败，任务ID: {task_id}, 错误: {str(e)}")
                
                # 添加任务记录（即使失败也要记录账号使用）
                if account_info:
                    await self.add_task_record(
                        account_id=account_id,
                        task_type=3  # 数字人
                    )
                
                logger.warning(f"数字人生成任务创建成功但未获取到task_id: {task_id}")
                return {
                    "code": 603,
                    "data": None,
                    "message": result.message
                }
                
            elif result.code == ErrorCode.GENERATION_FAILED.value:
                # 生成完成但未获取到URL
                # 仍然要更新cookies
                if account_info and result.cookies:
                    try:
                        await self.update_account_cookies(account_id, result.cookies)
                    except Exception as e:
                        logger.error(f"数字人生成失败但cookie更新也失败，任务ID: {task_id}, 错误: {str(e)}")
                
                # 添加任务记录（即使失败也要记录账号使用）
                if account_info:
                    await self.add_task_record(
                        account_id=account_id,
                        task_type=3  # 数字人
                    )
                
                logger.warning(f"数字人生成完成但未获取到URL: {task_id}")
                return {
                    "code": 604,
                    "data": None,
                    "message": result.message
                }
                
            else:
                # 其他错误
                # 如果有cookies也要更新
                if account_info and result.cookies:
                    try:
                        await self.update_account_cookies(account_id, result.cookies)
                    except Exception as e:
                        logger.error(f"数字人任务执行失败且cookie更新失败，任务ID: {task_id}, 错误: {str(e)}")
                
                logger.error(f"数字人生成任务执行失败: {task_id}, 错误: {result.message}")
                return {
                    "code": result.code,
                    "data": None,
                    "message": result.message
                }
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"执行数字人生成任务时出错: {error_msg}")
            
            return {
                "code": 500,
                "data": None,
                "message": f"执行数字人生成任务时出错: {error_msg}"
            }
        
        finally:
            # 清理运行中的任务记录
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def start_task(self, text: str, voice: str = "default", avatar: str = "default", 
                        account_id: int = None, headless: bool = True) -> Dict[str, Any]:
        """启动数字人生成任务"""
        import uuid
        task_id = str(uuid.uuid4())
        
        logger.info(f"启动数字人生成任务: {task_id}")
        
        # 记录任务为运行中
        self.running_tasks[task_id] = {
            "status": "running",
            "started_at": datetime.now()
        }
        
        # 异步执行任务
        asyncio.create_task(
            self.execute_task(task_id, text, voice, avatar, account_id, headless)
        )
        
        return {
            "code": 200,
            "data": {"task_id": task_id},
            "message": "数字人生成任务已启动"
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id in self.running_tasks:
            return {
                "code": 200,
                "data": self.running_tasks[task_id],
                "message": "任务运行中"
            }
        else:
            return {
                "code": 404,
                "data": None,
                "message": "任务不存在或已完成"
            }
    
    def get_summary(self) -> Dict:
        """获取即梦数字人任务汇总"""
        try:
            # 统计数字人任务状态
            base_query = JimengDigitalHumanTask.select()
            
            pending_count = base_query.where(
                JimengDigitalHumanTask.status == 0  # 排队中
            ).count()
            
            processing_count = base_query.where(
                JimengDigitalHumanTask.status == 1  # 生成中
            ).count()
            
            completed_count = base_query.where(
                JimengDigitalHumanTask.status == 2  # 已完成
            ).count()
            
            failed_count = base_query.where(
                JimengDigitalHumanTask.status == 3  # 失败
            ).count()
            
            return {
                'platform': self.platform_name,
                'pending': pending_count,
                'processing': processing_count,
                'completed': completed_count,
                'failed': failed_count,
                'total': pending_count + processing_count + completed_count + failed_count
            }
        except Exception as e:
            logger.error(f"获取{self.platform_name}汇总失败: {str(e)}")
            return {
                'platform': self.platform_name,
                'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0, 'total': 0
            }
    
    def get_status(self) -> Dict:
        """获取即梦数字人任务管理器状态"""
        with self._lock:
            max_threads = get_automation_max_threads()
            active_threads = len([f for f in self.active_futures.values() if not f.done()])
            
            return {
                'platform': self.platform_name,
                'status': self.status.value,
                'processing_count': len(self.processing_tasks),
                'processing_tasks': list(self.processing_tasks.keys()),
                'stats': self.stats.copy(),
                'uptime': (datetime.now() - self.stats['start_time']).total_seconds() 
                         if self.stats['start_time'] else 0,
                'max_threads': max_threads,
                'active_threads': active_threads,
                'thread_pool_alive': self.global_executor is not None and not self.global_executor._shutdown
            }

# 全局实例
jimeng_digital_human_task_manager = JimengDigitalHumanTaskManager() 