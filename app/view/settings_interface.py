from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog
from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup, SettingCard,
                            SpinBox, BodyLabel, PrimaryPushButton, LineEdit,
                            InfoBar, InfoBarPosition, FluentIcon as FIF,
                            MessageBox, SwitchButton, ComboBox, setTheme, Theme)
from app.utils.logger import log
from app.utils.log_manager import get_log_manager
from app.utils.config_manager import get_config_manager
from app.managers.global_task_manager import get_global_task_manager, CONFIG_KEY_TASK_MANAGER_THREADS, DEFAULT_TASK_MANAGER_THREADS


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

    def initUI(self):
        """初始化UI"""
        self.scrollWidget.setObjectName('scrollWidget')

        # 设置布局
        self.expandLayout.setContentsMargins(40, 20, 40, 20)
        self.expandLayout.setSpacing(20)

        # 即梦API设置组
        self.jimeng_api_group = SettingCardGroup("即梦API地址", self.scrollWidget)

        # jimeng-api 输入框卡片
        self.jimeng_api_card = SettingCard(
            FIF.LINK,
            "Jimeng API",
            "即梦API服务地址",
            self.jimeng_api_group
        )

        # 添加输入框和保存按钮
        jimeng_api_container = QWidget(self.jimeng_api_card)
        jimeng_api_layout = QHBoxLayout(jimeng_api_container)
        jimeng_api_layout.setContentsMargins(0, 0, 0, 0)
        jimeng_api_layout.setSpacing(10)

        self.jimeng_api_input = LineEdit(jimeng_api_container)
        self.jimeng_api_input.setPlaceholderText("请输入即梦API地址")
        self.jimeng_api_input.setFixedWidth(300)
        # 从数据库加载已保存的值
        config_manager = get_config_manager()
        saved_api = config_manager.get("jimeng_api", "")
        if saved_api:
            self.jimeng_api_input.setText(saved_api)
        jimeng_api_layout.addWidget(self.jimeng_api_input)

        self.jimeng_api_save_btn = PrimaryPushButton(FIF.SAVE, "保存", jimeng_api_container)
        self.jimeng_api_save_btn.clicked.connect(self.onSaveJimengApi)
        jimeng_api_layout.addWidget(self.jimeng_api_save_btn)

        self.jimeng_api_card.hBoxLayout.addWidget(jimeng_api_container, 0, Qt.AlignRight)
        self.jimeng_api_card.hBoxLayout.addSpacing(16)

        # 添加到组
        self.jimeng_api_group.addSettingCard(self.jimeng_api_card)

        # 添加到布局
        self.expandLayout.addWidget(self.jimeng_api_group)

        # 外观设置组
        self.appearance_group = SettingCardGroup("外观设置", self.scrollWidget)

        # 主题设置卡片
        self.theme_card = SettingCard(
            FIF.BRUSH,
            "应用主题",
            "选择应用的主题模式",
            self.appearance_group
        )

        # 创建主题设置容器
        theme_container = QWidget(self.theme_card)
        theme_layout = QHBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(10)

        self.theme_combo = ComboBox(theme_container)
        self.theme_combo.addItems(["深色", "浅色", "跟随系统"])
        self.theme_combo.setFixedWidth(150)

        # 从配置加载保存的主题设置
        saved_theme = config_manager.get("app_theme", "dark")
        theme_index = {"dark": 0, "light": 1, "auto": 2}.get(saved_theme, 0)
        self.theme_combo.setCurrentIndex(theme_index)

        # 连接信号
        self.theme_combo.currentIndexChanged.connect(self.onThemeChanged)

        theme_layout.addWidget(self.theme_combo)

        self.theme_card.hBoxLayout.addWidget(theme_container, 0, Qt.AlignRight)
        self.theme_card.hBoxLayout.addSpacing(16)

        # 添加到组
        self.appearance_group.addSettingCard(self.theme_card)

        # 添加到布局
        self.expandLayout.addWidget(self.appearance_group)

        # 任务管理器设置组
        self.task_manager_group = SettingCardGroup("任务管理器", self.scrollWidget)

        # 任务管理器线程数设置卡片
        self.task_threads_card = SettingCard(
            FIF.PEOPLE,
            "任务线程数",
            "任务管理器的最大并发线程数（1-200）",
            self.task_manager_group
        )

        # 创建任务线程数设置容器
        task_threads_container = QWidget(self.task_threads_card)
        task_threads_layout = QHBoxLayout(task_threads_container)
        task_threads_layout.setContentsMargins(0, 0, 0, 0)
        task_threads_layout.setSpacing(10)

        self.task_threads_spin = SpinBox(task_threads_container)
        self.task_threads_spin.setRange(1, 200)
        saved_task_threads = config_manager.get_int(CONFIG_KEY_TASK_MANAGER_THREADS, DEFAULT_TASK_MANAGER_THREADS)
        self.task_threads_spin.setValue(saved_task_threads)
        self.task_threads_spin.setFixedWidth(120)
        task_threads_layout.addWidget(self.task_threads_spin)

        self.task_threads_save_btn = PrimaryPushButton(FIF.SAVE, "保存", task_threads_container)
        self.task_threads_save_btn.clicked.connect(self.onSaveTaskThreads)
        task_threads_layout.addWidget(self.task_threads_save_btn)

        self.task_threads_card.hBoxLayout.addWidget(task_threads_container, 0, Qt.AlignRight)
        self.task_threads_card.hBoxLayout.addSpacing(16)

        # 添加到组
        self.task_manager_group.addSettingCard(self.task_threads_card)

        # 添加到布局
        self.expandLayout.addWidget(self.task_manager_group)

        # 即梦国际版超时设置组
        self.jimeng_intl_timeout_group = SettingCardGroup("即梦国际版超时设置", self.scrollWidget)

        # 图片生成超时设置卡片
        self.image_timeout_card = SettingCard(
            FIF.PHOTO,
            "图片生成超时",
            "图片生成请求的超时时间（60-7200秒，默认300秒）",
            self.jimeng_intl_timeout_group
        )

        # 创建图片超时设置容器
        image_timeout_container = QWidget(self.image_timeout_card)
        image_timeout_layout = QHBoxLayout(image_timeout_container)
        image_timeout_layout.setContentsMargins(0, 0, 0, 0)
        image_timeout_layout.setSpacing(10)

        self.image_timeout_spin = SpinBox(image_timeout_container)
        self.image_timeout_spin.setRange(60, 7200)
        saved_image_timeout = config_manager.get_int("jimeng_intl_image_timeout", 300)
        self.image_timeout_spin.setValue(saved_image_timeout)
        self.image_timeout_spin.setFixedWidth(120)
        image_timeout_layout.addWidget(self.image_timeout_spin)

        self.image_timeout_unit_label = BodyLabel("秒", image_timeout_container)
        image_timeout_layout.addWidget(self.image_timeout_unit_label)

        self.image_timeout_save_btn = PrimaryPushButton(FIF.SAVE, "保存", image_timeout_container)
        self.image_timeout_save_btn.clicked.connect(self.onSaveImageTimeout)
        image_timeout_layout.addWidget(self.image_timeout_save_btn)

        self.image_timeout_card.hBoxLayout.addWidget(image_timeout_container, 0, Qt.AlignRight)
        self.image_timeout_card.hBoxLayout.addSpacing(16)

        # 视频生成超时设置卡片
        self.video_timeout_card = SettingCard(
            FIF.VIDEO,
            "视频生成超时",
            "视频生成请求的超时时间（60-7200秒，默认600秒）",
            self.jimeng_intl_timeout_group
        )

        # 创建视频超时设置容器
        video_timeout_container = QWidget(self.video_timeout_card)
        video_timeout_layout = QHBoxLayout(video_timeout_container)
        video_timeout_layout.setContentsMargins(0, 0, 0, 0)
        video_timeout_layout.setSpacing(10)

        self.video_timeout_spin = SpinBox(video_timeout_container)
        self.video_timeout_spin.setRange(60, 7200)
        saved_video_timeout = config_manager.get_int("jimeng_intl_video_timeout", 600)
        self.video_timeout_spin.setValue(saved_video_timeout)
        self.video_timeout_spin.setFixedWidth(120)
        video_timeout_layout.addWidget(self.video_timeout_spin)

        self.video_timeout_unit_label = BodyLabel("秒", video_timeout_container)
        video_timeout_layout.addWidget(self.video_timeout_unit_label)

        self.video_timeout_save_btn = PrimaryPushButton(FIF.SAVE, "保存", video_timeout_container)
        self.video_timeout_save_btn.clicked.connect(self.onSaveVideoTimeout)
        video_timeout_layout.addWidget(self.video_timeout_save_btn)

        self.video_timeout_card.hBoxLayout.addWidget(video_timeout_container, 0, Qt.AlignRight)
        self.video_timeout_card.hBoxLayout.addSpacing(16)

        # 添加到组
        self.jimeng_intl_timeout_group.addSettingCard(self.image_timeout_card)
        self.jimeng_intl_timeout_group.addSettingCard(self.video_timeout_card)

        # 添加到布局
        self.expandLayout.addWidget(self.jimeng_intl_timeout_group)

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

    def onSaveJimengApi(self):
        """保存即梦API地址"""
        api_url = self.jimeng_api_input.text().strip()
        config_manager = get_config_manager()

        if config_manager.set("jimeng_api", api_url):
            log.info(f"即梦API地址已保存: {api_url}")
            InfoBar.success(
                title="保存成功",
                content="即梦API地址已保存",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        else:
            InfoBar.error(
                title="保存失败",
                content="无法保存即梦API地址",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def onThemeChanged(self, index):
        """主题切换处理"""
        config_manager = get_config_manager()
        theme_map = {0: "dark", 1: "light", 2: "auto"}
        theme_value = theme_map.get(index, "dark")

        # 保存配置
        config_manager.set("app_theme", theme_value)

        # 应用主题
        if theme_value == "dark":
            setTheme(Theme.DARK)
        elif theme_value == "light":
            setTheme(Theme.LIGHT)
        else:  # auto - 跟随系统
            setTheme(Theme.AUTO)

        theme_names = {0: "深色", 1: "浅色", 2: "跟随系统"}
        log.info(f"应用主题已切换为: {theme_names.get(index, '未知')}")

        InfoBar.success(
            title="主题已切换",
            content=f"应用主题已设置为「{theme_names.get(index, '未知')}」",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )

    def onSaveTaskThreads(self):
        """保存任务管理器线程数设置"""
        threads = self.task_threads_spin.value()

        log.info(f"保存任务管理器线程数: {threads}")

        task_manager = get_global_task_manager()
        task_manager.set_max_workers(threads)

        InfoBar.success(
            title="保存成功",
            content=f"任务管理器线程数已设置为 {threads}",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )

    def onSaveImageTimeout(self):
        """保存图片生成超时设置"""
        timeout = self.image_timeout_spin.value()
        config_manager = get_config_manager()

        if config_manager.set("jimeng_intl_image_timeout", timeout):
            log.info(f"图片生成超时已设置为: {timeout}秒")
            InfoBar.success(
                title="保存成功",
                content=f"图片生成超时已设置为 {timeout} 秒",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        else:
            InfoBar.error(
                title="保存失败",
                content="无法保存图片生成超时设置",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def onSaveVideoTimeout(self):
        """保存视频生成超时设置"""
        timeout = self.video_timeout_spin.value()
        config_manager = get_config_manager()

        if config_manager.set("jimeng_intl_video_timeout", timeout):
            log.info(f"视频生成超时已设置为: {timeout}秒")
            InfoBar.success(
                title="保存成功",
                content=f"视频生成超时已设置为 {timeout} 秒",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        else:
            InfoBar.error(
                title="保存失败",
                content="无法保存视频生成超时设置",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
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

            # 使用 GitHub 仓库信息
            manager = get_update_manager(
                repo_owner="shukeCyp",
                repo_name="VideoRobot"
            )

            update_checker = manager.check_for_updates()

            if not update_checker:
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
            def on_update_available(update_info):
                log.info(f"发现新版本: {update_info.get('version')}")
                # 恢复按钮状态
                self.check_update_btn.setEnabled(True)
                self.check_update_btn.setText("检查更新")

                # 显示更新对话框
                dialog = UpdateDialog(update_info, self)
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

            update_checker.update_available.connect(on_update_available)
            update_checker.no_update.connect(on_no_update)
            update_checker.error_occurred.connect(on_error)

            # 启动检查
            update_checker.start()

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