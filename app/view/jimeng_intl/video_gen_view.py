# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem,
                             QHeaderView, QLabel, QApplication, QFileDialog,
                             QTableWidget, QAbstractItemView, QStackedWidget,
                             QScrollArea, QGridLayout)
from datetime import datetime
from qfluentwidgets import (PrimaryPushButton, PushButton, TableWidget, ComboBox,
                           FluentIcon as FIF, InfoBar, InfoBarPosition, Dialog,
                           TextEdit, BodyLabel, CheckBox, Action, RoundMenu,
                           MessageBox, LineEdit, Pivot, ProgressBar)
from app.models.jimeng_intl_video_task import JimengIntlVideoTask
from app.view.jimeng.add_image_task_dialog import MultiImageDropWidget
from app.utils.logger import log
import os


class AddVideoTaskIntlDialog(Dialog):
    """添加视频任务对话框"""
    def __init__(self, parent=None):
        super().__init__("", "", parent)
        self.setFixedWidth(750)
        self.titleLabel.setVisible(False)
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 5, 30, 10)
        layout.setSpacing(15)

        # 第一行：模型选择
        model_layout = QHBoxLayout()
        model_label = BodyLabel("视频模型 *", content)
        model_layout.addWidget(model_label)
        self.model_combo = ComboBox(content)
        self.model_combo.addItems([
            'jimeng-video-veo3.1',
            'jimeng-video-sora2',
            'jimeng-video-3.0'
        ])
        self.model_combo.setCurrentText('jimeng-video-3.0')
        self.model_combo.setFixedWidth(200)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        layout.addLayout(model_layout)

        # 提示词
        prompt_label = BodyLabel("提示词 *", content)
        layout.addWidget(prompt_label)
        self.prompt_edit = TextEdit(content)
        self.prompt_edit.setPlaceholderText("请输入视频生成的提示词描述...")
        self.prompt_edit.setFixedHeight(80)
        layout.addWidget(self.prompt_edit)

        # 首帧图片
        image_label = BodyLabel("首帧图片（可选）", content)
        self.image_widget = MultiImageDropWidget(content, max_images=1)
        layout.addWidget(image_label)
        layout.addWidget(self.image_widget)

        # 第二行：视频比例、时长、质量
        settings_layout = QHBoxLayout()

        ratio_label = BodyLabel("视频比例 *", content)
        settings_layout.addWidget(ratio_label)
        self.ratio_combo = ComboBox(content)
        self.ratio_combo.addItems(['16:9', '9:16', '1:1', '4:3', '3:4'])
        self.ratio_combo.setCurrentText('16:9')
        self.ratio_combo.setFixedWidth(100)
        settings_layout.addWidget(self.ratio_combo)

        settings_layout.addSpacing(20)
        duration_label = BodyLabel("时长 *", content)
        settings_layout.addWidget(duration_label)
        self.duration_combo = ComboBox(content)
        self.duration_combo.addItems(['5s', '8s'])
        self.duration_combo.setCurrentText('5s')
        self.duration_combo.setFixedWidth(80)
        settings_layout.addWidget(self.duration_combo)

        settings_layout.addSpacing(20)
        quality_label = BodyLabel("质量 *", content)
        settings_layout.addWidget(quality_label)
        self.quality_combo = ComboBox(content)
        self.quality_combo.addItems(['720p', '1080p'])
        self.quality_combo.setCurrentText('1080p')
        self.quality_combo.setFixedWidth(100)
        settings_layout.addWidget(self.quality_combo)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        self.textLayout.addWidget(content)
        self.yesButton.setText("添加")
        self.cancelButton.setText("取消")
        self.yesButton.clicked.connect(self.on_add_task)
        self.cancelButton.clicked.connect(self.reject)
        self.image_widget.images_changed.connect(self.onImagesChanged)

    def on_add_task(self):
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            InfoBar.warning(title="提示", content="请输入提示词", parent=self, position=InfoBarPosition.TOP)
            return

        image_paths = self.image_widget.get_image_paths()

        try:
            JimengIntlVideoTask.create_task(
                prompt=prompt,
                account_id=None,
                ratio=self.ratio_combo.currentText(),
                model=self.model_combo.currentText(),
                duration=self.duration_combo.currentText(),
                quality=self.quality_combo.currentText(),
                input_images=image_paths
            )
            InfoBar.success(title="添加成功", content="视频任务已添加", parent=self, duration=2000, position=InfoBarPosition.TOP)
            self.accept()
        except Exception as e:
            log.error(f"添加视频任务失败: {e}")
            InfoBar.error(title="添加失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onImagesChanged(self, paths):
        self.resize(self.width(), self.sizeHint().height())


class VideoGenIntlView(QWidget):
    """即梦国际版视频生成界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoGenIntl")
        self.current_page = 1
        self.page_size = 20

        # 用于智能刷新的数据缓存：{task_id: task_state}
        # task_state 包含会影响UI的字段：status, code, message
        self.task_cache = {}

        # 添加自动刷新计时器
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.onAutoRefresh)
        self.auto_refresh_timer.start(5000)  # 5秒刷新一次

        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(20)

        # 顶部操作栏
        top = QHBoxLayout()
        self.selectAllCheckBox = CheckBox("全选", self)
        self.selectAllCheckBox.stateChanged.connect(self.onSelectAllChanged)
        top.addWidget(self.selectAllCheckBox)
        top.addStretch()

        self.addTaskBtn = PrimaryPushButton(FIF.ADD, "添加任务", self)
        self.addTaskBtn.clicked.connect(self.onAddTask)
        top.addWidget(self.addTaskBtn)

        self.batchAddBtn = PushButton(FIF.VIDEO, "批量添加", self)
        self.batchAddBtn.clicked.connect(self.onBatchAdd)
        top.addWidget(self.batchAddBtn)

        self.refreshBtn = PushButton(FIF.SYNC, "刷新", self)
        self.refreshBtn.clicked.connect(self.onRefresh)
        top.addWidget(self.refreshBtn)

        self.downloadBtn = PushButton(FIF.DOWNLOAD, "下载", self)
        self.downloadBtn.clicked.connect(self.onDownload)
        top.addWidget(self.downloadBtn)

        layout.addLayout(top)

        # 任务表格
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["", "ID", "首帧图", "提示词", "参数", "状态", "操作"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(100)
        self.table.setSelectionBehavior(TableWidget.SelectRows)
        self.table.setSelectionMode(TableWidget.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)
        layout.addWidget(self.table)

        # 底部分页栏
        bottom = QHBoxLayout()
        sizeLabel = BodyLabel("每页显示:", self)
        bottom.addWidget(sizeLabel)
        self.pageSizeCombo = ComboBox(self)
        self.pageSizeCombo.addItems(['10', '20', '50', '100'])
        self.pageSizeCombo.setCurrentText('20')
        self.pageSizeCombo.currentTextChanged.connect(self.onPageSizeChanged)
        self.pageSizeCombo.setFixedWidth(100)
        bottom.addWidget(self.pageSizeCombo)
        bottom.addStretch()
        self.pageInfoLabel = BodyLabel("第 1 页，共 0 条", self)
        bottom.addWidget(self.pageInfoLabel)
        bottom.addSpacing(20)
        self.prevPageBtn = PushButton(FIF.CARE_LEFT_SOLID, "上一页", self)
        self.prevPageBtn.clicked.connect(self.onPrevPage)
        bottom.addWidget(self.prevPageBtn)
        self.nextPageBtn = PushButton(FIF.CARE_RIGHT_SOLID, "下一页", self)
        self.nextPageBtn.clicked.connect(self.onNextPage)
        bottom.addWidget(self.nextPageBtn)
        layout.addLayout(bottom)

        # 初始列宽
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 220)

        self.loadTasks()

    def loadTasks(self):
        """加载任务列表"""
        try:
            tasks, total_count = JimengIntlVideoTask.get_tasks_by_page(self.current_page, self.page_size)

            # 清理旧内容
            old_row_count = self.table.rowCount()
            for r in range(old_row_count):
                for c in range(self.table.columnCount()):
                    w = self.table.cellWidget(r, c)
                    if w:
                        self.table.removeCellWidget(r, c)
                        w.setParent(None)
                        w.deleteLater()
            self.table.clearContents()
            self.table.setRowCount(0)
            QApplication.processEvents()

            self.table.setRowCount(len(tasks))
            for row, task in enumerate(tasks):
                self.table.setRowHeight(row, 100)

                # 复选框
                checkbox = CheckBox()
                container = QWidget(self.table)
                container.setFixedHeight(self.table.rowHeight(row))
                c_layout = QHBoxLayout(container)
                c_layout.setContentsMargins(0, 0, 0, 0)
                c_layout.setSpacing(0)
                c_layout.setAlignment(Qt.AlignCenter)
                c_layout.addWidget(checkbox, 0, Qt.AlignCenter)
                self.table.setCellWidget(row, 0, container)

                # ID
                id_item = QTableWidgetItem(str(task.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, id_item)

                # 首帧图
                first_img = None
                inputs = task.get_input_images()
                if inputs:
                    first_img = inputs[0]
                p = first_img or ""
                p = p.strip()
                if p.lower().startswith("file:///"):
                    p = p[8:].replace('/', '\\')
                if p and os.path.exists(p):
                    img_label = QLabel()
                    pixmap = QPixmap(p)
                    scaled = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_label.setPixmap(scaled)
                    img_label.setAlignment(Qt.AlignCenter)
                    img_label.setFixedSize(96, 96)
                    self.table.setCellWidget(row, 2, img_label)
                else:
                    item_img = QTableWidgetItem("无图片")
                    item_img.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 2, item_img)

                # 提示词
                pt = task.prompt or ""
                short = pt[:40] + ("..." if len(pt) > 40 else "")
                item_prompt = QTableWidgetItem(short)
                item_prompt.setToolTip(pt)
                item_prompt.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, item_prompt)

                # 参数信息
                params = f"{task.ratio} | {task.duration} | {task.quality}"
                item_params = QTableWidgetItem(params)
                item_params.setTextAlignment(Qt.AlignCenter)
                item_params.setToolTip(f"比例: {task.ratio}\n时长: {task.duration}\n质量: {task.quality}")
                self.table.setItem(row, 4, item_params)

                # 状态
                status_map = {0: "排队中", 1: "生成中", 2: "已完成", 3: "失败"}
                item_status = QTableWidgetItem(status_map.get(task.status, "-"))
                item_status.setData(Qt.UserRole, task.id)
                item_status.setTextAlignment(Qt.AlignCenter)

                # 如果失败，显示失败原因
                if task.status == 3 and task.message:
                    item_status.setToolTip(f"失败原因: {task.message}")

                if task.status == 2:
                    item_status.setForeground(QColor("#34C759"))
                elif task.status == 3:
                    item_status.setForeground(QColor("#FF3B30"))

                self.table.setItem(row, 5, item_status)

                # 操作按钮
                action_container = QWidget(self.table)
                action_container.setFixedHeight(self.table.rowHeight(row))
                action_layout = QHBoxLayout(action_container)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setSpacing(5)
                action_layout.setAlignment(Qt.AlignCenter)

                download_btn = PushButton("下载", action_container)
                download_btn.setFixedWidth(60)
                # 只有成功状态(2)才能下载
                download_btn.setEnabled(task.status == 2)
                download_btn.clicked.connect(lambda checked, tid=task.id: self.onDownloadTask(tid))
                action_layout.addWidget(download_btn)

                retry_btn = PushButton("重试", action_container)
                retry_btn.setFixedWidth(60)
                # 只有失败状态(3)才能重试
                retry_btn.setEnabled(task.status == 3)
                retry_btn.clicked.connect(lambda checked, tid=task.id: self.onRetryTask(tid))
                action_layout.addWidget(retry_btn)

                reason_btn = PushButton("原因", action_container)
                reason_btn.setFixedWidth(60)
                # 只有失败状态(3)才能查看原因
                reason_btn.setEnabled(task.status == 3)
                reason_btn.clicked.connect(lambda checked, tid=task.id: self.onShowFailReason(tid))
                action_layout.addWidget(reason_btn)

                self.table.setCellWidget(row, 6, action_container)

                # 初始化缓存
                self.task_cache[task.id] = {
                    'status': task.status,
                    'code': task.code,
                    'message': task.message
                }

            # 更新分页信息
            total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
            self.pageInfoLabel.setText(f"第 {self.current_page} 页，共 {total_count} 条")
            self.prevPageBtn.setEnabled(self.current_page > 1)
            self.nextPageBtn.setEnabled(self.current_page < total_pages)

        except Exception as e:
            log.error(f"加载视频任务失败: {e}")
            self.table.setRowCount(0)
            InfoBar.error(title="加载失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onAddTask(self):
        """添加任务"""
        dlg = AddVideoTaskIntlDialog(self)
        dlg.exec()
        self.loadTasks()

    def onRefresh(self):
        """刷新任务列表"""
        self.loadTasks()
        InfoBar.success(title="刷新成功", content="任务列表已更新", parent=self, duration=2000, position=InfoBarPosition.TOP)

    def onAutoRefresh(self):
        """自动刷新任务列表（5秒一次，仅更新变化的任务）"""
        try:
            self.smartRefreshTasks()
        except Exception as e:
            log.debug(f"自动刷新任务列表失败: {e}")

    def smartRefreshTasks(self):
        """智能刷新：只更新有变化的任务行"""
        try:
            tasks, total_count = JimengIntlVideoTask.get_tasks_by_page(self.current_page, self.page_size)

            # 遍历当前显示的任务，检查是否有变化
            for row, task in enumerate(tasks):
                # 构建当前任务的状态快照
                current_state = {
                    'status': task.status,
                    'code': task.code,
                    'message': task.message
                }

                # 检查这个任务是否在缓存中且状态是否改变
                task_id = task.id
                if task_id in self.task_cache:
                    cached_state = self.task_cache[task_id]
                    # 如果状态没有变化，跳过这一行
                    if cached_state == current_state:
                        continue

                # 状态有变化，更新缓存并刷新这一行
                self.task_cache[task_id] = current_state
                self.updateTaskRow(row, task)

        except Exception as e:
            log.debug(f"智能刷新失败: {e}")

    def updateTaskRow(self, row: int, task):
        """更新表格中的单一任务行"""
        try:
            # 更新状态列
            status_map = {0: "排队中", 1: "生成中", 2: "已完成", 3: "失败"}
            item_status = self.table.item(row, 5)
            if item_status:
                item_status.setText(status_map.get(task.status, "-"))
                item_status.setData(Qt.UserRole, task.id)
                item_status.setTextAlignment(Qt.AlignCenter)

                # 根据状态设置文字颜色
                if task.status == 2:  # 已完成
                    item_status.setForeground(QColor("#34C759"))  # 绿色
                elif task.status == 3:  # 失败
                    item_status.setForeground(QColor("#FF3B30"))  # 红色
                    # 如果失败，显示失败原因
                    if task.message:
                        item_status.setToolTip(f"失败原因: {task.message}")
                else:
                    item_status.setToolTip("")

            # 更新操作按钮的启用状态
            action_container = self.table.cellWidget(row, 6)
            if action_container:
                buttons = action_container.findChildren(PushButton)
                for btn in buttons:
                    if btn.text() == "下载":
                        btn.setEnabled(task.status == 2)
                    elif btn.text() == "重试":
                        btn.setEnabled(task.status == 3)
                    elif btn.text() == "原因":
                        btn.setEnabled(task.status == 3)

        except Exception as e:
            log.debug(f"更新任务行失败: {e}")

    def onDownloadTask(self, task_id: int):
        """下载单个任务的视频"""
        try:
            task = JimengIntlVideoTask.get_task_by_id(task_id)
            if not task:
                InfoBar.error(title="错误", content="任务不存在", parent=self, position=InfoBarPosition.TOP)
                return

            outputs = task.get_output_videos()
            if not outputs:
                InfoBar.warning(title="提示", content="该任务还未生成视频", parent=self, position=InfoBarPosition.TOP)
                return

            # 选择保存目录
            save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
            if not save_dir:
                return

            from PyQt5.QtCore import QObject
            import shutil
            import requests

            date_str = datetime.now().strftime("%Y%m%d%H%M%S")
            download_folder = os.path.join(save_dir, f"即梦_视频_{date_str}")

            # 创建下载进度对话框
            loading_dlg = Dialog("", "", self)
            loading_dlg.setFixedWidth(400)
            loading_dlg.setFixedHeight(150)
            loading_dlg.yesButton.setVisible(False)
            loading_dlg.cancelButton.setVisible(False)
            loading_dlg.titleLabel.setVisible(False)

            main_widget = QWidget(loading_dlg)
            dlg_layout = QVBoxLayout(main_widget)
            dlg_layout.setContentsMargins(24, 20, 24, 20)
            dlg_layout.setSpacing(12)

            title_label = BodyLabel("正在下载视频", main_widget)
            title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
            dlg_layout.addWidget(title_label)

            status_label = BodyLabel("初始化中...", main_widget)
            status_label.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.65);")
            dlg_layout.addWidget(status_label)

            progress_container = QWidget(main_widget)
            progress_layout = QHBoxLayout(progress_container)
            progress_layout.setContentsMargins(0, 0, 0, 0)
            progress_layout.setSpacing(10)

            progress_bar = ProgressBar(progress_container)
            progress_bar.setRange(0, len(outputs))
            progress_bar.setFixedHeight(5)
            progress_layout.addWidget(progress_bar, 1)

            progress_text = BodyLabel("0%", progress_container)
            progress_text.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.6); min-width: 30px;")
            progress_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            progress_layout.addWidget(progress_text)

            dlg_layout.addWidget(progress_container)
            loading_dlg.textLayout.addWidget(main_widget)

            class DownloadSignal(QObject):
                progress = pyqtSignal(int, int)
                finished = pyqtSignal(bool, str)

            signal_emitter = DownloadSignal()

            def on_progress_update(current, total):
                status_label.setText(f"已下载 {current}/{total} 个视频")
                progress_bar.setValue(current)
                percentage = int((current / total * 100)) if total > 0 else 0
                progress_text.setText(f"{percentage}%")

            def on_download_finished(success, message):
                loading_dlg.close()
                if success:
                    InfoBar.success(title="下载完成", content=message, parent=self, duration=3000, position=InfoBarPosition.TOP)
                else:
                    InfoBar.error(title="下载失败", content=message, parent=self, position=InfoBarPosition.TOP)

            def download_task_videos():
                success_count = 0
                fail_count = 0

                try:
                    os.makedirs(download_folder, exist_ok=True)

                    for idx, video_url in enumerate(outputs):
                        try:
                            signal_emitter.progress.emit(idx, len(outputs))

                            if video_url.startswith("http://") or video_url.startswith("https://"):
                                response = requests.get(video_url, timeout=120)
                                response.raise_for_status()

                                fname = os.path.basename(video_url.split('?')[0])
                                if not fname.endswith(('.mp4', '.webm', '.mov')):
                                    fname = f"video_{idx + 1}.mp4"

                                filepath = os.path.join(download_folder, fname)
                                with open(filepath, 'wb') as f:
                                    f.write(response.content)
                                success_count += 1
                            else:
                                if video_url.lower().startswith("file:///"):
                                    p = video_url[8:].replace('/', '\\')
                                else:
                                    p = video_url

                                if os.path.exists(p):
                                    fname = os.path.basename(p)
                                    shutil.copy2(p, os.path.join(download_folder, fname))
                                    success_count += 1
                                else:
                                    fail_count += 1

                        except Exception as e:
                            log.error(f"下载视频 {idx + 1} 失败: {e}")
                            fail_count += 1

                    signal_emitter.progress.emit(len(outputs), len(outputs))

                    if success_count > 0:
                        msg = f"成功下载 {success_count} 个视频"
                        if fail_count > 0:
                            msg += f"，{fail_count} 个失败"
                        signal_emitter.finished.emit(True, msg)
                    else:
                        signal_emitter.finished.emit(False, "未找到任何视频文件")

                except Exception as e:
                    log.error(f"下载任务 {task_id} 失败: {e}")
                    signal_emitter.finished.emit(False, str(e))

            signal_emitter.progress.connect(on_progress_update)
            signal_emitter.finished.connect(on_download_finished)

            download_thread = QThread()
            download_thread.run = download_task_videos
            download_thread.start()

            loading_dlg.exec()

        except Exception as e:
            log.error(f"下载视频失败: {e}")
            InfoBar.error(title="下载失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onRetryTask(self, task_id: int):
        """重试任务"""
        try:
            task = JimengIntlVideoTask.get_task_by_id(task_id)
            if not task:
                InfoBar.error(title="错误", content="任务不存在", parent=self, position=InfoBarPosition.TOP)
                return

            task.status = 0
            task.code = None
            task.message = None
            task.update_at = datetime.now()
            task.save()

            log.info(f"视频任务 {task_id} 已重置为排队状态")
            self.loadTasks()
            InfoBar.success(title="重试成功", content="任务已重新加入队列", parent=self, duration=2000, position=InfoBarPosition.TOP)

        except Exception as e:
            log.error(f"重试任务失败: {e}")
            InfoBar.error(title="重试失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onShowFailReason(self, task_id: int):
        """显示失败原因"""
        try:
            task = JimengIntlVideoTask.get_task_by_id(task_id)
            if not task:
                InfoBar.error(title="错误", content="任务不存在", parent=self, position=InfoBarPosition.TOP)
                return

            reason = task.message or "暂无失败原因记录"
            code = task.code or ""

            content = reason
            if code:
                content = f"错误码: {code}\n\n{reason}"

            msg_box = MessageBox("失败原因", content, self)
            msg_box.cancelButton.setVisible(False)
            msg_box.yesButton.setText("确定")
            msg_box.exec()

        except Exception as e:
            log.error(f"获取失败原因失败: {e}")
            InfoBar.error(title="错误", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onPageSizeChanged(self, size):
        self.page_size = int(size)
        self.current_page = 1
        self.loadTasks()

    def onPrevPage(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.loadTasks()

    def onNextPage(self):
        self.current_page += 1
        self.loadTasks()

    def showEvent(self, event):
        """界面显示时启动自动刷新"""
        super().showEvent(event)
        if hasattr(self, 'auto_refresh_timer') and not self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.start(5000)

    def hideEvent(self, event):
        """界面隐藏时停止自动刷新"""
        super().hideEvent(event)
        if hasattr(self, 'auto_refresh_timer') and self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()

    def onSelectAllChanged(self, state):
        checked = (state == Qt.Checked)
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, 0)
            if container:
                cb = container.findChild(CheckBox)
                if cb:
                    cb.setChecked(checked)

    def _getSelectedTaskIds(self):
        ids = []
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, 0)
            if container:
                cb = container.findChild(CheckBox)
                if cb and cb.isChecked():
                    status_item = self.table.item(row, 5)
                    if status_item:
                        task_id = status_item.data(Qt.UserRole)
                        if task_id:
                            ids.append(int(task_id))
        return ids

    def onDownload(self):
        """批量下载"""
        selected_ids = self._getSelectedTaskIds()
        if not selected_ids:
            InfoBar.warning(title="提示", content="请先勾选要下载的任务", parent=self, position=InfoBarPosition.TOP)
            return

        download_dir = QFileDialog.getExistingDirectory(self, "选择下载目录", "", QFileDialog.ShowDirsOnly)
        if not download_dir:
            return

        from PyQt5.QtCore import QObject
        import shutil
        import requests

        date_str = datetime.now().strftime("%Y%m%d%H%M%S")
        download_folder = os.path.join(download_dir, f"即梦_视频_{date_str}")

        loading_dlg = Dialog("", "", self)
        loading_dlg.setFixedWidth(400)
        loading_dlg.setFixedHeight(150)
        loading_dlg.yesButton.setVisible(False)
        loading_dlg.cancelButton.setVisible(False)
        loading_dlg.titleLabel.setVisible(False)

        main_widget = QWidget(loading_dlg)
        dlg_layout = QVBoxLayout(main_widget)
        dlg_layout.setContentsMargins(24, 20, 24, 20)
        dlg_layout.setSpacing(12)

        title_label = BodyLabel("正在下载视频", main_widget)
        title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        dlg_layout.addWidget(title_label)

        status_label = BodyLabel("初始化中...", main_widget)
        status_label.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.65);")
        dlg_layout.addWidget(status_label)

        progress_container = QWidget(main_widget)
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(10)

        progress_bar = ProgressBar(progress_container)
        progress_bar.setRange(0, len(selected_ids))
        progress_bar.setFixedHeight(5)
        progress_layout.addWidget(progress_bar, 1)

        progress_text = BodyLabel("0%", progress_container)
        progress_text.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.6); min-width: 30px;")
        progress_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(progress_text)

        dlg_layout.addWidget(progress_container)
        loading_dlg.textLayout.addWidget(main_widget)

        class DownloadSignal(QObject):
            progress = pyqtSignal(int, int)
            finished = pyqtSignal(int, int)

        signal_emitter = DownloadSignal()

        def on_progress_update(current, total):
            status_label.setText(f"已处理 {current}/{total} 个任务")
            progress_bar.setValue(current)
            percentage = int((current / total * 100)) if total > 0 else 0
            progress_text.setText(f"{percentage}%")

        def on_download_finished(completed, failed):
            loading_dlg.close()
            if completed > 0:
                msg = f"成功下载 {completed} 个任务"
                if failed > 0:
                    msg += f"，{failed} 个失败"
                InfoBar.success(title="下载完成", content=msg, parent=self, duration=3000, position=InfoBarPosition.TOP)
            else:
                InfoBar.error(title="下载失败", content="所有任务下载失败", parent=self, position=InfoBarPosition.TOP)

        def download_all_tasks():
            completed = 0
            failed = 0

            for idx, task_id in enumerate(selected_ids):
                try:
                    task = JimengIntlVideoTask.get_task_by_id(task_id)
                    if not task:
                        failed += 1
                        signal_emitter.progress.emit(idx + 1, len(selected_ids))
                        continue

                    outputs = task.get_output_videos()
                    if not outputs:
                        failed += 1
                        signal_emitter.progress.emit(idx + 1, len(selected_ids))
                        continue

                    os.makedirs(download_folder, exist_ok=True)

                    for p in outputs:
                        try:
                            if p.startswith("http://") or p.startswith("https://"):
                                response = requests.get(p, timeout=120)
                                response.raise_for_status()

                                fname = os.path.basename(p.split('?')[0])
                                if not fname.endswith(('.mp4', '.webm', '.mov')):
                                    # 使用task_id和索引来命名文件，确保不重复
                                    existing_count = len([f for f in os.listdir(download_folder) if f.startswith(f"task_{task_id}_")])
                                    fname = f"task_{task_id}_video_{existing_count + 1}.mp4"

                                filepath = os.path.join(download_folder, fname)
                                with open(filepath, 'wb') as f:
                                    f.write(response.content)
                            else:
                                if p.lower().startswith("file:///"):
                                    p2 = p[8:].replace('/', '\\')
                                else:
                                    p2 = p

                                if os.path.exists(p2):
                                    fname = os.path.basename(p2)
                                    shutil.copy2(p2, os.path.join(download_folder, fname))

                        except Exception as e:
                            log.error(f"下载视频失败: {e}")

                    completed += 1

                except Exception as e:
                    failed += 1
                    log.error(f"下载任务 {task_id} 失败: {e}")

                signal_emitter.progress.emit(idx + 1, len(selected_ids))

            signal_emitter.finished.emit(completed, failed)

        signal_emitter.progress.connect(on_progress_update)
        signal_emitter.finished.connect(on_download_finished)

        download_thread = QThread()
        download_thread.run = download_all_tasks
        download_thread.start()

        loading_dlg.exec()

    def showContextMenu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        status_item = self.table.item(row, 5)
        if not status_item:
            return
        task_id = status_item.data(Qt.UserRole)
        menu = RoundMenu(parent=self)
        delete_action = Action(FIF.DELETE, "删除", self)
        delete_action.triggered.connect(lambda: self.onDeleteTask(int(task_id)))
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def onDeleteTask(self, task_id: int):
        msg_box = MessageBox("确认删除", f"确定要删除任务 #{task_id} 吗？", self)
        if msg_box.exec():
            ok = JimengIntlVideoTask.mark_deleted(task_id)
            if ok:
                InfoBar.success(title="删除成功", content=f"任务 #{task_id} 已删除", parent=self, duration=2000, position=InfoBarPosition.TOP)
                self.loadTasks()
            else:
                InfoBar.error(title="删除失败", content="任务不存在", parent=self, position=InfoBarPosition.TOP)

    def onBatchAdd(self):
        """批量添加"""
        dlg = BatchAddVideoTaskIntlDialog(self)

        def on_added(tasks_data):
            try:
                ok = 0
                for t in tasks_data:
                    try:
                        JimengIntlVideoTask.create_task(
                            prompt=t.get('prompt', ''),
                            account_id=None,
                            ratio=t.get('ratio', '16:9'),
                            model=t.get('model', 'pixverse-v4.5'),
                            duration=t.get('duration', '5s'),
                            quality=t.get('quality', '1080p'),
                            motion=t.get('motion', 'auto'),
                            negative_prompt=t.get('negative_prompt'),
                            input_images=t.get('input_images', [])
                        )
                        ok += 1
                    except Exception:
                        pass
                self.loadTasks()
                if ok > 0:
                    InfoBar.success(title="批量添加成功", content=f"成功添加 {ok} 个任务", parent=self, duration=2500, position=InfoBarPosition.TOP)
                else:
                    InfoBar.error(title="批量添加失败", content="所有任务添加失败", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error(title="批量添加失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

        dlg.tasks_added.connect(on_added)
        dlg.exec()


class BatchAddVideoTaskIntlDialog(Dialog):
    """批量添加视频任务对话框"""
    from PyQt5.QtCore import pyqtSignal
    tasks_added = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__("", "", parent)
        screen = QApplication.desktop().screenGeometry()
        w = min(1000, int(screen.width() * 0.9))
        h = min(825, int(screen.height() * 0.9))
        self.setFixedSize(w, h)
        self.titleLabel.setVisible(False)
        self._initUI()

    def _center(self):
        screen = QApplication.desktop().screenGeometry()
        g = self.frameGeometry()
        g.moveCenter(screen.center())
        self.move(g.topLeft())

    def showEvent(self, e):
        super().showEvent(e)
        self._center()

    def moveEvent(self, e):
        if getattr(self, "_lock_move", False):
            return
        self._lock_move = True
        self._center()
        self._lock_move = False

    def _initUI(self):
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.pivot = Pivot(content)
        self.pivot.setFixedHeight(28)
        self.stacked = QStackedWidget(content)

        self.text_widget = _TextPromptVideoImportIntlWidget(self.stacked)
        self.folder_widget = _FolderVideoImportIntlWidget(self.stacked)

        self.stacked.addWidget(self.text_widget)
        self.stacked.addWidget(self.folder_widget)

        self.pivot.addItem(routeKey='text', text='文本导入', onClick=lambda: self.stacked.setCurrentWidget(self.text_widget))
        self.pivot.addItem(routeKey='folder', text='文件夹导入', onClick=lambda: self.stacked.setCurrentWidget(self.folder_widget))

        self.pivot.setCurrentItem('text')
        self.stacked.setCurrentWidget(self.text_widget)

        layout.addWidget(self.pivot)
        layout.addWidget(self.stacked)

        self.textLayout.addWidget(content)
        try:
            self.textLayout.setContentsMargins(0, 0, 0, 0)
            self.textLayout.setSpacing(0)
            if hasattr(self, 'buttonLayout') and self.buttonLayout is not None:
                self.buttonLayout.setContentsMargins(6, 6, 6, 6)
                self.buttonLayout.setSpacing(6)
        except Exception:
            pass

        content.setStyleSheet(
            "QTableWidget{background-color:#1f1f1f;color:#e5e5e5;gridline-color:#2d2d2d;}"
            "QTableWidget::item:selected{background-color:#2a2a2a;color:#ffffff;}"
            "QTableWidget::item{padding:6px;}"
            "QHeaderView::section{background-color:#303030;color:#dcdcdc;border:0px;border-bottom:1px solid #3a3a3a;padding:8px 6px;}"
        )

        self.yesButton.setText("批量添加")
        self.cancelButton.setText("取消")
        self.yesButton.clicked.connect(self._on_batch_add)
        self.cancelButton.clicked.connect(self.reject)

    def _on_batch_add(self):
        w = self.stacked.currentWidget()
        data = w.get_tasks_data()
        if not data:
            InfoBar.warning(title="提示", content="没有可添加的任务", parent=self, position=InfoBarPosition.TOP)
            return
        self.tasks_added.emit(data)
        self.accept()


class _VideoModelSettingsMixin:
    """视频模型参数设置混入类"""
    def _init_video_settings(self, owner):
        ml = QHBoxLayout()

        ml.addWidget(BodyLabel("模型:", owner))
        self.model_combo = ComboBox(owner)
        self.model_combo.addItems([
            'jimeng-video-veo3.1',
            'jimeng-video-sora2',
            'jimeng-video-3.0'
        ])
        self.model_combo.setCurrentText('jimeng-video-3.0')
        self.model_combo.setFixedWidth(180)
        ml.addWidget(self.model_combo)

        ml.addSpacing(10)
        ml.addWidget(BodyLabel("比例:", owner))
        self.ratio_combo = ComboBox(owner)
        self.ratio_combo.addItems(['16:9', '9:16', '1:1', '4:3', '3:4'])
        self.ratio_combo.setCurrentText('16:9')
        self.ratio_combo.setFixedWidth(80)
        ml.addWidget(self.ratio_combo)

        ml.addSpacing(10)
        ml.addWidget(BodyLabel("时长:", owner))
        self.duration_combo = ComboBox(owner)
        self.duration_combo.addItems(['5s', '8s'])
        self.duration_combo.setCurrentText('5s')
        self.duration_combo.setFixedWidth(70)
        ml.addWidget(self.duration_combo)

        ml.addSpacing(10)
        ml.addWidget(BodyLabel("质量:", owner))
        self.quality_combo = ComboBox(owner)
        self.quality_combo.addItems(['720p', '1080p'])
        self.quality_combo.setCurrentText('1080p')
        self.quality_combo.setFixedWidth(80)
        ml.addWidget(self.quality_combo)

        ml.addSpacing(10)
        ml.addWidget(BodyLabel("运动:", owner))
        self.motion_combo = ComboBox(owner)
        self.motion_combo.addItems(['auto', 'small', 'medium', 'large'])
        self.motion_combo.setCurrentText('auto')
        self.motion_combo.setFixedWidth(80)
        ml.addWidget(self.motion_combo)

        ml.addStretch()
        return ml


class _TextPromptVideoImportIntlWidget(QWidget, _VideoModelSettingsMixin):
    """文本导入视频任务"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        layout.addLayout(self._init_video_settings(self))

        layout.addWidget(BodyLabel("提示词列表（每行一个）:", self))
        self.prompts_edit = TextEdit(self)
        layout.addWidget(self.prompts_edit)

        self.count_label = BodyLabel("当前任务数：0", self)
        layout.addWidget(self.count_label)
        self.prompts_edit.textChanged.connect(self._update_count)

    def _update_count(self):
        text = self.prompts_edit.toPlainText()
        lines = [i.strip() for i in text.split('\n') if i.strip()]
        self.count_label.setText(f"当前任务数：{len(lines)}")

    def get_tasks_data(self):
        text = self.prompts_edit.toPlainText()
        lines = [i.strip() for i in text.split('\n') if i.strip()]
        if not lines:
            return []
        return [{
            'prompt': p,
            'model': self.model_combo.currentText(),
            'ratio': self.ratio_combo.currentText(),
            'duration': self.duration_combo.currentText(),
            'quality': self.quality_combo.currentText(),
            'motion': self.motion_combo.currentText(),
            'input_images': []
        } for p in lines]


class _FolderVideoImportIntlWidget(QWidget, _VideoModelSettingsMixin):
    """文件夹导入视频任务（图片作为首帧）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_path = ""
        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        fl = QHBoxLayout()
        fl.addWidget(BodyLabel("选择文件夹:", self))
        self.folder_edit = LineEdit(self)
        self.folder_edit.setReadOnly(True)
        fl.addWidget(self.folder_edit)
        btn = PushButton(FIF.FOLDER, "浏览", self)
        btn.clicked.connect(self._on_select_folder)
        fl.addWidget(btn)
        layout.addLayout(fl)

        layout.addLayout(self._init_video_settings(self))

        layout.addWidget(BodyLabel("默认提示词（可选）:", self))
        self.prompt_edit = TextEdit(self)
        self.prompt_edit.setFixedHeight(60)
        layout.addWidget(self.prompt_edit)

        self.preview_label = BodyLabel("尚未选择文件夹", self)
        layout.addWidget(self.preview_label)
        layout.addStretch()

    def _on_select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹", "")
        if folder:
            self.folder_path = folder
            self.folder_edit.setText(folder)
            files = self._get_image_files()
            if files:
                self.preview_label.setText(f"找到 {len(files)} 张图片（将作为首帧）")
            else:
                self.preview_label.setText("文件夹中没有找到图片文件")

    def _get_image_files(self):
        if not self.folder_path or not os.path.exists(self.folder_path):
            return []
        exts = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
        ret = []
        for f in os.listdir(self.folder_path):
            if f.lower().endswith(exts):
                ret.append(os.path.join(self.folder_path, f))
        return ret

    def get_tasks_data(self):
        files = self._get_image_files()
        if not files:
            return []
        dft = self.prompt_edit.toPlainText().strip()
        tasks = []
        for p in files:
            tasks.append({
                'prompt': dft or os.path.splitext(os.path.basename(p))[0],
                'model': self.model_combo.currentText(),
                'ratio': self.ratio_combo.currentText(),
                'duration': self.duration_combo.currentText(),
                'quality': self.quality_combo.currentText(),
                'motion': self.motion_combo.currentText(),
                'input_images': [p]
            })
        return tasks
