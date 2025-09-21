# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from datetime import datetime, date
from backend.models.models import JimengAccount
from backend.utils.jimeng_account_login import login_and_get_cookie
from backend.utils.jimeng_login_window import login_and_wait
from backend.core.global_task_manager import global_task_manager
import asyncio

# 创建蓝图
jimeng_accounts_bp = Blueprint('jimeng_accounts', __name__, url_prefix='/api/jimeng/accounts')

@jimeng_accounts_bp.route('', methods=['GET'])
def get_accounts():
    """获取所有账号"""
    try:
        accounts = JimengAccount.select()
        data = []
        today = date.today()
        
        for account in accounts:
            # 使用JimengTaskRecord表统计今日使用次数
            from backend.models.models import JimengTaskRecord
            
            # 计算今日文生图使用次数 (task_type=1)
            text2img_usage = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 1) &
                (JimengTaskRecord.created_at >= today)
            ).count()
            
            # 计算今日图生视频使用次数 (task_type=2)
            img2video_usage = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 2) &
                (JimengTaskRecord.created_at >= today)
            ).count()
            
            # 计算今日数字人使用次数 (task_type=3)
            digital_human_usage = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 3) &
                (JimengTaskRecord.created_at >= today)
            ).count()
            
            data.append({
                'id': account.id,
                'account': account.account,
                'password': account.password,
                'has_cookies': bool(account.cookies),  # 添加布尔值表示是否有Cookie
                'created_at': account.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': account.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'today_usage': {
                    'text2img': text2img_usage,
                    'img2video': img2video_usage,
                    'digital_human': digital_human_usage
                },
                'daily_limits': {
                    'text2img': 50,
                    'img2video': 2,  # 更新为2个视频任务
                    'digital_human': 1
                }
            })
        
        print("成功获取账号列表，总数: {}".format(len(data)))
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        print("获取账号列表失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '获取账号列表失败: {}'.format(str(e))
        }), 500

@jimeng_accounts_bp.route('', methods=['POST'])
def add_accounts():
    """批量添加账号"""
    try:
        data = request.get_json()
        accounts_text = data.get('accounts_text', '')
        
        if not accounts_text.strip():
            return jsonify({
                'success': False,
                'message': '请提供账号信息'
            }), 400
            
        print("开始批量添加即梦账号")
        
        lines = accounts_text.strip().split('\n')
        added_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if '----' in line:
                parts = line.split('----')
                if len(parts) >= 2:
                    account = parts[0].strip()
                    password = parts[1].strip()
                    
                    if account and password:
                        JimengAccount.create(
                            account=account,
                            password=password
                        )
                        added_count += 1
                        print("添加账号: {}".format(account))
        
        print("批量添加完成，成功添加 {} 个账号".format(added_count))
        return jsonify({
            'success': True,
            'message': '成功添加 {} 个账号'.format(added_count),
            'added_count': added_count
        })
        
    except Exception as e:
        print("批量添加账号失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '添加失败: {}'.format(str(e))
        }), 500

@jimeng_accounts_bp.route('/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """删除指定账号"""
    try:
        print("删除即梦账号，ID: {}".format(account_id))
        account = JimengAccount.get(JimengAccount.id == account_id)
        deleted_account = account.account
        account.delete_instance()
        
        print("成功删除账号: {}".format(deleted_account))
        return jsonify({
            'success': True,
            'message': '已成功删除账号: {}'.format(deleted_account)
        })
        
    except JimengAccount.DoesNotExist:
        print("删除失败：账号不存在，ID: {}".format(account_id))
        return jsonify({
            'success': False,
            'message': '账号不存在'
        }), 404
        
    except Exception as e:
        print("删除账号异常，ID: {}, 错误: {}".format(account_id, str(e)))
        return jsonify({
            'success': False,
            'message': '删除失败: {}'.format(str(e))
        }), 500

@jimeng_accounts_bp.route('/clear', methods=['DELETE'])
def clear_all_accounts():
    """清空所有账号"""
    try:
        print("警告：开始清空所有即梦账号")
        deleted_count = JimengAccount.delete().execute()
        print("已清空所有账号，共删除 {} 个".format(deleted_count))
        return jsonify({
            'success': True,
            'message': '已清空所有账号，共删除 {} 个'.format(deleted_count),
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print("清空所有账号异常: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '清空失败: {}'.format(str(e))
        }), 500

@jimeng_accounts_bp.route('/usage-stats', methods=['GET'])
def get_account_usage_stats():
    """获取账号使用情况统计"""
    try:
        from datetime import date
        
        today = date.today()
        accounts = list(JimengAccount.select())
        
        stats = []
        for account in accounts:
            # 使用JimengTaskRecord表统计使用次数
            from backend.models.models import JimengTaskRecord
            
            # 统计今日文生图使用次数 (task_type=1)
            today_text2img = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 1) &
                (JimengTaskRecord.created_at >= today)
            ).count()
            
            # 统计今日图生视频使用次数 (task_type=2)
            today_img2video = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 2) &
                (JimengTaskRecord.created_at >= today)
            ).count()
            
            # 统计今日数字人使用次数 (task_type=3)
            today_digital_human = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 3) &
                (JimengTaskRecord.created_at >= today)
            ).count()
            
            # 统计总使用次数
            total_text2img = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 1)
            ).count()
            
            total_img2video = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 2)
            ).count()
            
            total_digital_human = JimengTaskRecord.select().where(
                (JimengTaskRecord.account_id == account.id) &
                (JimengTaskRecord.task_type == 3)
            ).count()
            
            # 设置每日限额
            text2img_limit = 50
            img2video_limit = 2  # 更新为2个视频任务
            digital_human_limit = 1
            
            # 判断账号状态 - 任何一种类型达到限制就视为已满
            is_available = (today_text2img < text2img_limit) and (today_img2video < img2video_limit) and (today_digital_human < digital_human_limit)
            
            stats.append({
                'id': account.id,
                'account': account.account,
                'today_usage': {
                    'text2img': today_text2img,
                    'img2video': today_img2video,
                    'digital_human': today_digital_human
                },
                'daily_limits': {
                    'text2img': text2img_limit,
                    'img2video': img2video_limit,
                    'digital_human': digital_human_limit
                },
                'remaining': {
                    'text2img': max(0, text2img_limit - today_text2img),
                    'img2video': max(0, img2video_limit - today_img2video),
                    'digital_human': max(0, digital_human_limit - today_digital_human)
                },
                'total_usage': {
                    'text2img': total_text2img,
                    'img2video': total_img2video,
                    'digital_human': total_digital_human
                },
                'status': 'available' if is_available else 'limit_reached',
                'last_used': None  # 可以后续添加最后使用时间
            })
        
        # 计算总体统计数据
        total_today_text2img = sum(s['today_usage']['text2img'] for s in stats)
        total_today_img2video = sum(s['today_usage']['img2video'] for s in stats)
        total_today_digital_human = sum(s['today_usage']['digital_human'] for s in stats)
        
        total_remaining_text2img = sum(s['remaining']['text2img'] for s in stats)
        total_remaining_img2video = sum(s['remaining']['img2video'] for s in stats)
        total_remaining_digital_human = sum(s['remaining']['digital_human'] for s in stats)
        
        return jsonify({
            'success': True,
            'data': {
                'accounts': stats,
                'summary': {
                    'total_accounts': len(accounts),
                    'available_accounts': len([s for s in stats if s['status'] == 'available']),
                    'today_usage': {
                        'text2img': total_today_text2img,
                        'img2video': total_today_img2video,
                        'digital_human': total_today_digital_human,
                        'total': total_today_text2img + total_today_img2video + total_today_digital_human
                    },
                    'remaining': {
                        'text2img': total_remaining_text2img,
                        'img2video': total_remaining_img2video,
                        'digital_human': total_remaining_digital_human,
                        'total': total_remaining_text2img + total_remaining_img2video + total_remaining_digital_human
                    }
                }
            },
            'message': '获取账号使用统计成功'
        })
        
    except Exception as e:
        print("获取账号使用统计失败: {}".format(str(e)))
        return jsonify({
            'success': False,
            'message': '获取统计失败: {}'.format(str(e))
        }), 500

@jimeng_accounts_bp.route('/<int:account_id>/login', methods=['POST'])
def login_account(account_id):
    """登录指定账号（使用jimeng_login_window）"""
    try:
        print(f"开始登录账号，账号ID: {account_id}")
        account = JimengAccount.get_by_id(account_id)
        
        # 提交登录任务到全局线程池
        task_future = global_task_manager.submit_task(
            platform_name="即梦账号",
            task_callable=_process_login_task,
            task_id=account_id,  # 传递task_id参数
            account_id=account.id,  # 传递account_id参数
            account_email=account.account,  # 传递account_email参数
            account_password=account.password,  # 传递account_password参数
            task_type="登录账号",
            prompt=f"登录账号 {account.account}"
        )
        
        print(f"登录任务已提交到线程池，账号: {account.account}")
        return jsonify({
            'success': True,
            'message': f'正在登录账号 {account.account}，浏览器窗口已打开...'
        })
        
    except JimengAccount.DoesNotExist:
        print(f"登录失败：账号不存在，ID: {account_id}")
        return jsonify({
            'success': False,
            'message': '账号不存在'
        }), 404
        
    except Exception as e:
        print(f"登录异常，ID: {account_id}, 错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500

@jimeng_accounts_bp.route('/<int:account_id>/get-cookie', methods=['POST'])
def get_account_cookie(account_id):
    """获取指定账号的Cookie"""
    try:
        print(f"开始获取账号Cookie，账号ID: {account_id}")
        account = JimengAccount.get_by_id(account_id)
        
        # 提交任务到全局线程池
        task_future = global_task_manager.submit_task(
            platform_name="即梦账号",
            task_callable=_process_cookie_task,
            task_id=account_id,  # 传递task_id参数
            account_id=account.id,  # 传递account_id参数
            account_email=account.account,  # 传递account_email参数
            task_type="获取Cookie",
            prompt=f"获取账号 {account.account} 的Cookie"
        )
        
        print(f"Cookie获取任务已提交到线程池，账号: {account.account}")
        return jsonify({
            'success': True,
            'message': f'正在获取账号 {account.account} 的Cookie，请稍候...'
        })
        
    except JimengAccount.DoesNotExist:
        print(f"获取Cookie失败：账号不存在，ID: {account_id}")
        return jsonify({
            'success': False,
            'message': '账号不存在'
        }), 404
        
    except Exception as e:
        print(f"获取Cookie异常，ID: {account_id}, 错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取Cookie失败: {str(e)}'
        }), 500

@jimeng_accounts_bp.route('/batch-get-cookie', methods=['POST'])
def batch_get_account_cookie():
    """批量获取账号Cookie"""
    try:
        data = request.get_json()
        account_ids = data.get('account_ids', [])
        
        if not account_ids:
            return jsonify({
                'success': False,
                'message': '请提供要获取Cookie的账号ID列表'
            }), 400
        
        # 获取账号信息
        accounts = list(JimengAccount.select().where(JimengAccount.id.in_(account_ids)))
        
        if not accounts:
            return jsonify({
                'success': False,
                'message': '未找到指定的账号'
            }), 404
        
        # 提交任务到全局线程池
        for account in accounts:
            global_task_manager.submit_task(
                platform_name="即梦账号",
                task_callable=_process_cookie_task,
                task_id=account.id,  # 传递task_id参数
                account_id=account.id,  # 传递account_id参数
                account_email=account.account,  # 传递account_email参数
                task_type="获取Cookie",
                prompt=f"获取账号 {account.account} 的Cookie"
            )
        
        print(f"批量获取Cookie任务已提交，账号数量: {len(accounts)}")
        return jsonify({
            'success': True,
            'message': f'正在获取 {len(accounts)} 个账号的Cookie，请稍候...'
        })
        
    except Exception as e:
        print(f"批量获取Cookie异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'批量获取Cookie失败: {str(e)}'
        }), 500

@jimeng_accounts_bp.route('/update-all-cookies', methods=['POST'])
def update_all_cookies():
    """更新所有账号的Cookie"""
    try:
        # 获取所有账号
        accounts = list(JimengAccount.select())
        
        if not accounts:
            return jsonify({
                'success': False,
                'message': '没有找到任何账号'
            }), 404
        
        # 启动批量更新Cookie的后台任务
        import threading
        
        def batch_update_cookies():
            """批量更新Cookie的后台任务"""
            import time
            
            for account in accounts:
                # 检查线程池是否有空位
                while True:
                    active_threads = len(global_task_manager.active_tasks)
                    max_threads = global_task_manager.max_threads
                    
                    if active_threads < max_threads:
                        # 有空位，提交任务
                        global_task_manager.submit_task(
                            platform_name="即梦账号",
                            task_callable=_process_cookie_task,
                            task_id=account.id,
                            account_id=account.id,
                            account_email=account.account,
                            task_type="获取Cookie",
                            prompt=f"获取账号 {account.account} 的Cookie"
                        )
                        print(f"已提交账号 {account.account} 的Cookie获取任务")
                        break
                    else:
                        # 线程池满了，等待一会再检查
                        print(f"线程池已满，等待空位提交账号 {account.account} 的任务...")
                        time.sleep(2)
                
                # 稍微延迟一下，避免过快提交
                time.sleep(0.5)
            
            print(f"所有账号Cookie更新任务已成功提交完成，共 {len(accounts)} 个账号")
        
        # 启动后台线程
        update_thread = threading.Thread(target=batch_update_cookies, daemon=True)
        update_thread.start()
        
        print(f"开始批量更新所有账号Cookie，账号数量: {len(accounts)}")
        return jsonify({
            'success': True,
            'message': f'正在批量更新 {len(accounts)} 个账号的Cookie，任务将智能调度到线程池中...'
        })
        
    except Exception as e:
        print(f"更新所有账号Cookie异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新所有账号Cookie失败: {str(e)}'
        }), 500

@jimeng_accounts_bp.route('/get-uncookied-accounts-cookie', methods=['POST'])
def get_uncookied_accounts_cookie():
    """获取所有未设置Cookie账号的Cookie"""
    try:
        # 获取所有未设置Cookie的账号
        uncookied_accounts = list(JimengAccount.select().where(
            (JimengAccount.cookies.is_null()) | (JimengAccount.cookies == '')
        ))
        
        if not uncookied_accounts:
            return jsonify({
                'success': False,
                'message': '没有找到未设置Cookie的账号'
            }), 404
        
        # 启动批量获取Cookie的后台任务
        import threading
        
        def batch_get_uncookied_accounts():
            """批量获取未设置Cookie账号的后台任务"""
            import time
            
            for account in uncookied_accounts:
                # 检查线程池是否有空位
                while True:
                    active_threads = len(global_task_manager.active_tasks)
                    max_threads = global_task_manager.max_threads
                    
                    if active_threads < max_threads:
                        # 有空位，提交任务
                        global_task_manager.submit_task(
                            platform_name="即梦账号",
                            task_callable=_process_cookie_task,
                            task_id=account.id,
                            account_id=account.id,
                            account_email=account.account,
                            task_type="获取Cookie",
                            prompt=f"获取账号 {account.account} 的Cookie"
                        )
                        print(f"已提交未设置Cookie账号 {account.account} 的获取任务")
                        break
                    else:
                        # 线程池满了，等待一会再检查
                        print(f"线程池已满，等待空位提交账号 {account.account} 的任务...")
                        time.sleep(2)
                
                # 稍微延迟一下，避免过快提交
                time.sleep(0.5)
            
            print(f"所有未设置Cookie账号的获取任务已成功提交完成，共 {len(uncookied_accounts)} 个账号")
        
        # 启动后台线程
        update_thread = threading.Thread(target=batch_get_uncookied_accounts, daemon=True)
        update_thread.start()
        
        print(f"开始批量获取未设置Cookie账号的Cookie，账号数量: {len(uncookied_accounts)}")
        return jsonify({
            'success': True,
            'message': f'正在获取 {len(uncookied_accounts)} 个未设置Cookie账号的Cookie，任务将智能调度到线程池中...'
        })
        
    except Exception as e:
        print(f"获取未设置Cookie账号异常: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取未设置Cookie账号失败: {str(e)}'
        }), 500

def _process_login_task(account_id, account_email, account_password):
    """处理登录任务（使用jimeng_login_window）"""
    try:
        print(f"开始登录账号: {account_email}")
        
        # 获取账号信息
        account = JimengAccount.get_by_id(account_id)
        
        # 调用登录窗口模块进行登录 (使用asyncio.run执行异步函数)
        result = asyncio.run(login_and_wait(account.account, account.password, account.cookies))
        
        if result["code"] == 200 and result["data"]:
            # 更新账号的Cookie
            account.cookies = result["data"]
            account.updated_at = datetime.now()
            account.save()
            print(f"账号 {account.account} 登录成功，Cookie已更新")
            return True
        else:
            print(f"账号 {account.account} 登录失败: {result['message']}")
            return False
    except Exception as e:
        print(f"处理登录任务异常，账号: {account_email}, 错误: {str(e)}")
        return False

def _process_cookie_task(account_id, account_email):
    """处理获取Cookie的任务"""
    try:
        print(f"开始获取账号Cookie: {account_email}")
        
        # 获取账号信息
        account = JimengAccount.get_by_id(account_id)
        
        # 调用登录模块获取Cookie (使用asyncio.run执行异步函数)
        result = asyncio.run(login_and_get_cookie(account.account, account.password, headless=True))
        
        if result["code"] == 200 and result["data"]:
            # 更新账号的Cookie
            account.cookies = result["data"]
            account.updated_at = datetime.now()
            account.save()
            print(f"账号 {account.account} 的Cookie获取成功并已更新")
            return True
        else:
            print(f"账号 {account.account} 的Cookie获取失败: {result['message']}")
            return False
    except Exception as e:
        print(f"处理Cookie任务异常，账号: {account_email}, 错误: {str(e)}")
        return False