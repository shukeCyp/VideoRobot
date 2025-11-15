# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class DigitalHumanIntlView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("digitalHumanIntl")
        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("🛠️ 数字人（国际版）施工中...", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: rgba(255,255,255,0.8);")
        layout.addWidget(label)

