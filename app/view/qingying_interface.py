# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class QingYingInterface(QWidget):
    """清影界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("QingYingInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("🛠️ 清影功能施工中... 🛠️\n\n"
                      "代码还在烤箱里烘焙呢 🍰⏰\n"
                      "别急别急，好饭不怕晚～ 😋", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #4ECDC4; font-weight: bold;")
        layout.addWidget(label)