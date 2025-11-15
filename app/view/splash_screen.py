# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QGraphicsDropShadowEffect
from qfluentwidgets import ProgressBar, BodyLabel, TitleLabel, CaptionLabel
import os


class SplashScreen(QWidget):
    """启动界面"""

    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.progress = 0
        self.initUI()

    def initUI(self):
        """初始化UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置窗口大小
        self.setFixedSize(550, 380)

        # 主容器
        container = QWidget(self)
        container.setObjectName("container")
        container.setGeometry(0, 0, 550, 380)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)

        # 主布局
        layout = QVBoxLayout(container)
        layout.setContentsMargins(50, 45, 50, 45)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        # 应用图标
        icon_label = QLabel(container)
        icon_label.setAlignment(Qt.AlignCenter)

        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        icon_path = os.path.join(project_root, "icon.png")

        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)

        layout.addWidget(icon_label)
        layout.addSpacing(5)

        # 应用标题
        title_label = TitleLabel("视频机器人", container)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: rgba(255, 255, 255, 0.95);
        """)
        layout.addWidget(title_label)

        # 副标题/版本号
        version_label = CaptionLabel("AI Video Generation Platform", container)
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 13px;
        """)
        layout.addWidget(version_label)

        layout.addSpacing(10)

        # 状态标签
        self.status_label = BodyLabel("正在初始化...", container)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.85);
            font-size: 14px;
        """)
        layout.addWidget(self.status_label)

        layout.addSpacing(5)

        # 进度条
        self.progress_bar = ProgressBar(container)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        layout.addSpacing(10)

        # 版权信息
        copyright_label = CaptionLabel("© 2025 Video Robot", container)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.5);
            font-size: 11px;
        """)
        layout.addWidget(copyright_label)

        # 设置样式
        container.setStyleSheet("""
            #container {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(45, 45, 48, 240),
                    stop:1 rgba(32, 32, 35, 240)
                );
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)

        # 居中显示
        self.center()

    def center(self):
        """窗口居中"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def update_progress(self, value, message):
        """更新进度"""
        self.progress = value
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

        if value >= 100:
            self.status_label.setText("启动完成！")
            QTimer.singleShot(300, self.close_splash)

    def close_splash(self):
        """关闭启动界面"""
        self.finished.emit()
        self.close()
