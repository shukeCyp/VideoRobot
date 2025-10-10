from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class HomeInterface(QWidget):
    """首页界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)