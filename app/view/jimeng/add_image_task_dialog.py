# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QLabel
from qfluentwidgets import (Dialog, LineEdit, TextEdit, ComboBox, PrimaryPushButton,
                            PushButton, FluentIcon as FIF, BodyLabel)
from app.utils.logger import log


class MultiImageDropWidget(QWidget):
    """支持拖拽多张图片的组件"""

    images_changed = pyqtSignal(list)

    def __init__(self, parent=None, max_images=6):
        super().__init__(parent)
        self.image_paths = []
        self.max_images = max_images
        self.is_enabled = True
        self.setAcceptDrops(True)
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 拖拽区域
        self.drop_label = QLabel(self)
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setFixedHeight(120)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        if self.max_images == 1:
            self.drop_label.setText("拖拽图片到这里")
        else:
            self.drop_label.setText(f"拖拽图片到这里（最多{self.max_images}张）")
        layout.addWidget(self.drop_label)

        # 图片预览区域（网格布局显示缩略图）
        self.preview_widget = QWidget(self)
        from PyQt5.QtWidgets import QGridLayout
        self.preview_layout = QGridLayout(self.preview_widget)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSpacing(8)
        self.preview_widget.setVisible(False)
        layout.addWidget(self.preview_widget)

        # 清除按钮
        self.clear_btn = PushButton(FIF.DELETE, "清除", self)
        self.clear_btn.clicked.connect(self.clear_all_images)
        self.clear_btn.setVisible(False)
        layout.addWidget(self.clear_btn)

    def dragEnterEvent(self, event):
        """拖拽进入"""
        if not self.is_enabled:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """拖拽放下"""
        if not self.is_enabled:
            event.ignore()
            return
        urls = event.mimeData().urls()
        for url in urls:
            if len(self.image_paths) >= self.max_images:
                from qfluentwidgets import InfoBar, InfoBarPosition
                InfoBar.warning(
                    title="提示",
                    content=f"最多只能添加{self.max_images}张图片",
                    parent=self.window(),
                    position=InfoBarPosition.TOP
                )
                break

            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                if file_path not in self.image_paths:
                    self.image_paths.append(file_path)

        self.update_preview()
        self.images_changed.emit(self.image_paths)

    def update_preview(self):
        """更新预览"""
        # 清空现有预览
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not self.image_paths:
            self.preview_widget.setVisible(False)
            self.clear_btn.setVisible(False)
            if self.max_images == 1:
                self.drop_label.setText("拖拽图片到这里")
            else:
                self.drop_label.setText(f"拖拽图片到这里（最多{self.max_images}张）")
            return

        self.preview_widget.setVisible(True)
        self.clear_btn.setVisible(True)
        if self.max_images == 1:
            self.drop_label.setText("已添加图片")
        else:
            self.drop_label.setText(f"已添加 {len(self.image_paths)}/{self.max_images} 张图片")

        # 显示缩略图（6列布局）
        for idx, path in enumerate(self.image_paths):
            row = idx // 6
            col = idx % 6

            # 创建图片容器
            img_container = QWidget()
            img_layout = QVBoxLayout(img_container)
            img_layout.setContentsMargins(0, 0, 0, 0)
            img_layout.setSpacing(2)

            # 图片缩略图
            img_label = QLabel()
            try:
                pixmap = QPixmap(path)
                scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label.setPixmap(scaled_pixmap)
            except:
                img_label.setText("加载失败")
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setFixedSize(80, 80)
            img_label.setStyleSheet("border: 1px solid #666; border-radius: 3px;")
            img_layout.addWidget(img_label)

            # 删除按钮
            from functools import partial
            del_btn = PushButton(FIF.CLOSE, "", img_container)
            del_btn.setFixedSize(80, 25)
            del_btn.clicked.connect(partial(self.remove_image, idx))
            img_layout.addWidget(del_btn)

            self.preview_layout.addWidget(img_container, row, col)

    def remove_image(self, index):
        """删除指定图片"""
        if 0 <= index < len(self.image_paths):
            self.image_paths.pop(index)
            self.update_preview()
            self.images_changed.emit(self.image_paths)

    def clear_all_images(self):
        """清除所有图片"""
        self.image_paths = []
        self.update_preview()
        self.images_changed.emit(self.image_paths)

    def get_image_paths(self):
        """获取所有图片路径"""
        return self.image_paths

    def set_max_images(self, max_images):
        """设置最大图片数量"""
        self.max_images = max_images
        # 如果当前图片数超过新的最大值，移除多余的图片
        if len(self.image_paths) > max_images:
            self.image_paths = self.image_paths[:max_images]
            self.update_preview()
            self.images_changed.emit(self.image_paths)
        else:
            # 更新提示文字
            self.update_preview()

    def set_enabled(self, enabled):
        """设置启用/禁用状态"""
        self.is_enabled = enabled

        if enabled:
            # 启用状态
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #666;
                    border-radius: 5px;
                    background-color: rgba(255, 255, 255, 0.05);
                }
            """)
            self.setAcceptDrops(True)
            # 恢复提示文字
            if not self.image_paths:
                if self.max_images == 1:
                    self.drop_label.setText("拖拽图片到这里")
                else:
                    self.drop_label.setText(f"拖拽图片到这里（最多{self.max_images}张）")
        else:
            # 禁用状态
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #444;
                    border-radius: 5px;
                    background-color: rgba(255, 255, 255, 0.02);
                    color: #666;
                }
            """)
            self.drop_label.setText("该模型不可上传参考图片")
            self.setAcceptDrops(False)
            # 清空已有图片
            if self.image_paths:
                self.clear_all_images()


class AddImageTaskDialog(Dialog):
    """添加图片任务对话框"""

    task_added = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__("", "", parent)
        self.setFixedWidth(700)

        # 隐藏标题区域
        self.titleLabel.setVisible(False)

        self.initUI()

    def initUI(self):
        """初始化UI"""
        # 创建内容widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 5, 30, 10)
        layout.setSpacing(15)

        # 图片模型选择
        model_layout = QHBoxLayout()
        model_label = BodyLabel("图片模型 *", content)
        model_layout.addWidget(model_label)

        self.model_combo = ComboBox(content)
        self.model_combo.addItems(['图片 2.0', '图片 2.0 Pro', '图片 2.1', '图片 3.0', '图片 3.1', '图片 4.0'])
        self.model_combo.setCurrentText('图片 4.0')
        self.model_combo.setFixedWidth(180)
        self.model_combo.currentTextChanged.connect(self.onModelChanged)
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

        # 图片（可选）- 只有图片4.0支持
        self.image_label = BodyLabel("参考图片（可选）", content)
        self.image_widget = MultiImageDropWidget(content)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_widget)

        # 初始化图片区域显示
        self.onModelChanged(self.model_combo.currentText())

        # 比例和分辨率选择（同一行）
        settings_layout = QHBoxLayout()

        # 比例选择
        ratio_label = BodyLabel("分辨率比例 *", content)
        settings_layout.addWidget(ratio_label)

        self.ratio_combo = ComboBox(content)
        self.ratio_combo.addItems(['1:1', '16:9', '9:16', '4:3', '3:4'])
        self.ratio_combo.setCurrentText('1:1')
        self.ratio_combo.setFixedWidth(120)
        settings_layout.addWidget(self.ratio_combo)

        settings_layout.addSpacing(30)

        # 分辨率选择
        resolution_label = BodyLabel("分辨率 *", content)
        settings_layout.addWidget(resolution_label)

        self.resolution_combo = ComboBox(content)
        self.resolution_combo.addItems(['高清 2K', '超清 4K'])
        self.resolution_combo.setCurrentText('高清 2K')
        self.resolution_combo.setFixedWidth(120)
        settings_layout.addWidget(self.resolution_combo)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # 设置内容
        self.textLayout.addWidget(content)

        # 按钮
        self.yesButton.setText("添加")
        self.cancelButton.setText("取消")

        self.yesButton.clicked.connect(self.on_add_task)
        self.cancelButton.clicked.connect(self.reject)

    def onModelChanged(self, model_name):
        """模型切换时更新图片输入区域"""
        # 清空已有图片
        if self.image_widget.get_image_paths():
            self.image_widget.clear_all_images()

        if model_name == '图片 4.0':
            # 图片 4.0 支持最多6张参考图片
            self.image_widget.set_max_images(6)
            self.image_widget.set_enabled(True)
        elif model_name in ['图片 2.0 Pro', '图片 3.0']:
            # 图片 2.0 Pro 和 图片 3.0 支持1张参考图片
            self.image_widget.set_max_images(1)
            self.image_widget.set_enabled(True)
        else:
            # 其他模型不支持图生图
            self.image_widget.set_enabled(False)

    def on_add_task(self):
        """添加任务"""
        prompt = self.prompt_edit.toPlainText().strip()

        if not prompt:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning(
                title="提示",
                content="请输入提示词",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return

        # 收集所有有效的图片路径
        image_paths = self.image_widget.get_image_paths()

        # 收集任务数据
        task_data = {
            'prompt': prompt,
            'image_model': self.model_combo.currentText(),
            'input_image_paths': image_paths,
            'aspect_ratio': self.ratio_combo.currentText(),
            'resolution': self.resolution_combo.currentText(),
        }

        log.info(f"创建图片任务: {task_data}")
        self.task_added.emit(task_data)
        self.accept()
