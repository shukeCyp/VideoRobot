# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class HaiLuoInterface(QWidget):
    """海螺界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HaiLuoInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("🐚 海螺功能孵化中... 🐚\n\n"
                      "程序员掉了好多头发才写到这里 👨‍💻😭\n"
                      "再等等，马上就好！ ⏳✨", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #95E1D3; font-weight: bold;")
        layout.addWidget(label)