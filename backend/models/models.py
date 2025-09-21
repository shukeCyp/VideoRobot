# -*- coding: utf-8 -*-
from datetime import datetime
from peewee import *

from backend.config.settings import DATABASE_PATH

# 初始化数据库连接
db = SqliteDatabase(DATABASE_PATH)

class BaseModel(Model):
    """基础模型类"""
    class Meta:
        database = db

class Config(BaseModel):
    """系统配置表"""
    key = CharField(max_length=100, unique=True)  # 配置键
    value = TextField()  # 配置值
    description = CharField(max_length=255, null=True)  # 配置描述
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'config'

class JimengAccount(BaseModel):
    """即梦账号管理"""
    account = CharField(max_length=100)
    password = CharField(max_length=100)
    cookies = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'jimeng_accounts'

class QingyingAccount(BaseModel):
    """清影账号管理"""
    nickname = CharField(max_length=100)
    phone = CharField(max_length=100)
    cookies = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'qingying_accounts'

class JimengText2ImgTask(BaseModel):
    """即梦文生图任务"""
    # 基本字段
    prompt = TextField()  # 提示词
    model = CharField(max_length=100, default="Image 3.1")  # 使用的模型
    ratio = CharField(max_length=20, default="1:1")  # 分辨率比例
    quality = CharField(max_length=20, default="1K")  # 清晰度
    
    # 状态字段 - 使用数字状态码
    # 0: 排队中, 1: 生成中, 2: 已完成, 3: 失败
    status = IntegerField(default=0)  
    
    # 关联账号
    account_id = IntegerField(null=True)  # 使用的账号ID
    
    # 生成的图片 - 4个图片字段
    image1 = CharField(max_length=500, null=True)
    image2 = CharField(max_length=500, null=True)
    image3 = CharField(max_length=500, null=True)
    image4 = CharField(max_length=500, null=True)
    
    task_id = CharField(max_length=100, null=True)  # 任务ID

    # 重试相关字段
    retry_count = IntegerField(default=0)  # 重试次数
    max_retry = IntegerField(default=10)  # 最大重试次数
    failure_reason = CharField(max_length=50, null=True)  # 失败原因类型
    error_message = TextField(null=True)  # 详细错误信息
    
    # 时间戳
    create_at = DateTimeField(default=datetime.now)
    update_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'jimeng_text2img_tasks'
        
    def get_status_text(self):
        """获取状态文字描述"""
        status_map = {
            0: '排队中',
            1: '生成中', 
            2: '已完成',
            3: '失败'
        }
        return status_map.get(self.status, '未知状态')
        
    def update_status(self, status):
        """更新任务状态"""
        self.status = status
        self.update_at = datetime.now()
        self.save()
        
    def set_images(self, image_paths):
        """设置生成的图片路径"""
        if image_paths:
            for i, path in enumerate(image_paths[:4]):  # 最多4张图片
                if i == 0:
                    self.image1 = path
                elif i == 1:
                    self.image2 = path
                elif i == 2:
                    self.image3 = path
                elif i == 3:
                    self.image4 = path
        self.update_at = datetime.now()
        self.save()
        
    def get_images(self):
        """获取所有图片路径列表"""
        images = []
        for img in [self.image1, self.image2, self.image3, self.image4]:
            if img:
                images.append(img)
        return images
    
    def can_retry(self):
        """判断任务是否可以重试"""
        # 只有网络相关的失败才能重试
        network_failure_reasons = ['WEB_INTERACTION_FAILED', 'TASK_ID_NOT_OBTAINED']
        return (self.status == 3 and  # 任务失败
                self.retry_count < self.max_retry and  # 重试次数未超限
                self.failure_reason in network_failure_reasons)  # 是网络问题
    
    def set_failure(self, error_code, error_message=None):
        """设置任务失败状态和原因"""
        self.status = 3
        self.error_message = error_message
        
        # 根据错误代码判断失败原因
        if error_code in [600, 900, 'WEB_INTERACTION_FAILED']:
            self.failure_reason = 'WEB_INTERACTION_FAILED'
        elif error_code in [700, 'TASK_ID_NOT_OBTAINED']:
            self.failure_reason = 'TASK_ID_NOT_OBTAINED'
        elif error_code in [800, 'GENERATION_FAILED']:
            self.failure_reason = 'GENERATION_FAILED'
        else:
            self.failure_reason = 'OTHER_ERROR'
        
        self.update_at = datetime.now()
        self.save()
    
    def retry_task(self):
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = 0  # 重新排队
            self.error_message = None
            self.update_at = datetime.now()
            self.save()
            return True
        return False

class JimengImg2ImgTask(BaseModel):
    """即梦图生图任务"""
    # 基本字段
    prompt = TextField()  # 提示词
    model = CharField(max_length=100, default="Nano Banana")  # 使用的模型
    ratio = CharField(max_length=20, null=True, default=None)  # 分辨率比例

    # 状态字段 - 使用数字状态码
    # 0: 排队中, 1: 生成中, 2: 已完成, 3: 失败
    status = IntegerField(default=0)

    # 关联账号
    account_id = IntegerField(null=True)  # 使用的账号ID
    
    # 输入图片 - 最多3张输入图片
    input_image1 = CharField(max_length=500, null=True)
    input_image2 = CharField(max_length=500, null=True)
    input_image3 = CharField(max_length=500, null=True)
    
    # 生成的图片 - 4个图片字段
    image1 = CharField(max_length=500, null=True)
    image2 = CharField(max_length=500, null=True)
    image3 = CharField(max_length=500, null=True)
    image4 = CharField(max_length=500, null=True)
    
    task_id = CharField(max_length=100, null=True)  # 任务ID

    # 重试相关字段
    retry_count = IntegerField(default=0)  # 重试次数
    max_retry = IntegerField(default=10)  # 最大重试次数
    failure_reason = CharField(max_length=50, null=True)  # 失败原因类型
    error_message = TextField(null=True)  # 详细错误信息
    
    # 时间戳
    create_at = DateTimeField(default=datetime.now)
    update_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'jimeng_image2image_tasks'
        
    def get_status_text(self):
        """获取状态文字描述"""
        status_map = {
            0: '排队中',
            1: '生成中', 
            2: '已完成',
            3: '失败'
        }
        return status_map.get(self.status, '未知状态')
        
    def update_status(self, status):
        """更新任务状态"""
        self.status = status
        self.update_at = datetime.now()
        self.save()
        
    def set_input_images(self, image_paths):
        """设置输入图片路径"""
        if image_paths:
            for i, path in enumerate(image_paths[:3]):  # 最多3张输入图片
                if i == 0:
                    self.input_image1 = path
                elif i == 1:
                    self.input_image2 = path
                elif i == 2:
                    self.input_image3 = path
        self.update_at = datetime.now()
        self.save()
        
    def get_input_images(self):
        """获取所有输入图片路径列表"""
        images = []
        for img in [self.input_image1, self.input_image2, self.input_image3]:
            if img:
                images.append(img)
        return images
        
    def set_images(self, image_paths):
        """设置生成的图片路径"""
        if image_paths:
            for i, path in enumerate(image_paths[:4]):  # 最多4张图片
                if i == 0:
                    self.image1 = path
                elif i == 1:
                    self.image2 = path
                elif i == 2:
                    self.image3 = path
                elif i == 3:
                    self.image4 = path
        self.update_at = datetime.now()
        self.save()
        
    def get_images(self):
        """获取所有生成图片路径列表"""
        images = []
        for img in [self.image1, self.image2, self.image3, self.image4]:
            if img:
                images.append(img)
        return images
    
    def can_retry(self):
        """判断任务是否可以重试"""
        # 对于图生图任务，允许更多类型的失败进行重试
        retryable_failure_reasons = [
            'WEB_INTERACTION_FAILED', 
            'TASK_ID_NOT_OBTAINED', 
            'OTHER_ERROR',
            'GENERATION_FAILED'
        ]
        return ((self.status == 3 or (self.status == 0 and self.failure_reason is not None)) and  # 任务失败或排队但有失败原因
                self.retry_count < self.max_retry and  # 重试次数未超限
                self.failure_reason in retryable_failure_reasons)  # 是可重试的失败
    
    def set_failure(self, error_code, error_message=None):
        """设置任务失败状态和原因"""
        self.status = 3
        self.error_message = error_message
        
        # 根据错误代码判断失败原因
        if error_code in [600, 900, 'WEB_INTERACTION_FAILED']:
            self.failure_reason = 'WEB_INTERACTION_FAILED'
        elif error_code in [700, 'TASK_ID_NOT_OBTAINED']:
            self.failure_reason = 'TASK_ID_NOT_OBTAINED'
        elif error_code in [800, 'GENERATION_FAILED']:
            self.failure_reason = 'GENERATION_FAILED'
        else:
            self.failure_reason = 'OTHER_ERROR'
        
        self.update_at = datetime.now()
        self.save()
    
    def retry_task(self):
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = 0  # 重新排队
            self.error_message = None
            self.update_at = datetime.now()
            self.save()
            return True
        return False

class JimengImg2VideoTask(BaseModel):
    """即梦图生视频任务"""
    # 基本字段
    prompt = TextField()  # 提示词
    model = CharField(max_length=100, default="Video 1.0")  # 使用的模型
    second = IntegerField(default=5)  # 视频时长（秒）
    
    # 状态字段 - 使用数字状态码
    # 0: 排队中, 1: 生成中, 2: 已完成, 3: 失败
    status = IntegerField(default=0)
    
    # 关联账号
    account_id = IntegerField(null=True)  # 使用的账号ID
    
    # 输入图片和输出视频
    image_path = CharField(max_length=500, null=True)  # 输入图片路径
    video_url = CharField(max_length=500, null=True)  # 生成的视频URL
    
    task_id = CharField(max_length=100, null=True)  # 任务ID

    # 重试相关字段
    retry_count = IntegerField(default=0)  # 重试次数
    max_retry = IntegerField(default=10)  # 最大重试次数
    failure_reason = CharField(max_length=50, null=True)  # 失败原因类型
    error_message = TextField(null=True)  # 详细错误信息
    
    # 时间戳
    create_at = DateTimeField(default=datetime.now)
    update_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'jimeng_img2video_tasks'
        
    def get_status_text(self):
        """获取状态文字描述"""
        status_map = {
            0: '排队中',
            1: '生成中', 
            2: '已完成',
            3: '失败'
        }
        return status_map.get(self.status, '未知状态')
        
    def update_status(self, status):
        """更新任务状态"""
        self.status = status
        self.update_at = datetime.now()
        self.save()
    
    def can_retry(self):
        """判断任务是否可以重试"""
        # 只有网络相关的失败才能重试
        network_failure_reasons = ['WEB_INTERACTION_FAILED', 'TASK_ID_NOT_OBTAINED']
        return (self.status == 3 and  # 任务失败
                self.retry_count < self.max_retry and  # 重试次数未超限
                self.failure_reason in network_failure_reasons)  # 是网络问题
    
    def set_failure(self, error_code, error_message=None):
        """设置任务失败状态和原因"""
        self.status = 3
        self.error_message = error_message
        
        # 根据错误代码判断失败原因
        if error_code in [600, 900, 'WEB_INTERACTION_FAILED']:
            self.failure_reason = 'WEB_INTERACTION_FAILED'
        elif error_code in [700, 'TASK_ID_NOT_OBTAINED']:
            self.failure_reason = 'TASK_ID_NOT_OBTAINED'
        elif error_code in [800, 'GENERATION_FAILED']:
            self.failure_reason = 'GENERATION_FAILED'
        else:
            self.failure_reason = 'OTHER_ERROR'
        
        self.update_at = datetime.now()
        self.save()
    
    def retry_task(self):
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = 0  # 重新排队
            self.error_message = None
            self.update_at = datetime.now()
            self.save()
            return True
        return False

class JimengDigitalHumanTask(BaseModel):
    """即梦数字人任务"""
    # 基本字段
    image_path = CharField(max_length=500)  # 图片路径
    audio_path = CharField(max_length=500)  # 音频路径
    
    # 状态字段 - 使用数字状态码
    # 0: 排队中, 1: 生成中, 2: 已完成, 3: 失败
    status = IntegerField(default=0)
    
    # 关联账号
    account_id = IntegerField(null=True)  # 使用的账号ID
    
    # 时间字段
    create_at = DateTimeField(default=datetime.now)  # 创建时间
    start_time = DateTimeField(null=True)  # 开始处理时间
    
    # 结果字段
    video_url = TextField(null=True)  # 生成的视频URL

    task_id = CharField(max_length=100, null=True)  # 任务ID
    
    # 重试相关字段
    retry_count = IntegerField(default=0)  # 重试次数
    max_retry = IntegerField(default=10)  # 最大重试次数
    failure_reason = CharField(max_length=50, null=True)  # 失败原因类型
    error_message = TextField(null=True)  # 详细错误信息
    
    class Meta:
        table_name = 'jimeng_digital_human_tasks'
    
    def can_retry(self):
        """判断任务是否可以重试"""
        # 只有网络相关的失败才能重试
        network_failure_reasons = ['WEB_INTERACTION_FAILED', 'TASK_ID_NOT_OBTAINED']
        return (self.status == 3 and  # 任务失败
                self.retry_count < self.max_retry and  # 重试次数未超限
                self.failure_reason in network_failure_reasons)  # 是网络问题
    
    def set_failure(self, error_code, error_message=None):
        """设置任务失败状态和原因"""
        self.status = 3
        self.error_message = error_message
        
        # 根据错误代码判断失败原因
        if error_code in [600, 900, 'WEB_INTERACTION_FAILED']:
            self.failure_reason = 'WEB_INTERACTION_FAILED'
        elif error_code in [700, 'TASK_ID_NOT_OBTAINED']:
            self.failure_reason = 'TASK_ID_NOT_OBTAINED'
        elif error_code in [800, 'GENERATION_FAILED']:
            self.failure_reason = 'GENERATION_FAILED'
        else:
            self.failure_reason = 'OTHER_ERROR'
        
        self.update_at = datetime.now()
        self.save()
    
    def retry_task(self):
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = 0  # 重新排队
            self.error_message = None
            self.update_at = datetime.now()
            self.save()
            return True
        return False

# 即梦任务记录
class JimengTaskRecord(BaseModel):
    """即梦任务记录"""
    account_id = IntegerField(null=True)  # 使用的账号ID
    
    # 关联的即梦账号
    jimeng_account = ForeignKeyField(JimengAccount, null=True, backref='jimeng_records')

    task_type = IntegerField(null=True)  # 任务类型 1是文生图，2是图生视频， 3是数字人， 4是图生图
    # 时间戳
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'jimeng_task_records'

class QingyingImage2VideoTask(BaseModel):
    """清影图生视频任务"""
    # 基本字段
    prompt = TextField()  # 提示词
    generation_mode = CharField(max_length=100, default="fast")  # 生成模式
    frame_rate = CharField(max_length=100, default="30")  # 帧率
    resolution = CharField(max_length=100, default="720p")  # 分辨率
    duration = CharField(max_length=100, default="5s")  # 视频时长
    ai_audio = BooleanField(default=False)  # AI音效
    
    # 状态字段 - 使用数字状态码
    # 0: 排队中, 1: 生成中, 2: 已完成, 3: 失败
    status = IntegerField(default=0)
    
    # 关联账号
    account_id = IntegerField(null=True)  # 使用的账号ID
    
    # 输入图片和输出视频
    image_path = CharField(max_length=500, null=True)  # 输入图片路径
    video_url = CharField(max_length=500, null=True)  # 生成的视频URL
    
    # 重试相关字段
    retry_count = IntegerField(default=0)  # 重试次数
    max_retry = IntegerField(default=10)  # 最大重试次数
    failure_reason = CharField(max_length=50, null=True)  # 失败原因类型
    error_message = TextField(null=True)  # 详细错误信息
    
    # 时间戳
    create_at = DateTimeField(default=datetime.now)
    update_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'qingying_image2video_tasks'
        
    def get_status_text(self):
        """获取状态文字描述"""
        status_map = {
            0: '排队中',
            1: '生成中', 
            2: '已完成',
            3: '失败'
        }
        return status_map.get(self.status, '未知状态')
        
    def update_status(self, status):
        """更新任务状态"""
        self.status = status
        self.update_at = datetime.now()
        self.save()
    
    def can_retry(self):
        """判断任务是否可以重试"""
        # 只有网络相关的失败才能重试
        network_failure_reasons = ['WEB_INTERACTION_FAILED', 'TASK_ID_NOT_OBTAINED']
        return (self.status == 3 and  # 任务失败
                self.retry_count < self.max_retry and  # 重试次数未超限
                self.failure_reason in network_failure_reasons)  # 是网络问题
    
    def set_failure(self, error_code, error_message=None):
        """设置任务失败状态和原因"""
        self.status = 3
        self.error_message = error_message
        
        # 根据错误代码判断失败原因
        if error_code in [600, 900, 'WEB_INTERACTION_FAILED']:
            self.failure_reason = 'WEB_INTERACTION_FAILED'
        elif error_code in [700, 'TASK_ID_NOT_OBTAINED']:
            self.failure_reason = 'TASK_ID_NOT_OBTAINED'
        elif error_code in [800, 'GENERATION_FAILED']:
            self.failure_reason = 'GENERATION_FAILED'
        else:
            self.failure_reason = 'OTHER_ERROR'
        
        self.update_at = datetime.now()
        self.save()
    
    def retry_task(self):
        """重试任务"""
        if self.can_retry():
            self.retry_count += 1
            self.status = 0  # 重新排队
            self.error_message = None
            self.update_at = datetime.now()
            self.save()
            return True
        return False