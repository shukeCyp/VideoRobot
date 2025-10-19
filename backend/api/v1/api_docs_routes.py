# -*- coding: utf-8 -*-
"""
API文档路由 - 使用Flask-RESTX提供Swagger UI
"""

from flask import Blueprint
from flask_restx import Api, Resource, fields
from datetime import datetime

# 创建蓝图
api_docs_bp = Blueprint('api_docs', __name__, url_prefix='/api-docs')

# 创建API实例
api = Api(
    api_docs_bp,
    version='1.0',
    title='VideoRobot API文档',
    description='VideoRobot后端API接口文档，包含即梦文生图、图生视频、数字人等功能',
    doc='/',
    contact='舒克AI团队',
    contact_email='support@shukeai.com'
)

# 定义API命名空间
common_ns = api.namespace('common', description='通用接口')
jimeng_text2img_ns = api.namespace('jimeng/text2img', description='即梦文生图接口')
jimeng_img2img_ns = api.namespace('jimeng/img2img', description='即梦图生图接口')
jimeng_img2video_ns = api.namespace('jimeng/img2video', description='即梦图生视频接口')
jimeng_digital_human_ns = api.namespace('jimeng/digital-human', description='即梦数字人接口')
qingying_img2video_ns = api.namespace('qingying/img2video', description='清影图生视频接口')
accounts_ns = api.namespace('accounts', description='账号管理接口')
task_manager_ns = api.namespace('task-manager', description='任务管理接口')
prompt_ns = api.namespace('prompt', description='提示词管理接口')

# 定义数据模型
task_response_model = api.model('TaskResponse', {
    'success': fields.Boolean(description='操作是否成功'),
    'message': fields.String(description='响应消息'),
    'data': fields.Raw(description='响应数据')
})

pagination_model = api.model('Pagination', {
    'total': fields.Integer(description='总记录数'),
    'page': fields.Integer(description='当前页码'),
    'page_size': fields.Integer(description='每页记录数'),
    'total_pages': fields.Integer(description='总页数')
})

health_model = api.model('HealthResponse', {
    'success': fields.Boolean(description='服务是否正常'),
    'message': fields.String(description='状态消息'),
    'timestamp': fields.String(description='时间戳')
})

# 通用接口
@common_ns.route('/health')
class HealthCheck(Resource):
    @common_ns.doc('health_check')
    @common_ns.marshal_with(health_model)
    def get(self):
        """健康检查接口"""
        return {
            'success': True,
            'message': '服务正常运行',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# 即梦文生图接口文档
@jimeng_text2img_ns.route('/tasks')
class JimengText2ImgTasks(Resource):
    @jimeng_text2img_ns.doc('get_text2img_tasks')
    @jimeng_text2img_ns.param('page', '页码', type=int, default=1)
    @jimeng_text2img_ns.param('page_size', '每页数量', type=int, default=10)
    @jimeng_text2img_ns.param('status', '任务状态', enum=['0', '1', '2', '3'])
    def get(self):
        """获取文生图任务列表"""
        return {
            'success': True,
            'message': '获取任务列表成功',
            'data': [],
            'pagination': {
                'total': 0,
                'page': 1,
                'page_size': 10,
                'total_pages': 0
            }
        }

    @jimeng_text2img_ns.doc('create_text2img_task')
    @jimeng_text2img_ns.expect(api.model('CreateText2ImgTask', {
        'prompt': fields.String(required=True, description='提示词'),
        'model': fields.String(required=True, description='模型'),
        'aspect_ratio': fields.String(required=True, description='画面比例'),
        'quality': fields.String(required=True, description='图片质量'),
        'account_id': fields.Integer(description='账号ID')
    }))
    @jimeng_text2img_ns.marshal_with(task_response_model)
    def post(self):
        """创建文生图任务"""
        return {
            'success': True,
            'message': '任务创建成功',
            'data': {
                'id': 1,
                'status': 0,
                'status_text': '排队中',
                'create_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

@jimeng_text2img_ns.route('/tasks/<int:task_id>')
class JimengText2ImgTask(Resource):
    @jimeng_text2img_ns.doc('delete_text2img_task')
    @jimeng_text2img_ns.param('task_id', '任务ID')
    @jimeng_text2img_ns.marshal_with(task_response_model)
    def delete(self, task_id):
        """删除文生图任务"""
        return {
            'success': True,
            'message': '任务删除成功'
        }

@jimeng_text2img_ns.route('/tasks/<int:task_id>/retry')
class JimengText2ImgTaskRetry(Resource):
    @jimeng_text2img_ns.doc('retry_text2img_task')
    @jimeng_text2img_ns.param('task_id', '任务ID')
    @jimeng_text2img_ns.marshal_with(task_response_model)
    def post(self, task_id):
        """重试文生图任务"""
        return {
            'success': True,
            'message': '任务已重新加入队列'
        }

@jimeng_text2img_ns.route('/stats')
class JimengText2ImgStats(Resource):
    @jimeng_text2img_ns.doc('get_text2img_stats')
    @jimeng_text2img_ns.marshal_with(task_response_model)
    def get(self):
        """获取文生图任务统计信息"""
        return {
            'success': True,
            'message': '统计信息获取成功',
            'data': {
                'total': 0,
                'queued': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0
            }
        }

# 即梦图生图接口文档（类似结构）
@jimeng_img2img_ns.route('/tasks')
class JimengImg2ImgTasks(Resource):
    @jimeng_img2img_ns.doc('get_img2img_tasks')
    def get(self):
        """获取图生图任务列表"""
        return {'success': True, 'message': '获取任务列表成功'}

    @jimeng_img2img_ns.doc('create_img2img_task')
    def post(self):
        """创建图生图任务"""
        return {'success': True, 'message': '任务创建成功'}

# 即梦图生视频接口文档
@jimeng_img2video_ns.route('/tasks')
class JimengImg2VideoTasks(Resource):
    @jimeng_img2video_ns.doc('get_img2video_tasks')
    def get(self):
        """获取图生视频任务列表"""
        return {'success': True, 'message': '获取任务列表成功'}

    @jimeng_img2video_ns.doc('create_img2video_task')
    def post(self):
        """创建图生视频任务"""
        return {'success': True, 'message': '任务创建成功'}

# 即梦数字人接口文档
@jimeng_digital_human_ns.route('/tasks')
class JimengDigitalHumanTasks(Resource):
    @jimeng_digital_human_ns.doc('get_digital_human_tasks')
    def get(self):
        """获取数字人任务列表"""
        return {'success': True, 'message': '获取任务列表成功'}

    @jimeng_digital_human_ns.doc('create_digital_human_task')
    def post(self):
        """创建数字人任务"""
        return {'success': True, 'message': '任务创建成功'}

# 清影图生视频接口文档
@qingying_img2video_ns.route('/tasks')
class QingyingImg2VideoTasks(Resource):
    @qingying_img2video_ns.doc('get_qingying_img2video_tasks')
    def get(self):
        """获取清影图生视频任务列表"""
        return {'success': True, 'message': '获取任务列表成功'}

    @qingying_img2video_ns.doc('create_qingying_img2video_task')
    def post(self):
        """创建清影图生视频任务"""
        return {'success': True, 'message': '任务创建成功'}

# 账号管理接口文档
@accounts_ns.route('/jimeng')
class JimengAccounts(Resource):
    @accounts_ns.doc('get_jimeng_accounts')
    def get(self):
        """获取即梦账号列表"""
        return {'success': True, 'message': '获取账号列表成功'}

    @accounts_ns.doc('add_jimeng_account')
    def post(self):
        """添加即梦账号"""
        return {'success': True, 'message': '账号添加成功'}

@accounts_ns.route('/qingying')
class QingyingAccounts(Resource):
    @accounts_ns.doc('get_qingying_accounts')
    def get(self):
        """获取清影账号列表"""
        return {'success': True, 'message': '获取账号列表成功'}

    @accounts_ns.doc('add_qingying_account')
    def post(self):
        """添加清影账号"""
        return {'success': True, 'message': '账号添加成功'}

# 任务管理器接口文档
@task_manager_ns.route('/overview')
class TaskManagerOverview(Resource):
    @task_manager_ns.doc('get_task_overview')
    def get(self):
        """获取任务总览"""
        return {
            'success': True,
            'message': '获取任务总览成功',
            'data': {
                'total_tasks': 0,
                'running_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0
            }
        }

# 提示词管理接口文档
@prompt_ns.route('/prompts')
class Prompts(Resource):
    @prompt_ns.doc('get_prompts')
    def get(self):
        """获取提示词列表"""
        return {'success': True, 'message': '获取提示词列表成功'}

    @prompt_ns.doc('create_prompt')
    def post(self):
        """创建提示词"""
        return {'success': True, 'message': '提示词创建成功'}

# 添加所有命名空间到API
api.add_namespace(common_ns)
api.add_namespace(jimeng_text2img_ns)
api.add_namespace(jimeng_img2img_ns)
api.add_namespace(jimeng_img2video_ns)
api.add_namespace(jimeng_digital_human_ns)
api.add_namespace(qingying_img2video_ns)
api.add_namespace(accounts_ns)
api.add_namespace(task_manager_ns)
api.add_namespace(prompt_ns)