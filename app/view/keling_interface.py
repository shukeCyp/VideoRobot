# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class KeLingInterface(QWidget):
    """可灵界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("KeLingInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("🚧 可灵功能开发中... 🚧\n\n"
                      "程序员正在疯狂敲代码中 ⌨️💻\n"
                      "请耐心等待，或者给开发者买杯奶茶催更 ☕😊", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #FF6B6B; font-weight: bold;")
        layout.addWidget(label)