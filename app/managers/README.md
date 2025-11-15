# 任务管理器框架说明

## 架构概览

```
GlobalTaskManager (全局任务管理器)
├── ThreadPoolExecutor (线程池)
├── 轮询循环 (每N秒检查一次)
└── TaskExecutors (任务执行器列表)
    ├── JimengImageTaskExecutor
    ├── QingyingVideoTaskExecutor (待实现)
    └── 其他执行器...
```

## 核心组件

### 1. BaseTaskExecutor (基类)
**文件**: `base_task_executor.py`

所有任务执行器的基类，定义了标准接口：

- `get_task_type()`: 返回任务类型名称
- `get_pending_tasks(limit)`: 获取待执行的任务列表
- `execute_task(task)`: 执行单个任务的具体逻辑
- `update_task_status(task, status, error_message)`: 更新任务状态
- `run_task(task)`: 任务执行的包装方法（已实现，处理异常和状态更新）

### 2. JimengImageTaskExecutor (即梦图片任务执行器)
**文件**: `jimeng_image_task_executor.py`

即梦图片生成任务的执行器，需要实现：

#### TODO - get_pending_tasks():
```python
# 从数据库查询status='pending'的任务
# 使用 JimengImageTask.select().where(status='pending').limit(limit)
# 返回任务列表
```

#### TODO - execute_task():
```python
# 1. 打开即梦网站/API
# 2. 输入提示词 (task.prompt)
# 3. 上传参考图片 (task.get_input_image_paths())
# 4. 设置参数:
#    - 模型: task.image_model
#    - 比例: task.aspect_ratio
#    - 分辨率: task.resolution
# 5. 提交生成请求
# 6. 等待结果
# 7. 下载生成的图片
# 8. 调用 JimengImageTask.update_task_outputs(task.id, [图片路径列表])
# 9. 返回 True (成功) 或 False (失败)
```

#### TODO - update_task_status():
```python
# 调用 JimengImageTask.update_task_status(task.id, status, error_message)
```

### 3. GlobalTaskManager (全局任务管理器)
**文件**: `global_task_manager.py`

核心调度器，功能：

#### 已实现功能：
- 线程池管理
- 轮询循环框架
- 执行器注册
- 配置更新（线程池大小、轮询间隔）
- 信号发送（任务开始/完成/状态变化）

#### TODO - run() 方法中的轮询逻辑：
```python
while self.is_running:
    # 1. 遍历所有执行器
    for executor in self.executors:
        # 2. 获取待执行任务（数量不超过剩余线程数）
        pending_tasks = executor.get_pending_tasks(limit=剩余线程数)

        # 3. 提交任务到线程池
        for task in pending_tasks:
            if 线程池有空闲:
                self.submit_task(executor, task)

    # 4. 休眠等待下次轮询
    time.sleep(self.poll_interval)
```

#### TODO - submit_task() 方法：
```python
def submit_task(self, executor, task):
    # 1. 发送任务开始信号
    self.task_started.emit(executor.task_type, task.id)

    # 2. 定义完成回调
    def task_done(future):
        try:
            success = future.result()
            self.task_finished.emit(executor.task_type, task.id, success)
        except Exception as e:
            log.error(f"任务执行异常: {e}")
            self.task_finished.emit(executor.task_type, task.id, False)

    # 3. 提交到线程池
    future = self.thread_pool.submit(executor.run_task, task)
    future.add_done_callback(task_done)
```

## 设置界面集成

**文件**: `app/view/settings_interface.py`

### TODO - onStartTaskManager():
```python
# 1. 获取全局任务管理器
from app.managers.global_task_manager import get_global_task_manager
manager = get_global_task_manager()

# 2. 设置参数
manager.set_max_workers(self.thread_pool_spin.value())
manager.set_poll_interval(self.poll_interval_spin.value())

# 3. 启动
if not manager.isRunning():
    manager.start()

# 4. 连接信号
manager.status_changed.connect(self.onStatusChanged)
manager.task_started.connect(self.onTaskStarted)
manager.task_finished.connect(self.onTaskFinished)
```

### TODO - onStopTaskManager():
```python
# 1. 获取全局任务管理器
manager = get_global_task_manager()

# 2. 停止
manager.stop()

# 3. 等待线程结束
manager.wait()
```

## 添加新的任务类型

### 步骤：

1. **创建新的执行器类**
   ```python
   # app/managers/your_task_executor.py
   from app.managers.base_task_executor import BaseTaskExecutor

   class YourTaskExecutor(BaseTaskExecutor):
       def get_task_type(self):
           return "YourTaskType"

       def get_pending_tasks(self, limit=10):
           # 实现查询逻辑
           pass

       def execute_task(self, task):
           # 实现执行逻辑
           pass

       def update_task_status(self, task, status, error_message=""):
           # 实现状态更新
           pass
   ```

2. **注册到全局管理器**
   在 `global_task_manager.py` 的 `register_executors()` 方法中：
   ```python
   from app.managers.your_task_executor import YourTaskExecutor

   def register_executors(self):
       self.executors.append(JimengImageTaskExecutor())
       self.executors.append(YourTaskExecutor())  # 添加这行
   ```

## 使用示例

```python
# 在应用启动时
from app.managers.global_task_manager import get_global_task_manager

# 获取管理器
manager = get_global_task_manager()

# 配置
manager.set_max_workers(5)  # 5个线程
manager.set_poll_interval(3)  # 每3秒检查一次

# 启动
manager.start()

# 停止
manager.stop()
manager.wait()
```

## 信号说明

- `task_started(task_type: str, task_id: int)`: 任务开始执行
- `task_finished(task_type: str, task_id: int, success: bool)`: 任务执行完成
- `status_changed(message: str)`: 管理器状态变化

## 注意事项

1. 所有执行器的 `execute_task()` 方法都在线程池中运行，不要在其中操作UI
2. 使用信号与UI通信
3. 任务执行过程中的异常会被 `run_task()` 捕获并自动更新任务状态为失败
4. 线程池大小建议根据CPU核心数和任务性质设置（1-10之间）
5. 轮询间隔不宜过短，建议3-10秒
