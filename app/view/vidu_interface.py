# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


class ViduInterface(QWidget):
    """Vidu界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ViduInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("⚠️ Vidu功能即将登场... ⚠️\n\n"
                      "开发者正在与BUG斗智斗勇 🐛⚔️\n"
                      "胜利在望，敬请期待！ 🎉", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #FFD93D; font-weight: bold;")
        layout.addWidget(label)