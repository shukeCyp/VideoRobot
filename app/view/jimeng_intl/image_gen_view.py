# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView, QLabel, QApplication, QFileDialog, QTableWidget, QAbstractItemView, QStackedWidget, QScrollArea, QGridLayout
from datetime import datetime
from qfluentwidgets import PrimaryPushButton, PushButton, TableWidget, ComboBox, FluentIcon as FIF, InfoBar, InfoBarPosition, Dialog, TextEdit, BodyLabel, CheckBox, Action, RoundMenu, MessageBox, LineEdit, Pivot, ProgressBar
from app.models.jimeng_intl_image_task import JimengIntlImageTask
from app.view.jimeng.add_image_task_dialog import MultiImageDropWidget
from app.utils.logger import log
import os
import requests
import re
from app.constants import JIMENG_INTL_IMAGE_MODE_MAP


class AddImageTaskIntlDialog(Dialog):
    def __init__(self, parent=None):
        super().__init__("", "", parent)
        self.setFixedWidth(700)
        self.titleLabel.setVisible(False)
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 5, 30, 10)
        layout.setSpacing(15)

        # 模型选择（单独一行，在最上面）
        model_layout = QHBoxLayout()
        model_label = BodyLabel("图片模型 *", content)
        model_layout.addWidget(model_label)
        self.model_combo = ComboBox(content)
        self.model_combo.addItems(['nanobananapro', 'nanobanana', 'jimeng-4.5', 'jimeng-4.1', 'jimeng-4.0', 'jimeng-3.0'])
        self.model_combo.setCurrentText('jimeng-4.5')
        self.model_combo.setFixedWidth(180)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        layout.addLayout(model_layout)

        # 提示词
        prompt_label = BodyLabel("提示词 *", content)
        layout.addWidget(prompt_label)
        self.prompt_edit = TextEdit(content)
        self.prompt_edit.setPlaceholderText("请输入图片生成的提示词描述...")
        self.prompt_edit.setFixedHeight(80)
        layout.addWidget(self.prompt_edit)

        # 参考图片
        image_label = BodyLabel("参考图片（可选）", content)
        self.image_widget = MultiImageDropWidget(content)
        layout.addWidget(image_label)
        layout.addWidget(self.image_widget)

        # 分辨率比例和清晰度（同一行，在下面）
        settings_layout = QHBoxLayout()
        ratio_label = BodyLabel("分辨率比例 *", content)
        settings_layout.addWidget(ratio_label)
        self.ratio_combo = ComboBox(content)
        self.ratio_combo.addItems(['1:1', '4:3', '3:4', '16:9', '9:16', '3:2', '2:3', '21:9'])
        self.ratio_combo.setCurrentText('1:1')
        self.ratio_combo.setFixedWidth(120)
        settings_layout.addWidget(self.ratio_combo)

        settings_layout.addSpacing(30)
        quality_label = BodyLabel("清晰度 *", content)
        settings_layout.addWidget(quality_label)
        self.resolution_combo = ComboBox(content)
        self.resolution_combo.addItems(['1k', '2k', '4k'])
        self.resolution_combo.setCurrentText('2k')
        self.resolution_combo.setFixedWidth(120)
        settings_layout.addWidget(self.resolution_combo)

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
            ratio_val = self.ratio_combo.currentText()
            model_val = self.model_combo.currentText()
            resolution_val = self.resolution_combo.currentText()
            JimengIntlImageTask.create_task(
                prompt=prompt,
                account_id=None,
                ratio=ratio_val,
                model=model_val,
                resolution=resolution_val,
                input_images=image_paths
            )
            InfoBar.success(title="添加成功", content="任务已添加", parent=self, duration=2000, position=InfoBarPosition.TOP)
            self.accept()
        except Exception as e:
            log.error(f"添加国际版任务失败: {e}")
            InfoBar.error(title="添加失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onImagesChanged(self, paths):
        self.resize(self.width(), self.sizeHint().height())


class ImageGenIntlView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("imageGenIntl")
        self.current_page = 1
        self.page_size = 20
        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(20)
        top = QHBoxLayout()
        self.selectAllCheckBox = CheckBox("全选", self)
        self.selectAllCheckBox.stateChanged.connect(self.onSelectAllChanged)
        top.addWidget(self.selectAllCheckBox)
        top.addStretch()
        self.addTaskBtn = PrimaryPushButton(FIF.ADD, "添加任务", self)
        self.addTaskBtn.clicked.connect(self.onAddTask)
        top.addWidget(self.addTaskBtn)
        self.batchAddBtn = PushButton(FIF.ALBUM, "批量添加", self)
        self.batchAddBtn.clicked.connect(self.onBatchAdd)
        top.addWidget(self.batchAddBtn)
        self.refreshBtn = PushButton(FIF.SYNC, "刷新", self)
        self.refreshBtn.clicked.connect(self.onRefresh)
        top.addWidget(self.refreshBtn)
        self.downloadBtn = PushButton(FIF.DOWNLOAD, "下载", self)
        self.downloadBtn.clicked.connect(self.onDownload)
        top.addWidget(self.downloadBtn)
        layout.addLayout(top)
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "ID", "参考图片", "提示词", "状态", "操作"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(100)
        self.table.setSelectionBehavior(TableWidget.SelectRows)
        self.table.setSelectionMode(TableWidget.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)
        layout.addWidget(self.table)
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
        self.loadTasks()
        # 初始列宽
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 220)

    def loadTasks(self):
        try:
            tasks, total_count = JimengIntlImageTask.get_tasks_by_page(self.current_page, self.page_size)
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
                checkbox = CheckBox()
                container = QWidget(self.table)
                container.setFixedHeight(self.table.rowHeight(row))
                c_layout = QHBoxLayout(container)
                c_layout.setContentsMargins(0, 0, 0, 0)
                c_layout.setSpacing(0)
                c_layout.setAlignment(Qt.AlignCenter)
                c_layout.addWidget(checkbox, 0, Qt.AlignCenter)
                self.table.setCellWidget(row, 0, container)

                id_item = QTableWidgetItem(str(task.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, id_item)

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
                    self.table.setRowHeight(row, 100)
                else:
                    item_img = QTableWidgetItem("无图片")
                    item_img.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 2, item_img)
                    self.table.setRowHeight(row, 100)

                pt = task.prompt or ""
                short = pt[:50] + ("..." if len(pt) > 50 else "")
                item_prompt = QTableWidgetItem(short)
                item_prompt.setToolTip(pt)
                item_prompt.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, item_prompt)

                status_map = {0: "排队中", 1: "生成中", 2: "已完成", 3: "失败"}
                item_status = QTableWidgetItem(status_map.get(task.status, "-"))
                item_status.setData(Qt.UserRole, task.id)
                item_status.setTextAlignment(Qt.AlignCenter)

                # 根据状态设置文字颜色
                if task.status == 2:  # 已完成
                    item_status.setForeground(QColor("#34C759"))  # 绿色
                elif task.status == 3:  # 失败
                    item_status.setForeground(QColor("#FF3B30"))  # 红色

                self.table.setItem(row, 4, item_status)

                # 操作按钮
                action_container = QWidget(self.table)
                action_container.setFixedHeight(self.table.rowHeight(row))
                action_layout = QHBoxLayout(action_container)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setSpacing(5)
                action_layout.setAlignment(Qt.AlignCenter)

                download_btn = PushButton("下载", action_container)
                download_btn.setFixedWidth(60)
                download_btn.clicked.connect(lambda checked, tid=task.id: self.onDownloadTask(tid))
                action_layout.addWidget(download_btn)

                retry_btn = PushButton("重试", action_container)
                retry_btn.setFixedWidth(60)
                retry_btn.clicked.connect(lambda checked, tid=task.id: self.onRetryTask(tid))
                action_layout.addWidget(retry_btn)

                self.table.setCellWidget(row, 5, action_container)

                # 已设置选择列居中，不重复创建容器
            total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
            self.pageInfoLabel.setText(f"第 {self.current_page} 页，共 {total_count} 条")
            self.prevPageBtn.setEnabled(self.current_page > 1)
            self.nextPageBtn.setEnabled(self.current_page < total_pages)
        except Exception as e:
            log.error(f"加载国际版任务失败: {e}")
            self.table.setRowCount(0)
            InfoBar.error(title="加载失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onAddTask(self):
        dlg = AddImageTaskIntlDialog(self)
        dlg.exec()
        self.loadTasks()

    def onRefresh(self):
        self.loadTasks()
        InfoBar.success(title="刷新成功", content="任务列表已更新", parent=self, duration=2000, position=InfoBarPosition.TOP)

    def showDownloadMessage(self, task_id: int):
        """显示下载提示信息"""
        InfoBar.info(
            title="下载提示",
            content="请在右上角的【下载】按钮处勾选此任务，然后使用批量下载功能",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )

    def onDownloadTask(self, task_id: int):
        """下载单个任务生成的图片"""
        try:
            from datetime import datetime

            task = JimengIntlImageTask.get_task_by_id(task_id)
            if not task:
                InfoBar.error(title="错误", content="任务不存在", parent=self, position=InfoBarPosition.TOP)
                return

            outputs = task.get_output_images()
            if not outputs:
                InfoBar.warning(title="提示", content="该任务还未生成图片", parent=self, position=InfoBarPosition.TOP)
                return

            # 选择保存目录
            save_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
            if not save_dir:
                return

            from app.utils.logger import log
            from PyQt5.QtCore import QObject, pyqtSignal
            import shutil

            # 创建带日期的文件夹
            date_str = datetime.now().strftime("%Y%m%d%H%M%S")
            download_folder = os.path.join(save_dir, f"即梦_图片_{date_str}")

            log.info(f"开始下载任务 {task_id} 的图片，保存到: {download_folder}")

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

            title_label = BodyLabel("正在下载图片", main_widget)
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

            # 创建信号发射器，用于跨线程通信
            class DownloadSignal(QObject):
                progress = pyqtSignal(int, int)
                finished = pyqtSignal(bool, str)

            signal_emitter = DownloadSignal()

            def on_progress_update(current, total):
                """进度更新回调（在主线程执行）"""
                status_label.setText(f"已下载 {current}/{total} 张图片")
                progress_bar.setValue(current)
                percentage = int((current / total * 100)) if total > 0 else 0
                progress_text.setText(f"{percentage}%")

            def on_download_finished(success, message):
                """下载完成回调（在主线程执行）"""
                loading_dlg.close()
                if success:
                    InfoBar.success(title="下载完成", content=message, parent=self, duration=3000, position=InfoBarPosition.TOP)
                    log.info(f"任务 {task_id} 图片下载完成: {message}")
                else:
                    InfoBar.error(title="下载失败", content=message, parent=self, position=InfoBarPosition.TOP)

            def download_task_images():
                """在子线程中下载任务图片"""
                success_count = 0
                fail_count = 0

                try:
                    # 创建目标文件夹，文件夹名为 task_{task_id}
                    folder = os.path.join(download_folder, f"task_{task_id}")
                    os.makedirs(folder, exist_ok=True)

                    for idx, image_url in enumerate(outputs):
                        try:
                            signal_emitter.progress.emit(idx, len(outputs))

                            # 检查是否是 URL
                            if image_url.startswith("http://") or image_url.startswith("https://"):
                                # 网络下载
                                import requests
                                response = requests.get(image_url, timeout=60)
                                response.raise_for_status()

                                # 从 URL 提取文件名
                                fname = os.path.basename(image_url.split('?')[0])
                                # 处理文件名中的非法字符
                                fname = re.sub(r'[<>:"/\\|?*]', '_', fname)

                                if not fname.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                    fname = f"image_{idx + 1}.jpeg"

                                filepath = os.path.join(folder, fname)
                                with open(filepath, 'wb') as f:
                                    f.write(response.content)
                                success_count += 1
                                log.debug(f"图片 {idx + 1} 下载成功: {filepath}")
                            else:
                                # 本地文件
                                if image_url.lower().startswith("file:///"):
                                    p = image_url[8:].replace('/', '\\')
                                else:
                                    p = image_url

                                if os.path.exists(p):
                                    fname = os.path.basename(p)
                                    shutil.copy2(p, os.path.join(folder, fname))
                                    success_count += 1
                                    log.debug(f"图片 {idx + 1} 下载成功: {fname}")
                                else:
                                    fail_count += 1
                                    log.warning(f"图片 {idx + 1} 文件不存在: {p}")

                        except Exception as e:
                            log.error(f"下载图片 {idx + 1} 失败: {e}")
                            fail_count += 1

                    signal_emitter.progress.emit(len(outputs), len(outputs))

                    if success_count > 0:
                        msg = f"成功下载 {success_count} 张图片"
                        if fail_count > 0:
                            msg += f"，{fail_count} 张失败"
                        signal_emitter.finished.emit(True, msg)
                    else:
                        signal_emitter.finished.emit(False, "未找到任何图片文件")

                except Exception as e:
                    log.error(f"下载任务 {task_id} 失败: {e}")
                    signal_emitter.finished.emit(False, str(e))

            # 连接信号到主线程的槽函数
            signal_emitter.progress.connect(on_progress_update)
            signal_emitter.finished.connect(on_download_finished)

            # 在子线程中执行下载
            download_thread = QThread()
            download_thread.run = download_task_images
            download_thread.start()

            loading_dlg.exec()

        except Exception as e:
            log.error(f"下载任务图片失败: {e}")
            InfoBar.error(title="下载失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onRetryTask(self, task_id: int):
        """重新执行任务"""
        try:
            task = JimengIntlImageTask.get_task_by_id(task_id)
            if not task:
                InfoBar.error(title="错误", content="任务不存在", parent=self, position=InfoBarPosition.TOP)
                return

            # 重置任务状态为排队中
            task.status = 0
            task.code = None
            task.message = None
            task.update_at = datetime.now()
            task.save()

            log.info(f"任务 {task_id} 已重置为排队状态")
            self.loadTasks()
            InfoBar.success(title="重试成功", content="任务已重新加入队列", parent=self, duration=2000, position=InfoBarPosition.TOP)

        except Exception as e:
            log.error(f"重新执行任务失败: {e}")
            InfoBar.error(title="重试失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

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

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # 维持图片列与状态列的最小宽度，提示词列自动伸缩
        self.table.setColumnWidth(2, max(160, self.table.columnWidth(2)))
        self.table.setColumnWidth(5, max(100, self.table.columnWidth(5)))

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
                    status_item = self.table.item(row, 4)
                    if status_item:
                        task_id = status_item.data(Qt.UserRole)
                        if task_id:
                            ids.append(int(task_id))
        return ids

    def onDownload(self):
        selected_ids = self._getSelectedTaskIds()
        if not selected_ids:
            InfoBar.warning(title="提示", content="请先勾选要下载的任务", parent=self, position=InfoBarPosition.TOP)
            return

        download_dir = QFileDialog.getExistingDirectory(self, "选择下载目录", "", QFileDialog.ShowDirsOnly)
        if not download_dir:
            return

        from app.utils.logger import log
        from PyQt5.QtCore import QObject, pyqtSignal
        from datetime import datetime
        import shutil

        # 创建带日期的文件夹
        date_str = datetime.now().strftime("%Y%m%d%H%M%S")
        download_folder = os.path.join(download_dir, f"即梦_图片_{date_str}")

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

        title_label = BodyLabel("正在下载图片", main_widget)
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

        # 创建信号发射器，用于跨线程通信
        class DownloadSignal(QObject):
            progress = pyqtSignal(int, int)
            finished = pyqtSignal(int, int)

        signal_emitter = DownloadSignal()

        def on_progress_update(current, total):
            """进度更新回调（在主线程执行）"""
            status_label.setText(f"已处理 {current}/{total} 个任务")
            progress_bar.setValue(current)
            percentage = int((current / total * 100)) if total > 0 else 0
            progress_text.setText(f"{percentage}%")

        def on_download_finished(completed, failed):
            """下载完成回调（在主线程执行）"""
            loading_dlg.close()
            if completed > 0:
                msg = f"成功下载 {completed} 个任务"
                if failed > 0:
                    msg += f"，{failed} 个失败"
                InfoBar.success(title="下载完成", content=msg, parent=self, duration=3000, position=InfoBarPosition.TOP)
                log.info(f"批量下载完成: {msg}")
            else:
                InfoBar.error(title="下载失败", content="所有任务下载失败", parent=self, position=InfoBarPosition.TOP)

        def download_all_tasks():
            """在子线程中下载所有任务"""
            import requests
            completed = 0
            failed = 0

            for idx, task_id in enumerate(selected_ids):
                try:
                    task = JimengIntlImageTask.get_task_by_id(task_id)
                    if not task:
                        failed += 1
                        signal_emitter.progress.emit(idx + 1, len(selected_ids))
                        continue

                    outputs = task.get_output_images()
                    if not outputs:
                        failed += 1
                        signal_emitter.progress.emit(idx + 1, len(selected_ids))
                        continue

                    folder = os.path.join(download_folder, f"task_{task_id}")
                    os.makedirs(folder, exist_ok=True)

                    for p in outputs:
                        try:
                            # 检查是否是 URL
                            if p.startswith("http://") or p.startswith("https://"):
                                # 网络下载
                                response = requests.get(p, timeout=60)
                                response.raise_for_status()

                                # 从 URL 提取文件名
                                fname = os.path.basename(p.split('?')[0])
                                if not fname.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                    fname = f"image_{len(os.listdir(folder)) + 1}.jpeg"

                                filepath = os.path.join(folder, fname)
                                with open(filepath, 'wb') as f:
                                    f.write(response.content)
                                log.debug(f"图片下载成功: {filepath}")
                            else:
                                # 本地文件
                                if p.lower().startswith("file:///"):
                                    p2 = p[8:].replace('/', '\\')
                                else:
                                    p2 = p

                                if os.path.exists(p2):
                                    fname = os.path.basename(p2)
                                    shutil.copy2(p2, os.path.join(folder, fname))
                                    log.debug(f"文件复制成功: {fname}")
                                else:
                                    log.warning(f"文件不存在: {p2}")
                        except Exception as e:
                            log.error(f"下载或复制文件失败: {e}")

                    completed += 1
                    log.debug(f"任务 {task_id} 下载完成")

                except Exception as e:
                    failed += 1
                    log.error(f"下载任务 {task_id} 的图片失败: {e}")

                signal_emitter.progress.emit(idx + 1, len(selected_ids))

            signal_emitter.finished.emit(completed, failed)

        # 连接信号到主线程的槽函数
        signal_emitter.progress.connect(on_progress_update)
        signal_emitter.finished.connect(on_download_finished)

        # 在子线程中执行下载
        download_thread = QThread()
        download_thread.run = download_all_tasks
        download_thread.start()

        loading_dlg.exec()

    def showContextMenu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        status_item = self.table.item(row, 4)
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
            ok = JimengIntlImageTask.mark_deleted(task_id)
            if ok:
                InfoBar.success(title="删除成功", content=f"任务 #{task_id} 已删除", parent=self, duration=2000, position=InfoBarPosition.TOP)
                self.loadTasks()
            else:
                InfoBar.error(title="删除失败", content="任务不存在", parent=self, position=InfoBarPosition.TOP)

    def onBatchAdd(self):
        dlg = BatchAddImageTaskIntlDialog(self)
        def on_added(tasks_data):
            try:
                from app.models.jimeng_intl_image_task import JimengIntlImageTask
                ok = 0
                for t in tasks_data:
                    try:
                        JimengIntlImageTask.create_task(
                            prompt=t.get('prompt', ''),
                            account_id=None,
                            ratio=t.get('ratio', '1:1'),
                            model=t.get('model', 'jimeng-4.5'),
                            resolution=t.get('resolution', '2k'),
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

class BatchAddImageTaskIntlDialog(Dialog):
    from PyQt5.QtCore import pyqtSignal
    tasks_added = pyqtSignal(list)
    def __init__(self, parent=None):
        super().__init__("", "", parent)
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.desktop().screenGeometry()
        w = min(1000, int(screen.width() * 0.9))
        h = min(825, int(screen.height() * 0.9))
        self.setFixedSize(w, h)
        self.titleLabel.setVisible(False)
        self._initUI()
    def _center(self):
        from PyQt5.QtWidgets import QApplication
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
        self.text_widget = _TextPromptImportIntlWidget(self.stacked)
        self.folder_widget = _FolderImportIntlWidget(self.stacked)
        self.table_widget = _TableImportIntlWidget(self.stacked)
        self.seq_widget = _SequentialAddIntlWidget(self.stacked)
        self.stacked.addWidget(self.text_widget)
        self.stacked.addWidget(self.folder_widget)
        self.stacked.addWidget(self.table_widget)
        self.stacked.addWidget(self.seq_widget)
        self.pivot.addItem(routeKey='text', text='文本导入', onClick=lambda: self.stacked.setCurrentWidget(self.text_widget))
        self.pivot.addItem(routeKey='folder', text='文件夹导入', onClick=lambda: self.stacked.setCurrentWidget(self.folder_widget))
        self.pivot.addItem(routeKey='table', text='表格导入', onClick=lambda: self.stacked.setCurrentWidget(self.table_widget))
        self.pivot.addItem(routeKey='seq', text='依次添加', onClick=lambda: self.stacked.setCurrentWidget(self.seq_widget))
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

class _ModelRatioResolutionMixin:
    def _init_mrr(self, owner):
        ml = QHBoxLayout()

        ml.addWidget(BodyLabel("模型:", owner))
        self.model_combo = ComboBox(owner)
        self.model_combo.addItems(['nanobananapro', 'nanobanana', 'jimeng-4.5', 'jimeng-4.1', 'jimeng-4.0', 'jimeng-3.0'])
        self.model_combo.setCurrentText('jimeng-4.5')
        self.model_combo.setFixedWidth(160)
        ml.addWidget(self.model_combo)

        ml.addSpacing(15)
        ml.addWidget(BodyLabel("分辨率比例:", owner))
        self.ratio_combo = ComboBox(owner)
        self.ratio_combo.addItems(['1:1', '4:3', '3:4', '16:9', '9:16', '3:2', '2:3', '21:9'])
        self.ratio_combo.setCurrentText('1:1')
        self.ratio_combo.setFixedWidth(100)
        ml.addWidget(self.ratio_combo)

        ml.addSpacing(15)
        ml.addWidget(BodyLabel("清晰度:", owner))
        self.resolution_combo = ComboBox(owner)
        self.resolution_combo.addItems(['1k', '2k', '4k'])
        self.resolution_combo.setCurrentText('2k')
        self.resolution_combo.setFixedWidth(100)
        ml.addWidget(self.resolution_combo)

        ml.addStretch()
        return ml

    def _on_model_changed(self, m):
        # 已弃用，保留以兼容旧代码
        pass

class _FolderImportIntlWidget(QWidget, _ModelRatioResolutionMixin):
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
        layout.addLayout(self._init_mrr(self))
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
                self.preview_label.setText(f"找到 {len(files)} 张图片")
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
                'resolution': self.resolution_combo.currentText(),
                'input_images': [p]
            })
        return tasks

class _TableImportIntlWidget(QWidget, _ModelRatioResolutionMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.excel_path = ""
        self._initUI()
    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        fl = QHBoxLayout()
        fl.addWidget(BodyLabel("选择文件:", self))
        self.file_edit = LineEdit(self)
        self.file_edit.setReadOnly(True)
        fl.addWidget(self.file_edit)
        btn = PushButton(FIF.DOCUMENT, "浏览", self)
        btn.clicked.connect(self._on_select_file)
        fl.addWidget(btn)
        layout.addLayout(fl)
        layout.addLayout(self._init_mrr(self))
        self.preview_table = QTableWidget(self)
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(['提示词', '模型', '参考图片路径', '分辨率比例', '清晰度'])
        h = self.preview_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Interactive)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        h.setSectionResizeMode(4, QHeaderView.Fixed)
        self.preview_table.setColumnWidth(3, 80)
        self.preview_table.setColumnWidth(4, 100)
        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.preview_table.setStyleSheet(
            "QTableWidget{background-color:#1f1f1f;color:#e5e5e5;gridline-color:#2d2d2d;}"
            "QTableWidget::item:selected{background-color:#2a2a2a;color:#ffffff;}"
            "QTableWidget::item{padding:6px;}"
            "QTableWidget QHeaderView::section{background-color:#2b2b2b;color:#dcdcdc;border:0px;"
            "border-bottom:1px solid #3a3a3a;padding:8px 6px;}"
        )
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color:#303030;color:#dcdcdc;border:0px;border-bottom:1px solid #3a3a3a;padding:8px 6px;}"
        )
        layout.addWidget(self.preview_table)
        self.status_label = BodyLabel("请选择Excel文件", self)
        layout.addWidget(self.status_label)
    def _on_select_file(self):
        fp, _ = QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if fp:
            self.excel_path = fp
            self.file_edit.setText(fp)
            self._load_excel()
    def _load_excel(self):
        try:
            import pandas as pd
            df = pd.read_excel(self.excel_path)
            req = ['提示词', '模型']
            miss = [c for c in req if c not in df.columns]
            if miss:
                self.status_label.setText(f"缺少必需列: {', '.join(miss)}")
                return
            self.preview_table.setRowCount(0)
            for _, row in df.iterrows():
                r = self.preview_table.rowCount()
                self.preview_table.insertRow(r)
                self.preview_table.setItem(r, 0, QTableWidgetItem(str(row.get('提示词', ''))))
                self.preview_table.setItem(r, 1, QTableWidgetItem(str(row.get('模型', ''))))
                self.preview_table.setItem(r, 2, QTableWidgetItem(str(row.get('参考图片路径', ''))))
                self.preview_table.setItem(r, 3, QTableWidgetItem(str(row.get('分辨率比例', ''))))
                self.preview_table.setItem(r, 4, QTableWidgetItem(str(row.get('清晰度', ''))))
            self.status_label.setText(f"成功加载 {len(df)} 条记录")
        except Exception as e:
            self.status_label.setText(f"加载失败: {str(e)}")
    def get_tasks_data(self):
        if not self.excel_path:
            return []
        try:
            import pandas as pd
            df = pd.read_excel(self.excel_path)
            tasks = []
            for _, row in df.iterrows():
                imgs = []
                ips = str(row.get('参考图片路径', '')).strip()
                if ips and ips != 'nan':
                    s = ips.replace('；', ';').replace('，', ',')
                    if ';' in s:
                        imgs = [p.strip() for p in s.split(';') if p.strip()]
                    elif ',' in s:
                        imgs = [p.strip() for p in s.split(',') if p.strip()]
                    else:
                        imgs = [s]
                tasks.append({
                    'prompt': str(row.get('提示词', '')),
                    'model': str(row.get('模型', self.model_combo.currentText())),
                    'ratio': str(row.get('分辨率比例', self.ratio_combo.currentText())),
                    'resolution': str(row.get('清晰度', self.resolution_combo.currentText())),
                    'input_images': imgs
                })
            return tasks
        except Exception:
            return []

class _TextPromptImportIntlWidget(QWidget, _ModelRatioResolutionMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._initUI()
    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        layout.addLayout(self._init_mrr(self))
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
            'resolution': self.resolution_combo.currentText(),
            'input_images': []
        } for p in lines]

class _SequentialAddIntlWidget(QWidget, _ModelRatioResolutionMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self._initUI()
    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        top = self._init_mrr(self)
        add_btn = PrimaryPushButton(FIF.ADD, "添加到列表", self)
        add_btn.clicked.connect(self._on_add)
        top.addWidget(add_btn)
        layout.addLayout(top)
        layout.addWidget(BodyLabel("提示词:", self))
        self.prompt_edit = TextEdit(self)
        self.prompt_edit.setFixedHeight(60)
        layout.addWidget(self.prompt_edit)
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['提示词', '分辨率比例', '操作'])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Fixed)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setStyleSheet(
            "QTableWidget{background-color:#1f1f1f;color:#e5e5e5;gridline-color:#2d2d2d;}"
            "QTableWidget::item:selected{background-color:#2a2a2a;color:#ffffff;}"
            "QTableWidget::item{padding:6px;}"
            "QTableWidget QHeaderView::section{background-color:#2b2b2b;color:#dcdcdc;border:0px;"
            "border-bottom:1px solid #3a3a3a;padding:8px 6px;}"
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section{background-color:#303030;color:#dcdcdc;border:0px;border-bottom:1px solid #3a3a3a;padding:8px 6px;}"
        )
        layout.addWidget(self.table)
    def _on_add(self):
        p = self.prompt_edit.toPlainText().strip()
        if not p:
            return
        t = {
            'prompt': p,
            'model': self.model_combo.currentText(),
            'ratio': self.ratio_combo.currentText(),
            'resolution': self.resolution_combo.currentText(),
            'input_images': []
        }
        self.tasks.append(t)
        self._update_table()
        self.prompt_edit.clear()
    def _update_table(self):
        self.table.setRowCount(0)
        for i, t in enumerate(self.tasks):
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(t['prompt']))
            self.table.setItem(r, 1, QTableWidgetItem(t['ratio']))
            btn = PushButton(FIF.DELETE, "", self.table)
            btn.setFixedSize(60, 30)
            def _mk(idx=i):
                self._del(idx)
            btn.clicked.connect(_mk)
            self.table.setCellWidget(r, 2, btn)
    def _del(self, idx):
        if 0 <= idx < len(self.tasks):
            self.tasks.pop(idx)
            self._update_table()
    def get_tasks_data(self):
        return self.tasks
