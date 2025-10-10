from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog
from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup, SettingCard,
                            SpinBox, BodyLabel, PrimaryPushButton,
                            InfoBar, InfoBarPosition, FluentIcon as FIF,
                            MessageBox)
from app.utils.logger import log
from app.utils.log_manager import get_log_manager


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

        # 日志管理设置组
        self.log_manager_group = SettingCardGroup("日志管理", self.scrollWidget)

        # 日志信息显示卡片
        self.log_info_card = SettingCard(
            FIF.DOCUMENT,
            "日志信息",
            "查看当前日志文件大小",
            self.log_manager_group
        )

        # 添加日志信息显示
        log_info_container = QWidget(self.log_info_card)
        log_info_layout = QHBoxLayout(log_info_container)
        log_info_layout.setContentsMargins(0, 0, 0, 0)
        log_info_layout.setSpacing(10)

        self.log_size_label = BodyLabel("计算中...", log_info_container)
        self.log_size_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: bold;")
        log_info_layout.addWidget(self.log_size_label)

        self.refresh_log_btn = PrimaryPushButton(FIF.SYNC, "刷新", log_info_container)
        self.refresh_log_btn.clicked.connect(self.onRefreshLogInfo)
        log_info_layout.addWidget(self.refresh_log_btn)

        self.log_info_card.hBoxLayout.addWidget(log_info_container, 0, Qt.AlignRight)
        self.log_info_card.hBoxLayout.addSpacing(16)

        # 清除日志卡片
        self.clear_log_card = SettingCard(
            FIF.DELETE,
            "清除日志",
            "删除所有日志文件以释放空间",
            self.log_manager_group
        )

        self.clear_log_btn = PrimaryPushButton(FIF.DELETE, "清除日志", self.clear_log_card)
        self.clear_log_btn.clicked.connect(self.onClearLogs)
        self.clear_log_card.hBoxLayout.addWidget(self.clear_log_btn, 0, Qt.AlignRight)
        self.clear_log_card.hBoxLayout.addSpacing(16)

        # 打包日志卡片
        self.pack_log_card = SettingCard(
            FIF.ZIP_FOLDER,
            "打包日志",
            "将日志文件打包为 ZIP 压缩包",
            self.log_manager_group
        )

        self.pack_log_btn = PrimaryPushButton(FIF.ZIP_FOLDER, "打包日志", self.pack_log_card)
        self.pack_log_btn.clicked.connect(self.onPackLogs)
        self.pack_log_card.hBoxLayout.addWidget(self.pack_log_btn, 0, Qt.AlignRight)
        self.pack_log_card.hBoxLayout.addSpacing(16)

        # 添加到组
        self.log_manager_group.addSettingCard(self.log_info_card)
        self.log_manager_group.addSettingCard(self.clear_log_card)
        self.log_manager_group.addSettingCard(self.pack_log_card)

        # 添加到布局
        self.expandLayout.addWidget(self.log_manager_group)

        # 关于应用设置组
        self.about_group = SettingCardGroup("关于", self.scrollWidget)

        # 版本信息卡片
        self.version_card = SettingCard(
            FIF.INFO,
            "版本信息",
            self._get_version_description(),
            self.about_group
        )

        # 添加版本号显示
        version_container = QWidget(self.version_card)
        version_layout = QHBoxLayout(version_container)
        version_layout.setContentsMargins(0, 0, 0, 0)
        version_layout.setSpacing(10)

        self.version_label = BodyLabel(f"v{self._get_current_version()}", version_container)
        self.version_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: bold; font-size: 14px;")
        version_layout.addWidget(self.version_label)

        self.check_update_btn = PrimaryPushButton(FIF.UPDATE, "检查更新", version_container)
        self.check_update_btn.clicked.connect(self.onCheckUpdate)
        version_layout.addWidget(self.check_update_btn)

        self.version_card.hBoxLayout.addWidget(version_container, 0, Qt.AlignRight)
        self.version_card.hBoxLayout.addSpacing(16)

        # 添加到组
        self.about_group.addSettingCard(self.version_card)

        # 添加到布局
        self.expandLayout.addWidget(self.about_group)

        # 初始化日志信息
        self.onRefreshLogInfo()

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

    def onRefreshLogInfo(self):
        """刷新日志信息"""
        try:
            log_manager = get_log_manager()
            total_size, formatted_size = log_manager.get_log_size()
            file_count = log_manager.get_log_files_count()

            self.log_size_label.setText(f"{formatted_size} ({file_count} 个文件)")
            log.debug(f"日志信息已刷新: {formatted_size}, {file_count} 个文件")

        except Exception as e:
            self.log_size_label.setText("获取失败")
            log.error(f"刷新日志信息失败: {str(e)}")

    def onClearLogs(self):
        """清除日志"""
        # 显示确认对话框
        w = MessageBox(
            "确认清除",
            "确定要删除所有日志文件吗？此操作不可恢复！",
            self
        )
        w.yesButton.setText("确定")
        w.cancelButton.setText("取消")

        if w.exec():
            try:
                log_manager = get_log_manager()
                success, message = log_manager.clear_logs()

                if success:
                    InfoBar.success(
                        title="清除成功",
                        content=message,
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                    # 刷新日志信息
                    self.onRefreshLogInfo()
                else:
                    InfoBar.error(
                        title="清除失败",
                        content=message,
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )

            except Exception as e:
                InfoBar.error(
                    title="清除失败",
                    content=f"发生错误: {str(e)}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )

    def onPackLogs(self):
        """打包日志"""
        try:
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存日志压缩包",
                f"logs_backup_{self._get_timestamp()}.zip",
                "ZIP 文件 (*.zip)"
            )

            if not file_path:
                return

            log_manager = get_log_manager()
            success, result = log_manager.pack_logs(file_path)

            if success:
                InfoBar.success(
                    title="打包成功",
                    content=f"日志已保存到: {result}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
            else:
                InfoBar.error(
                    title="打包失败",
                    content=result,
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )

        except Exception as e:
            InfoBar.error(
                title="打包失败",
                content=f"发生错误: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def _get_timestamp(self):
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _get_current_version(self):
        """获取当前版本号"""
        try:
            from app.version import __version__
            return __version__
        except Exception as e:
            log.error(f"获取版本号失败: {str(e)}")
            return "未知"

    def _get_version_description(self):
        """获取版本描述"""
        try:
            from app.version import __version__, __app_name__
            return f"{__app_name__} - 当前版本"
        except Exception:
            return "当前版本"

    def onCheckUpdate(self):
        """检查更新"""
        try:
            from app.utils.update_manager import get_update_manager
            from app.view.update_dialog import UpdateDialog

            # 禁用按钮
            self.check_update_btn.setEnabled(False)
            self.check_update_btn.setText("检查中...")

            log.info("用户手动检查更新...")

            manager = get_update_manager()
            update_thread = manager.check_for_updates()

            if not update_thread:
                log.warning("无法启动更新检查")
                self.check_update_btn.setEnabled(True)
                self.check_update_btn.setText("检查更新")
                InfoBar.error(
                    title="检查失败",
                    content="无法启动更新检查",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                return

            # 连接信号
            def on_update_available(app_update):
                log.info(f"发现新版本: {app_update.version}")
                # 恢复按钮状态
                self.check_update_btn.setEnabled(True)
                self.check_update_btn.setText("检查更新")

                # 显示更新对话框
                dialog = UpdateDialog(app_update, self)
                dialog.exec_()

            def on_no_update():
                log.info("当前已是最新版本")
                # 恢复按钮状态
                self.check_update_btn.setEnabled(True)
                self.check_update_btn.setText("检查更新")

                InfoBar.success(
                    title="已是最新版本",
                    content=f"当前版本 v{self._get_current_version()} 已是最新",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )

            def on_error(error_msg):
                log.error(f"检查更新出错: {error_msg}")
                # 恢复按钮状态
                self.check_update_btn.setEnabled(True)
                self.check_update_btn.setText("检查更新")

                InfoBar.error(
                    title="检查更新失败",
                    content=error_msg,
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )

            update_thread.update_available.connect(on_update_available)
            update_thread.no_update.connect(on_no_update)
            update_thread.error_occurred.connect(on_error)

            # 启动检查
            update_thread.start()

        except Exception as e:
            error_msg = f"检查更新功能异常: {str(e)}"
            log.error(error_msg)

            # 恢复按钮状态
            self.check_update_btn.setEnabled(True)
            self.check_update_btn.setText("检查更新")

            InfoBar.error(
                title="操作失败",
                content=error_msg,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000
            )