# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView,
                              QLabel, QCheckBox, QApplication, QSizePolicy)
from qfluentwidgets import (PrimaryPushButton, PushButton, TableWidget, ComboBox,
                            FluentIcon as FIF, InfoBar, InfoBarPosition, BodyLabel, CheckBox)
from app.utils.logger import log
from app.models.jimeng_image_task import JimengImageTask
import os


class ImageGenView(QWidget):
    """图片生成视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.page_size = 20
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(20)

        # 顶部按钮区域
        buttonLayout = QHBoxLayout()

        # 全选复选框
        self.selectAllCheckBox = CheckBox("全选", self)
        self.selectAllCheckBox.stateChanged.connect(self.onSelectAllChanged)
        buttonLayout.addWidget(self.selectAllCheckBox)

        buttonLayout.addStretch()

        self.addTaskBtn = PrimaryPushButton(FIF.ADD, "添加任务", self)
        self.addTaskBtn.clicked.connect(self.onAddTask)
        buttonLayout.addWidget(self.addTaskBtn)

        self.batchAddBtn = PushButton(FIF.ALBUM, "批量添加", self)
        self.batchAddBtn.clicked.connect(self.onBatchAdd)
        buttonLayout.addWidget(self.batchAddBtn)

        self.refreshBtn = PushButton(FIF.SYNC, "刷新", self)
        self.refreshBtn.clicked.connect(self.onRefresh)
        buttonLayout.addWidget(self.refreshBtn)

        self.downloadBtn = PushButton(FIF.DOWNLOAD, "下载", self)
        self.downloadBtn.clicked.connect(self.onDownload)
        buttonLayout.addWidget(self.downloadBtn)

        layout.addLayout(buttonLayout)

        # 任务表格
        self.taskTable = TableWidget(self)
        self.taskTable.setBorderVisible(True)
        self.taskTable.setBorderRadius(8)
        self.taskTable.setWordWrap(False)

        # 设置表格列 - 列顺序：选择、ID、参考图片、模型、提示词、结果、状态
        self.taskTable.setColumnCount(7)
        self.taskTable.setHorizontalHeaderLabels(['', 'ID', '参考图片', '模型', '提示词', '结果', '状态'])

        # 设置列宽按比例自适应
        header = self.taskTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)        # 选择框
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # ID
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # 参考图片
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # 模型
        header.setSectionResizeMode(4, QHeaderView.Stretch)      # 提示词（自动伸缩）
        header.setSectionResizeMode(5, QHeaderView.Interactive)  # 结果
        header.setSectionResizeMode(6, QHeaderView.Interactive)  # 状态

        # 设置初始比例宽度
        # 使用基准单位来计算，1份 = 80px
        base_unit = 80
        self.taskTable.setColumnWidth(0, 50)             # 选择框: 50px
        self.taskTable.setColumnWidth(1, base_unit * 1)  # ID: 80px (1份)
        self.taskTable.setColumnWidth(2, base_unit * 2)  # 参考图片: 160px (2份)
        self.taskTable.setColumnWidth(3, base_unit * 2)  # 模型: 160px (2份)
        # 提示词会自动伸缩填充剩余空间 (4份，约320px)
        self.taskTable.setColumnWidth(5, base_unit * 2)  # 结果: 160px (2份)
        self.taskTable.setColumnWidth(6, base_unit * 2)  # 状态: 160px (2份)


        # 设置行高
        self.taskTable.verticalHeader().setDefaultSectionSize(90)

        # 设置选择模式
        self.taskTable.setSelectionBehavior(TableWidget.SelectRows)
        self.taskTable.setSelectionMode(TableWidget.ExtendedSelection)

        # 隐藏垂直表头（行号）
        self.taskTable.verticalHeader().setVisible(False)

        layout.addWidget(self.taskTable)

        # 分页控制区域
        paginationLayout = QHBoxLayout()

        # 每页显示数量
        pageSizeLabel = BodyLabel("每页显示:", self)
        paginationLayout.addWidget(pageSizeLabel)

        self.pageSizeCombo = ComboBox(self)
        self.pageSizeCombo.addItems(['10', '20', '50', '100', '500', '1000'])
        self.pageSizeCombo.setCurrentText('20')
        self.pageSizeCombo.currentTextChanged.connect(self.onPageSizeChanged)
        self.pageSizeCombo.setFixedWidth(100)
        paginationLayout.addWidget(self.pageSizeCombo)

        paginationLayout.addStretch()

        # 分页信息
        self.pageInfoLabel = BodyLabel("第 1 页，共 0 条", self)
        paginationLayout.addWidget(self.pageInfoLabel)

        paginationLayout.addSpacing(20)

        # 分页按钮
        self.firstPageBtn = PushButton(FIF.CARE_LEFT_SOLID, "首页", self)
        self.firstPageBtn.clicked.connect(self.onFirstPage)
        paginationLayout.addWidget(self.firstPageBtn)

        self.prevPageBtn = PushButton(FIF.CARE_LEFT_SOLID, "上一页", self)
        self.prevPageBtn.clicked.connect(self.onPrevPage)
        paginationLayout.addWidget(self.prevPageBtn)

        self.nextPageBtn = PushButton(FIF.CARE_RIGHT_SOLID, "下一页", self)
        self.nextPageBtn.clicked.connect(self.onNextPage)
        paginationLayout.addWidget(self.nextPageBtn)

        self.lastPageBtn = PushButton(FIF.CARE_RIGHT_SOLID, "末页", self)
        self.lastPageBtn.clicked.connect(self.onLastPage)
        paginationLayout.addWidget(self.lastPageBtn)

        layout.addLayout(paginationLayout)

        # 加载数据
        self.loadTasks()

    def loadTasks(self):
        """加载任务数据"""
        try:
            from app.models.jimeng_image_task import JimengImageTask

            # 从数据库分页获取任务
            tasks, total_count = JimengImageTask.get_tasks_by_page(
                page=self.current_page,
                page_size=self.page_size
            )

            # 清空表格 - 彻底清除所有widget和内容
            old_row_count = self.taskTable.rowCount()

            # 先移除所有的cellWidget并立即删除
            for row in range(old_row_count):
                for col in range(self.taskTable.columnCount()):
                    widget = self.taskTable.cellWidget(row, col)
                    if widget:
                        self.taskTable.removeCellWidget(row, col)
                        widget.setParent(None)
                        widget.deleteLater()

            # 清空所有内容并重置行数
            self.taskTable.clearContents()
            self.taskTable.setRowCount(0)

            # 强制处理待删除的对象
            QApplication.processEvents()

            # 设置新的行数
            self.taskTable.setRowCount(len(tasks))

            # 填充数据 - 列顺序：选择、ID、参考图片、模型、提示词、结果、状态
            for row, task in enumerate(tasks):
                # 先设置行高
                self.taskTable.setRowHeight(row, 90)

                # 列0: 复选框 - 使用固定高度容器确保稳定居中
                checkbox = CheckBox()
                checkbox.setObjectName(f"checkbox_{row}")

                checkbox_container = QWidget(self.taskTable)
                checkbox_container.setObjectName(f"container_{row}")
                # 设置固定高度与行高一致，确保布局稳定
                checkbox_container.setFixedHeight(90)
                checkbox_container.setStyleSheet("background: transparent;")

                # 使用QHBoxLayout并设置对齐
                container_layout = QHBoxLayout(checkbox_container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(0)
                container_layout.setAlignment(Qt.AlignCenter)
                container_layout.addWidget(checkbox, 0, Qt.AlignCenter)

                self.taskTable.setCellWidget(row, 0, checkbox_container)

                # 列1: ID
                id_item = QTableWidgetItem(str(task.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.taskTable.setItem(row, 1, id_item)

                # 列2: 参考图片 - 显示缩略图（最多一张）
                image_paths = task.get_input_image_paths()
                if image_paths and len(image_paths) > 0:
                    # 显示第一张图片的缩略图
                    image_path = image_paths[0]
                    if os.path.exists(image_path):
                        image_label = QLabel()
                        pixmap = QPixmap(image_path)
                        scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        image_label.setPixmap(scaled_pixmap)
                        image_label.setAlignment(Qt.AlignCenter)
                        self.taskTable.setCellWidget(row, 2, image_label)
                    else:
                        # 图片文件不存在
                        no_image_item = QTableWidgetItem("文件不存在")
                        no_image_item.setTextAlignment(Qt.AlignCenter)
                        self.taskTable.setItem(row, 2, no_image_item)
                else:
                    # 没有参考图片
                    no_image_item = QTableWidgetItem("无")
                    no_image_item.setTextAlignment(Qt.AlignCenter)
                    self.taskTable.setItem(row, 2, no_image_item)

                # 列3: 模型
                model_item = QTableWidgetItem(task.image_model or "未指定")
                model_item.setTextAlignment(Qt.AlignCenter)
                self.taskTable.setItem(row, 3, model_item)

                # 列4: 提示词（缩短显示）
                prompt_text = task.prompt
                if len(prompt_text) > 50:
                    prompt_text = prompt_text[:50] + "..."
                prompt_item = QTableWidgetItem(prompt_text)
                prompt_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                prompt_item.setToolTip(task.prompt)  # 完整提示词作为提示
                self.taskTable.setItem(row, 4, prompt_item)

                # 列5: 结果 - 显示生成的图片（第一张）
                output_images = task.get_output_images()
                if output_images and len(output_images) > 0:
                    # 显示第一张生成图片的缩略图
                    output_path = output_images[0]
                    if os.path.exists(output_path):
                        result_label = QLabel()
                        pixmap = QPixmap(output_path)
                        scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        result_label.setPixmap(scaled_pixmap)
                        result_label.setAlignment(Qt.AlignCenter)
                        self.taskTable.setCellWidget(row, 5, result_label)
                    else:
                        no_result_item = QTableWidgetItem("文件不存在")
                        no_result_item.setTextAlignment(Qt.AlignCenter)
                        self.taskTable.setItem(row, 5, no_result_item)
                else:
                    # 还没有生成结果
                    if task.status == 'success':
                        no_result_item = QTableWidgetItem("无结果")
                    else:
                        no_result_item = QTableWidgetItem("-")
                    no_result_item.setTextAlignment(Qt.AlignCenter)
                    self.taskTable.setItem(row, 5, no_result_item)

                # 列6: 状态
                status_map = {
                    'pending': '等待中',
                    'processing': '处理中',
                    'success': '成功',
                    'failed': '失败'
                }
                status_text = status_map.get(task.status, task.status)
                status_item = QTableWidgetItem(status_text)
                status_item.setTextAlignment(Qt.AlignCenter)
                self.taskTable.setItem(row, 6, status_item)

            # 更新分页信息
            self.updatePageInfo(total_count)

            log.info(f"加载第 {self.current_page} 页任务，每页 {self.page_size} 条，共 {total_count} 条")

        except Exception as e:
            log.error(f"加载任务失败: {e}")
            self.taskTable.setRowCount(0)
            self.updatePageInfo(0)

    def updatePageInfo(self, total_count):
        """更新分页信息"""
        total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
        self.pageInfoLabel.setText(f"第 {self.current_page} 页，共 {total_count} 条")

        # 更新按钮状态
        self.firstPageBtn.setEnabled(self.current_page > 1)
        self.prevPageBtn.setEnabled(self.current_page > 1)
        self.nextPageBtn.setEnabled(self.current_page < total_pages)
        self.lastPageBtn.setEnabled(self.current_page < total_pages)

    def onPageSizeChanged(self, size):
        """每页数量改变"""
        self.page_size = int(size)
        self.current_page = 1
        self.loadTasks()

    def onFirstPage(self):
        """首页"""
        self.current_page = 1
        self.loadTasks()

    def onPrevPage(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.loadTasks()

    def onNextPage(self):
        """下一页"""
        self.current_page += 1
        self.loadTasks()

    def onLastPage(self):
        """末页"""
        try:
            from app.models.jimeng_image_task import JimengImageTask
            _, total_count = JimengImageTask.get_tasks_by_page(
                page=1,
                page_size=self.page_size
            )
            total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
            self.current_page = total_pages
            self.loadTasks()
        except Exception as e:
            log.error(f"跳转到末页失败: {e}")

    def onAddTask(self):
        """添加任务"""
        from app.view.jimeng.add_image_task_dialog import AddImageTaskDialog
        from app.models.jimeng_image_task import JimengImageTask

        dialog = AddImageTaskDialog(self)
        dialog.task_added.connect(self.onTaskAdded)
        dialog.exec()

    def onTaskAdded(self, task_data):
        """任务添加完成"""
        try:
            # 创建任务到数据库
            task = JimengImageTask.create_task(
                prompt=task_data['prompt'],
                input_image_paths=task_data.get('input_image_paths', []),
                image_model=task_data.get('image_model', ''),
                aspect_ratio=task_data['aspect_ratio'],
                resolution=task_data['resolution']
            )

            log.info(f"任务已添加: ID={task.id}")

            InfoBar.success(
                title="添加成功",
                content=f"任务已添加到列表",
                parent=self,
                duration=2000,
                position=InfoBarPosition.TOP
            )

            # 刷新列表
            self.loadTasks()

        except Exception as e:
            log.error(f"添加任务失败: {e}")
            InfoBar.error(
                title="添加失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )

    def onBatchAdd(self):
        """批量添加"""
        from app.view.jimeng.batch_add_image_task_dialog import BatchAddImageTaskDialog

        dialog = BatchAddImageTaskDialog(self)
        dialog.tasks_added.connect(self.onBatchTasksAdded)
        dialog.exec()

    def onBatchTasksAdded(self, tasks_data_list):
        """批量任务添加完成"""
        try:
            from app.models.jimeng_image_task import JimengImageTask

            success_count = 0
            fail_count = 0

            for task_data in tasks_data_list:
                try:
                    task = JimengImageTask.create_task(
                        prompt=task_data['prompt'],
                        input_image_paths=task_data.get('input_image_paths', []),
                        image_model=task_data.get('image_model', '图片 4.0'),
                        aspect_ratio=task_data['aspect_ratio'],
                        resolution=task_data['resolution']
                    )
                    success_count += 1
                except Exception as e:
                    log.error(f"创建任务失败: {e}")
                    fail_count += 1

            log.info(f"批量添加完成: 成功 {success_count} 个, 失败 {fail_count} 个")

            if success_count > 0:
                InfoBar.success(
                    title="批量添加成功",
                    content=f"成功添加 {success_count} 个任务" + (f"，{fail_count} 个失败" if fail_count > 0 else ""),
                    parent=self,
                    duration=3000,
                    position=InfoBarPosition.TOP
                )

                # 刷新列表
                self.loadTasks()
            else:
                InfoBar.error(
                    title="批量添加失败",
                    content="所有任务添加失败",
                    parent=self,
                    position=InfoBarPosition.TOP
                )

        except Exception as e:
            log.error(f"批量添加任务失败: {e}")
            InfoBar.error(
                title="批量添加失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )

    def onRefresh(self):
        """刷新"""
        log.info("刷新任务列表")
        self.loadTasks()
        InfoBar.success(
            title="刷新成功",
            content="任务列表已更新",
            parent=self,
            duration=2000,
            position=InfoBarPosition.TOP
        )

    def onSelectAllChanged(self, state):
        """全选/取消全选"""
        is_checked = (state == Qt.Checked)
        for row in range(self.taskTable.rowCount()):
            container = self.taskTable.cellWidget(row, 0)
            if container:
                # 直接查找第一个CheckBox子widget
                checkbox = container.findChild(CheckBox)
                if checkbox:
                    checkbox.setChecked(is_checked)

    def getSelectedTaskIds(self):
        """获取选中的任务ID列表"""
        selected_ids = []
        for row in range(self.taskTable.rowCount()):
            container = self.taskTable.cellWidget(row, 0)
            if container:
                # 直接查找第一个CheckBox子widget
                checkbox = container.findChild(CheckBox)
                if checkbox and checkbox.isChecked():
                    # 获取该行的任务ID（第1列）
                    id_item = self.taskTable.item(row, 1)
                    if id_item:
                        selected_ids.append(int(id_item.text()))
        return selected_ids

    def onDownload(self):
        """下载选中项"""
        selected_ids = self.getSelectedTaskIds()
        if not selected_ids:
            InfoBar.warning(
                title="提示",
                content="请先勾选要下载的任务",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return

        # 弹出文件夹选择对话框
        from PyQt5.QtWidgets import QFileDialog
        download_dir = QFileDialog.getExistingDirectory(
            self,
            "选择下载目录",
            "",
            QFileDialog.ShowDirsOnly
        )

        if not download_dir:
            log.info("用户取消了下载")
            return

        log.info(f"下载 {len(selected_ids)} 个任务到: {download_dir}")

        # 在后台线程执行下载
        from PyQt5.QtCore import QThread, pyqtSignal
        import shutil

        class DownloadThread(QThread):
            """下载线程"""
            progress = pyqtSignal(int, int, str)  # 当前进度, 总数, 消息
            finished = pyqtSignal(int, int)  # 成功数, 失败数

            def __init__(self, task_ids, download_dir):
                super().__init__()
                self.task_ids = task_ids
                self.download_dir = download_dir

            def run(self):
                success_count = 0
                fail_count = 0

                for idx, task_id in enumerate(self.task_ids):
                    try:
                        task = JimengImageTask.get_task_by_id(task_id)
                        if not task:
                            self.progress.emit(idx + 1, len(self.task_ids), f"任务 {task_id} 不存在")
                            fail_count += 1
                            continue

                        # 获取所有输出图片
                        output_images = task.get_output_images()
                        if not output_images:
                            self.progress.emit(idx + 1, len(self.task_ids), f"任务 {task_id} 没有输出图片")
                            fail_count += 1
                            continue

                        # 复制图片到下载目录
                        task_folder = os.path.join(self.download_dir, f"task_{task_id}")
                        os.makedirs(task_folder, exist_ok=True)

                        for img_idx, img_path in enumerate(output_images):
                            if os.path.exists(img_path):
                                # 保留原始文件名或使用编号
                                filename = os.path.basename(img_path)
                                dest_path = os.path.join(task_folder, filename)
                                shutil.copy2(img_path, dest_path)
                            else:
                                log.warning(f"图片文件不存在: {img_path}")

                        self.progress.emit(idx + 1, len(self.task_ids), f"任务 {task_id} 下载完成")
                        success_count += 1

                    except Exception as e:
                        log.error(f"下载任务 {task_id} 失败: {e}")
                        self.progress.emit(idx + 1, len(self.task_ids), f"任务 {task_id} 下载失败: {str(e)}")
                        fail_count += 1

                self.finished.emit(success_count, fail_count)

        # 创建并启动下载线程
        self.download_thread = DownloadThread(selected_ids, download_dir)

        def on_progress(current, total, message):
            log.info(f"下载进度: {current}/{total} - {message}")

        def on_finished(success, fail):
            log.info(f"下载完成: 成功 {success} 个, 失败 {fail} 个")
            if success > 0:
                InfoBar.success(
                    title="下载完成",
                    content=f"成功下载 {success} 个任务" + (f"，{fail} 个失败" if fail > 0 else ""),
                    parent=self,
                    duration=3000,
                    position=InfoBarPosition.TOP
                )
            else:
                InfoBar.error(
                    title="下载失败",
                    content="所有任务下载失败",
                    parent=self,
                    position=InfoBarPosition.TOP
                )

        self.download_thread.progress.connect(on_progress)
        self.download_thread.finished.connect(on_finished)
        self.download_thread.start()

        InfoBar.info(
            title="开始下载",
            content=f"正在后台下载 {len(selected_ids)} 个任务...",
            parent=self,
            duration=2000,
            position=InfoBarPosition.TOP
        )
