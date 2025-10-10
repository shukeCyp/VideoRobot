from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup, SettingCard,
                            SpinBox, BodyLabel, PrimaryPushButton,
                            InfoBar, InfoBarPosition, FluentIcon as FIF)
from app.utils.logger import log


class SettingsInterface(ScrollArea):
    """设置界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 设置样式
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QWidget#scrollWidget {
                background-color: transparent;
            }
        """)

        self.initUI()
        self.updateManagerStatus()

    def updateManagerStatus(self):
        """更新任务管理器状态显示"""
        from app.managers.global_task_manager import get_global_task_manager

        manager = get_global_task_manager()

        if manager.isRunning():
            # 更新SpinBox的值
            status = manager.get_status()
            self.thread_pool_spin.setValue(status['max_workers'])
            self.poll_interval_spin.setValue(status['poll_interval'])

            # 更新UI状态
            self.status_label.setText("运行中")
            self.status_label.setStyleSheet("color: rgba(0, 255, 0, 0.8); font-weight: bold;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.thread_pool_spin.setEnabled(False)
            self.poll_interval_spin.setEnabled(False)
        else:
            self.status_label.setText("未启动")
            self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-weight: bold;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.thread_pool_spin.setEnabled(True)
            self.poll_interval_spin.setEnabled(True)

    def initUI(self):
        """初始化UI"""
        self.scrollWidget.setObjectName('scrollWidget')

        # 设置布局
        self.expandLayout.setContentsMargins(40, 20, 40, 20)
        self.expandLayout.setSpacing(20)

        # 任务管理器设置组
        self.task_manager_group = SettingCardGroup("任务管理器", self.scrollWidget)

        # 线程池大小设置卡片
        self.thread_pool_card = SettingCard(
            FIF.PEOPLE,
            "线程池大小",
            "同时执行的最大任务数量",
            self.task_manager_group
        )

        # 添加 SpinBox 到卡片
        self.thread_pool_spin = SpinBox(self.thread_pool_card)
        self.thread_pool_spin.setRange(1, 10)
        self.thread_pool_spin.setValue(3)
        self.thread_pool_spin.setFixedWidth(120)
        self.thread_pool_card.hBoxLayout.addWidget(self.thread_pool_spin, 0, Qt.AlignRight)
        self.thread_pool_card.hBoxLayout.addSpacing(16)

        # 轮询间隔设置卡片
        self.poll_interval_card = SettingCard(
            FIF.CALENDAR,
            "轮询间隔",
            "检查新任务的时间间隔（秒）",
            self.task_manager_group
        )

        # 添加 SpinBox 到卡片
        self.poll_interval_spin = SpinBox(self.poll_interval_card)
        self.poll_interval_spin.setRange(1, 60)
        self.poll_interval_spin.setValue(5)
        self.poll_interval_spin.setFixedWidth(120)
        self.poll_interval_card.hBoxLayout.addWidget(self.poll_interval_spin, 0, Qt.AlignRight)
        self.poll_interval_card.hBoxLayout.addSpacing(16)

        # 创建控制面板卡片
        self.control_card = SettingCard(
            FIF.PLAY,
            "任务管理器控制",
            "启动或停止任务管理器",
            self.task_manager_group
        )

        # 创建控制按钮容器
        control_container = QWidget(self.control_card)
        control_layout = QHBoxLayout(control_container)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        self.status_label = BodyLabel("未启动", control_container)
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-weight: bold;")
        control_layout.addWidget(self.status_label)

        self.start_btn = PrimaryPushButton(FIF.PLAY, "启动", control_container)
        self.start_btn.clicked.connect(self.onStartTaskManager)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = PrimaryPushButton(FIF.PAUSE, "停止", control_container)
        self.stop_btn.clicked.connect(self.onStopTaskManager)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        self.control_card.hBoxLayout.addWidget(control_container, 0, Qt.AlignRight)
        self.control_card.hBoxLayout.addSpacing(16)

        # 添加到组
        self.task_manager_group.addSettingCard(self.thread_pool_card)
        self.task_manager_group.addSettingCard(self.poll_interval_card)
        self.task_manager_group.addSettingCard(self.control_card)

        # 添加到布局
        self.expandLayout.addWidget(self.task_manager_group)

    def onStartTaskManager(self):
        """启动任务管理器"""
        from app.managers.global_task_manager import get_global_task_manager

        max_workers = self.thread_pool_spin.value()
        poll_interval = self.poll_interval_spin.value()

        log.info(f"启动任务管理器: 线程池={max_workers}, 轮询间隔={poll_interval}秒")

        manager = get_global_task_manager()
        manager.set_max_workers(max_workers)
        manager.set_poll_interval(poll_interval)

        if not manager.isRunning():
            manager.start()

        self.status_label.setText("运行中")
        self.status_label.setStyleSheet("color: rgba(0, 255, 0, 0.8); font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.thread_pool_spin.setEnabled(False)
        self.poll_interval_spin.setEnabled(False)

        InfoBar.success(
            title="启动成功",
            content="任务管理器已启动",
            parent=self,
            position=InfoBarPosition.TOP
        )

    def onStopTaskManager(self):
        """停止任务管理器"""
        from app.managers.global_task_manager import get_global_task_manager

        log.info("停止任务管理器")

        manager = get_global_task_manager()
        manager.stop()
        manager.wait()

        self.status_label.setText("已停止")
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.thread_pool_spin.setEnabled(True)
        self.poll_interval_spin.setEnabled(True)

        InfoBar.info(
            title="已停止",
            content="任务管理器已停止",
            parent=self,
            position=InfoBarPosition.TOP
        )