# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class RunwayInterface(QWidget):
    """Runway界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RunwayInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("✈️ Runway功能准备起飞... ✈️\n\n"
                      "代码正在跑道上加速中 🏃‍♂️💨\n"
                      "请系好安全带，马上就要上线啦！ 🚀", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #A8E6CF; font-weight: bold;")
        layout.addWidget(label)