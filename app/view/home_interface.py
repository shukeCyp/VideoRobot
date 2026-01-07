from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QColor
import os


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

        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # 创建二维码容器
        qrcode_container = QWidget()
        qrcode_layout = QHBoxLayout(qrcode_container)
        qrcode_layout.setContentsMargins(0, 0, 0, 0)
        qrcode_layout.setSpacing(40)

        # 群二维码
        group_qrcode_path = os.path.join(project_root, "group_qrcode.png")
        if os.path.exists(group_qrcode_path):
            group_label = QLabel()
            group_label.setAlignment(Qt.AlignCenter)
            group_pixmap = QPixmap(group_qrcode_path)
            # 缩放到合适大小 (200x200)
            scaled_pixmap = group_pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            group_label.setPixmap(scaled_pixmap)

            # 创建群二维码容器
            group_container = QWidget()
            group_container_layout = QVBoxLayout(group_container)
            group_container_layout.setContentsMargins(0, 0, 0, 0)
            group_label_text = QLabel("群二维码")
            group_label_text.setStyleSheet("color: white; font-weight: bold;")
            group_label_text.setAlignment(Qt.AlignCenter)
            group_container_layout.addWidget(group_label_text, 0, Qt.AlignCenter)
            group_container_layout.addWidget(group_label, 0, Qt.AlignCenter)
            group_container_layout.addStretch()

            qrcode_layout.addWidget(group_container)

        # 作者二维码
        vx_qrcode_path = os.path.join(project_root, "vx_qrcode.png")
        if os.path.exists(vx_qrcode_path):
            vx_label = QLabel()
            vx_label.setAlignment(Qt.AlignCenter)
            vx_pixmap = QPixmap(vx_qrcode_path)
            # 缩放到合适大小 (200x200)
            scaled_pixmap = vx_pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            vx_label.setPixmap(scaled_pixmap)

            # 创建微信二维码容器
            vx_container = QWidget()
            vx_container_layout = QVBoxLayout(vx_container)
            vx_container_layout.setContentsMargins(0, 0, 0, 0)
            vx_label_text = QLabel("作者微信")
            vx_label_text.setStyleSheet("color: white; font-weight: bold;")
            vx_label_text.setAlignment(Qt.AlignCenter)
            vx_container_layout.addWidget(vx_label_text, 0, Qt.AlignCenter)
            vx_container_layout.addWidget(vx_label, 0, Qt.AlignCenter)
            vx_container_layout.addStretch()

            qrcode_layout.addWidget(vx_container)

        qrcode_layout.addStretch()
        layout.addWidget(qrcode_container)
        layout.addStretch()