# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFileDialog,
                            QLabel, QGridLayout, QTableWidget, QTableWidgetItem,
                            QHeaderView, QAbstractItemView, QStackedWidget, QScrollArea)
from qfluentwidgets import (Dialog, LineEdit, TextEdit, ComboBox, PrimaryPushButton,
                            PushButton, FluentIcon as FIF, BodyLabel, Pivot, CheckBox)
from app.utils.logger import log
import os


class FolderImportWidget(QWidget):
    """文件夹导入标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_path = ""
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # 说明文字
        desc_label = BodyLabel("从文件夹中批量导入图片，系统将为每张图片创建一个任务")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(desc_label)

        # 文件夹选择
        folder_layout = QHBoxLayout()
        folder_label = BodyLabel("选择文件夹:", self)
        folder_label.setFixedWidth(80)
        folder_layout.addWidget(folder_label)

        self.folder_edit = LineEdit(self)
        self.folder_edit.setPlaceholderText("点击右侧按钮选择文件夹...")
        self.folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.folder_edit)

        self.select_folder_btn = PushButton(FIF.FOLDER, "浏览", self)
        self.select_folder_btn.clicked.connect(self.onSelectFolder)
        folder_layout.addWidget(self.select_folder_btn)

        layout.addLayout(folder_layout)

        # 设置区域（一行放更多内容）
        settings_layout = QHBoxLayout()

        model_label = BodyLabel("模型:", self)
        settings_layout.addWidget(model_label)

        self.model_combo = ComboBox(self)
        self.model_combo.addItems(['图片 2.0', '图片 2.0 Pro', '图片 2.1', '图片 3.0', '图片 3.1', '图片 4.0'])
        self.model_combo.setCurrentText('图片 4.0')
        self.model_combo.setFixedWidth(140)
        settings_layout.addWidget(self.model_combo)

        settings_layout.addSpacing(15)

        ratio_label = BodyLabel("比例:", self)
        settings_layout.addWidget(ratio_label)

        self.ratio_combo = ComboBox(self)
        self.ratio_combo.addItems(['1:1', '16:9', '9:16', '4:3', '3:4'])
        self.ratio_combo.setCurrentText('1:1')
        self.ratio_combo.setFixedWidth(100)
        settings_layout.addWidget(self.ratio_combo)

        settings_layout.addSpacing(15)

        resolution_label = BodyLabel("分辨率:", self)
        settings_layout.addWidget(resolution_label)

        self.resolution_combo = ComboBox(self)
        self.resolution_combo.addItems(['高清 2K', '超清 4K'])
        self.resolution_combo.setCurrentText('高清 2K')
        self.resolution_combo.setFixedWidth(100)
        settings_layout.addWidget(self.resolution_combo)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # 默认提示词
        prompt_label = BodyLabel("默认提示词（可选）:", self)
        layout.addWidget(prompt_label)

        self.prompt_edit = TextEdit(self)
        self.prompt_edit.setPlaceholderText("为所有图片设置默认提示词...")
        self.prompt_edit.setFixedHeight(60)
        layout.addWidget(self.prompt_edit)

        # 预览区域
        self.preview_label = BodyLabel("尚未选择文件夹", self)
        self.preview_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); padding: 5px;")
        layout.addWidget(self.preview_label)

        layout.addStretch()

    def onSelectFolder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹", "")
        if folder:
            self.folder_path = folder
            self.folder_edit.setText(folder)

            # 统计图片数量
            image_files = self.get_image_files()
            if image_files:
                self.preview_label.setText(f"找到 {len(image_files)} 张图片")
                self.preview_label.setStyleSheet("color: rgba(0, 255, 0, 0.8);")
            else:
                self.preview_label.setText("文件夹中没有找到图片文件")
                self.preview_label.setStyleSheet("color: rgba(255, 0, 0, 0.8);")

    def get_image_files(self):
        """获取文件夹中的图片文件"""
        if not self.folder_path or not os.path.exists(self.folder_path):
            return []

        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
        image_files = []

        for file in os.listdir(self.folder_path):
            if file.lower().endswith(image_extensions):
                image_files.append(os.path.join(self.folder_path, file))

        return image_files

    def get_tasks_data(self):
        """获取任务数据列表"""
        image_files = self.get_image_files()
        if not image_files:
            return []

        tasks = []
        default_prompt = self.prompt_edit.toPlainText().strip()

        for image_path in image_files:
            task_data = {
                'prompt': default_prompt or os.path.splitext(os.path.basename(image_path))[0],
                'image_model': self.model_combo.currentText(),
                'input_image_paths': [image_path],
                'aspect_ratio': self.ratio_combo.currentText(),
                'resolution': self.resolution_combo.currentText(),
            }
            tasks.append(task_data)

        return tasks


class TableImportWidget(QWidget):
    """表格导入标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.excel_path = ""
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # 说明文字和下载模板按钮在同一行
        top_layout = QHBoxLayout()
        desc_label = BodyLabel("从Excel表格导入批量任务（支持.xlsx/.xls格式）")
        desc_label.setStyleSheet("font-size: 12px;")
        top_layout.addWidget(desc_label)
        top_layout.addStretch()

        self.download_template_btn = PushButton(FIF.DOWNLOAD, "下载模板", self)
        self.download_template_btn.clicked.connect(self.onDownloadTemplate)
        top_layout.addWidget(self.download_template_btn)
        layout.addLayout(top_layout)

        # 文件选择
        file_layout = QHBoxLayout()
        file_label = BodyLabel("选择文件:", self)
        file_label.setFixedWidth(80)
        file_layout.addWidget(file_label)

        self.file_edit = LineEdit(self)
        self.file_edit.setPlaceholderText("点击右侧按钮选择Excel文件...")
        self.file_edit.setReadOnly(True)
        file_layout.addWidget(self.file_edit)

        self.select_file_btn = PushButton(FIF.DOCUMENT, "浏览", self)
        self.select_file_btn.clicked.connect(self.onSelectFile)
        file_layout.addWidget(self.select_file_btn)

        layout.addLayout(file_layout)

        # 预览表格
        preview_label = BodyLabel("预览数据:", self)
        layout.addWidget(preview_label)

        self.preview_table = QTableWidget(self)
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(['提示词', '图片模型', '参考图片路径', '比例', '分辨率'])

        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)

        self.preview_table.setColumnWidth(3, 80)
        self.preview_table.setColumnWidth(4, 100)

        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        layout.addWidget(self.preview_table)

        # 状态提示
        self.status_label = BodyLabel("请选择Excel文件", self)
        self.status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); padding: 5px;")
        layout.addWidget(self.status_label)

    def onSelectFile(self):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel Files (*.xlsx *.xls)"
        )

        if file_path:
            self.excel_path = file_path
            self.file_edit.setText(file_path)
            self.load_excel_data()

    def load_excel_data(self):
        """加载Excel数据"""
        try:
            import pandas as pd

            df = pd.read_excel(self.excel_path)

            # 检查必需的列
            required_columns = ['提示词', '图片模型', '比例', '分辨率']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.status_label.setText(f"缺少必需列: {', '.join(missing_columns)}")
                self.status_label.setStyleSheet("color: rgba(255, 0, 0, 0.8);")
                return

            # 清空表格
            self.preview_table.setRowCount(0)

            # 填充数据
            for index, row in df.iterrows():
                row_position = self.preview_table.rowCount()
                self.preview_table.insertRow(row_position)

                self.preview_table.setItem(row_position, 0, QTableWidgetItem(str(row.get('提示词', ''))))
                self.preview_table.setItem(row_position, 1, QTableWidgetItem(str(row.get('图片模型', ''))))
                self.preview_table.setItem(row_position, 2, QTableWidgetItem(str(row.get('参考图片路径', ''))))
                self.preview_table.setItem(row_position, 3, QTableWidgetItem(str(row.get('比例', ''))))
                self.preview_table.setItem(row_position, 4, QTableWidgetItem(str(row.get('分辨率', ''))))

            self.status_label.setText(f"成功加载 {len(df)} 条记录")
            self.status_label.setStyleSheet("color: rgba(0, 255, 0, 0.8);")

        except Exception as e:
            log.error(f"加载Excel失败: {e}")
            self.status_label.setText(f"加载失败: {str(e)}")
            self.status_label.setStyleSheet("color: rgba(255, 0, 0, 0.8);")

    def onDownloadTemplate(self):
        """下载模板文件"""
        try:
            import pandas as pd

            # 创建模板数据
            template_data = {
                '提示词': ['示例提示词1', '示例提示词2'],
                '图片模型': ['图片 4.0', '图片 4.0'],
                '参考图片路径': ['', ''],
                '比例': ['1:1', '16:9'],
                '分辨率': ['高清 2K', '超清 4K']
            }

            df = pd.DataFrame(template_data)

            # 保存文件
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存模板文件",
                "批量任务模板.xlsx",
                "Excel Files (*.xlsx)"
            )

            if file_path:
                df.to_excel(file_path, index=False)
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.success(
                    title="下载成功",
                    content="模板文件已保存",
                    parent=self.window(),
                    position=InfoBarPosition.TOP
                )

        except Exception as e:
            log.error(f"下载模板失败: {e}")
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title="下载失败",
                content=str(e),
                parent=self.window(),
                position=InfoBarPosition.TOP
            )

    def get_tasks_data(self):
        """获取任务数据列表"""
        if not self.excel_path:
            return []

        try:
            import pandas as pd
            df = pd.read_excel(self.excel_path)

            tasks = []
            for _, row in df.iterrows():
                # 处理参考图片路径
                image_paths_str = str(row.get('参考图片路径', '')).strip()
                input_image_paths = []
                if image_paths_str and image_paths_str != 'nan':
                    # 支持多个路径，用分号或逗号分隔
                    paths = image_paths_str.replace('；', ';').replace('，', ',')
                    if ';' in paths:
                        input_image_paths = [p.strip() for p in paths.split(';') if p.strip()]
                    elif ',' in paths:
                        input_image_paths = [p.strip() for p in paths.split(',') if p.strip()]
                    else:
                        input_image_paths = [paths]

                task_data = {
                    'prompt': str(row.get('提示词', '')),
                    'image_model': str(row.get('图片模型', '图片 4.0')),
                    'input_image_paths': input_image_paths,
                    'aspect_ratio': str(row.get('比例', '1:1')),
                    'resolution': str(row.get('分辨率', '高清 2K')),
                }
                tasks.append(task_data)

            return tasks

        except Exception as e:
            log.error(f"解析Excel数据失败: {e}")
            return []


class TextPromptImportWidget(QWidget):
    """文本提示词导入标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # 说明文字
        desc_label = BodyLabel("每行一个提示词，系统将为每行创建一个任务（空行将被忽略）")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(desc_label)

        # 设置区域（一行放所有设置）
        settings_layout = QHBoxLayout()

        model_label = BodyLabel("模型:", self)
        settings_layout.addWidget(model_label)

        self.model_combo = ComboBox(self)
        self.model_combo.addItems(['图片 2.0', '图片 2.0 Pro', '图片 2.1', '图片 3.0', '图片 3.1', '图片 4.0'])
        self.model_combo.setCurrentText('图片 4.0')
        self.model_combo.setFixedWidth(140)
        settings_layout.addWidget(self.model_combo)

        settings_layout.addSpacing(15)

        ratio_label = BodyLabel("比例:", self)
        settings_layout.addWidget(ratio_label)

        self.ratio_combo = ComboBox(self)
        self.ratio_combo.addItems(['1:1', '16:9', '9:16', '4:3', '3:4'])
        self.ratio_combo.setCurrentText('1:1')
        self.ratio_combo.setFixedWidth(100)
        settings_layout.addWidget(self.ratio_combo)

        settings_layout.addSpacing(15)

        resolution_label = BodyLabel("分辨率:", self)
        settings_layout.addWidget(resolution_label)

        self.resolution_combo = ComboBox(self)
        self.resolution_combo.addItems(['高清 2K', '超清 4K'])
        self.resolution_combo.setCurrentText('高清 2K')
        self.resolution_combo.setFixedWidth(100)
        settings_layout.addWidget(self.resolution_combo)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # 提示词输入区域
        prompt_label = BodyLabel("提示词列表（每行一个）:", self)
        layout.addWidget(prompt_label)

        self.prompts_edit = TextEdit(self)
        self.prompts_edit.setPlaceholderText(
            "每行输入一个提示词，例如：\n"
            "一只可爱的小猫在阳光下玩耍\n"
            "城市夜景，霓虹灯闪烁\n"
            "夕阳下的海边，浪花拍打着沙滩\n"
            "..."
        )
        layout.addWidget(self.prompts_edit)

        # 统计信息
        self.count_label = BodyLabel("当前任务数：0", self)
        self.count_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); padding: 5px;")
        layout.addWidget(self.count_label)

        # 连接文本变化信号
        self.prompts_edit.textChanged.connect(self.update_count)

    def update_count(self):
        """更新任务数量统计"""
        text = self.prompts_edit.toPlainText()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        count = len(lines)
        self.count_label.setText(f"当前任务数：{count}")

        if count > 0:
            self.count_label.setStyleSheet("color: rgba(0, 255, 0, 0.8); padding: 5px;")
        else:
            self.count_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); padding: 5px;")

    def get_tasks_data(self):
        """获取任务数据列表"""
        text = self.prompts_edit.toPlainText()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if not lines:
            return []

        tasks = []
        for prompt in lines:
            task_data = {
                'prompt': prompt,
                'image_model': self.model_combo.currentText(),
                'input_image_paths': [],
                'aspect_ratio': self.ratio_combo.currentText(),
                'resolution': self.resolution_combo.currentText(),
            }
            tasks.append(task_data)

        return tasks


class SequentialAddWidget(QWidget):
    """依次添加标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks_list = []
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # 说明文字
        desc_label = BodyLabel("逐个添加多个任务，填写完成后点击'添加到列表'，可重复添加")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(desc_label)

        # 任务输入区域
        input_container = QWidget(self)
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(10, 8, 10, 8)
        input_layout.setSpacing(8)

        # 第一行：模型、比例、分辨率、按钮
        top_settings_layout = QHBoxLayout()

        model_label = BodyLabel("模型:", input_container)
        top_settings_layout.addWidget(model_label)

        self.model_combo = ComboBox(input_container)
        self.model_combo.addItems(['图片 2.0', '图片 2.0 Pro', '图片 2.1', '图片 3.0', '图片 3.1', '图片 4.0'])
        self.model_combo.setCurrentText('图片 4.0')
        self.model_combo.setFixedWidth(130)
        top_settings_layout.addWidget(self.model_combo)

        top_settings_layout.addSpacing(10)

        ratio_label = BodyLabel("比例:", input_container)
        top_settings_layout.addWidget(ratio_label)

        self.ratio_combo = ComboBox(input_container)
        self.ratio_combo.addItems(['1:1', '16:9', '9:16', '4:3', '3:4'])
        self.ratio_combo.setCurrentText('1:1')
        self.ratio_combo.setFixedWidth(90)
        top_settings_layout.addWidget(self.ratio_combo)

        top_settings_layout.addSpacing(10)

        resolution_label = BodyLabel("分辨率:", input_container)
        top_settings_layout.addWidget(resolution_label)

        self.resolution_combo = ComboBox(input_container)
        self.resolution_combo.addItems(['高清 2K', '超清 4K'])
        self.resolution_combo.setCurrentText('高清 2K')
        self.resolution_combo.setFixedWidth(90)
        top_settings_layout.addWidget(self.resolution_combo)

        top_settings_layout.addStretch()

        self.add_to_list_btn = PrimaryPushButton(FIF.ADD, "添加到列表", input_container)
        self.add_to_list_btn.clicked.connect(self.onAddToList)
        top_settings_layout.addWidget(self.add_to_list_btn)

        input_layout.addLayout(top_settings_layout)

        # 提示词
        prompt_label = BodyLabel("提示词:", input_container)
        input_layout.addWidget(prompt_label)

        self.prompt_edit = TextEdit(input_container)
        self.prompt_edit.setPlaceholderText("请输入图片生成的提示词描述...")
        self.prompt_edit.setFixedHeight(60)
        input_layout.addWidget(self.prompt_edit)

        input_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)

        layout.addWidget(input_container)

        # 已添加的任务列表
        list_header_layout = QHBoxLayout()
        list_label = BodyLabel("已添加的任务:", self)
        list_header_layout.addWidget(list_label)
        list_header_layout.addStretch()

        self.clear_list_btn = PushButton(FIF.DELETE, "清空列表", self)
        self.clear_list_btn.clicked.connect(self.onClearList)
        list_header_layout.addWidget(self.clear_list_btn)
        layout.addLayout(list_header_layout)

        self.tasks_table = QTableWidget(self)
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(['提示词', '模型', '比例', '分辨率', '操作'])

        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)

        self.tasks_table.setColumnWidth(2, 80)
        self.tasks_table.setColumnWidth(3, 100)
        self.tasks_table.setColumnWidth(4, 80)

        self.tasks_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        layout.addWidget(self.tasks_table)

    def onAddToList(self):
        """添加到列表"""
        prompt = self.prompt_edit.toPlainText().strip()

        if not prompt:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning(
                title="提示",
                content="请输入提示词",
                parent=self.window(),
                position=InfoBarPosition.TOP
            )
            return

        task_data = {
            'prompt': prompt,
            'image_model': self.model_combo.currentText(),
            'input_image_paths': [],
            'aspect_ratio': self.ratio_combo.currentText(),
            'resolution': self.resolution_combo.currentText(),
        }

        self.tasks_list.append(task_data)
        self.update_tasks_table()

        # 清空输入
        self.prompt_edit.clear()

        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.success(
            title="添加成功",
            content=f"已添加到列表，当前共 {len(self.tasks_list)} 个任务",
            parent=self.window(),
            duration=1500,
            position=InfoBarPosition.TOP
        )

    def update_tasks_table(self):
        """更新任务表格"""
        self.tasks_table.setRowCount(0)

        for index, task in enumerate(self.tasks_list):
            row_position = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row_position)

            # 提示词（截断显示）
            prompt_text = task['prompt']
            if len(prompt_text) > 30:
                prompt_text = prompt_text[:30] + "..."

            self.tasks_table.setItem(row_position, 0, QTableWidgetItem(prompt_text))
            self.tasks_table.setItem(row_position, 1, QTableWidgetItem(task['image_model']))
            self.tasks_table.setItem(row_position, 2, QTableWidgetItem(task['aspect_ratio']))
            self.tasks_table.setItem(row_position, 3, QTableWidgetItem(task['resolution']))

            # 删除按钮
            delete_btn = PushButton(FIF.DELETE, "", self.tasks_table)
            delete_btn.setFixedSize(60, 30)
            delete_btn.clicked.connect(lambda checked, idx=index: self.onDeleteTask(idx))
            self.tasks_table.setCellWidget(row_position, 4, delete_btn)

    def onDeleteTask(self, index):
        """删除任务"""
        if 0 <= index < len(self.tasks_list):
            self.tasks_list.pop(index)
            self.update_tasks_table()

    def onClearList(self):
        """清空列表"""
        self.tasks_list = []
        self.update_tasks_table()

        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.info(
            title="提示",
            content="列表已清空",
            parent=self.window(),
            position=InfoBarPosition.TOP
        )

    def get_tasks_data(self):
        """获取任务数据列表"""
        return self.tasks_list


class BatchAddImageTaskDialog(Dialog):
    """批量添加图片任务对话框"""

    tasks_added = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__("", "", parent)

        # 动态计算窗口大小
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.desktop().screenGeometry()

        # 宽度设置为较宽，高度不超过屏幕的80%
        dialog_width = min(1000, int(screen.width() * 0.9))
        dialog_height = min(550, int(screen.height() * 0.8))

        self.setFixedSize(dialog_width, dialog_height)

        # 隐藏标题区域
        self.titleLabel.setVisible(False)

        self.initUI()

    def initUI(self):
        """初始化UI"""
        # 创建内容widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)

        # 标题
        title_label = BodyLabel("批量添加任务", content)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        # 创建Pivot（标签栏）
        self.pivot = Pivot(content)
        self.pivot.setFixedHeight(36)

        # 创建QStackedWidget
        self.stackedWidget = QStackedWidget(content)

        # 创建四个标签页
        self.text_prompt_widget = TextPromptImportWidget(self.stackedWidget)
        self.folder_widget = FolderImportWidget(self.stackedWidget)
        self.table_widget = TableImportWidget(self.stackedWidget)
        self.sequential_widget = SequentialAddWidget(self.stackedWidget)

        # 添加标签页到QStackedWidget
        self.stackedWidget.addWidget(self.text_prompt_widget)
        self.stackedWidget.addWidget(self.folder_widget)
        self.stackedWidget.addWidget(self.table_widget)
        self.stackedWidget.addWidget(self.sequential_widget)

        # 添加标签到Pivot
        self.pivot.addItem(
            routeKey='text_prompt',
            text='文本导入',
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.text_prompt_widget)
        )
        self.pivot.addItem(
            routeKey='folder',
            text='文件夹导入',
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.folder_widget)
        )
        self.pivot.addItem(
            routeKey='table',
            text='表格导入',
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.table_widget)
        )
        self.pivot.addItem(
            routeKey='sequential',
            text='依次添加',
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.sequential_widget)
        )

        # 设置默认选中第一个（文本导入）
        self.pivot.setCurrentItem('text_prompt')
        self.stackedWidget.setCurrentWidget(self.text_prompt_widget)

        layout.addWidget(self.pivot)
        layout.addWidget(self.stackedWidget)

        # 设置内容
        self.textLayout.addWidget(content)

        # 按钮
        self.yesButton.setText("批量添加")
        self.cancelButton.setText("取消")

        self.yesButton.clicked.connect(self.on_batch_add)
        self.cancelButton.clicked.connect(self.reject)

    def on_batch_add(self):
        """批量添加任务"""
        # 获取当前标签页的任务数据
        current_widget = self.stackedWidget.currentWidget()
        tasks_data = current_widget.get_tasks_data()

        if not tasks_data:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning(
                title="提示",
                content="没有可添加的任务",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return

        log.info(f"批量创建 {len(tasks_data)} 个图片任务")
        self.tasks_added.emit(tasks_data)
        self.accept()
