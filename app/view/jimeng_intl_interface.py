# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from qfluentwidgets import Pivot


class JiMengIntlInterface(QWidget):
    """即梦国际版界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("jimengIntlInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标签导航
        self.pivot = Pivot(self)
        layout.addWidget(self.pivot, 0, Qt.AlignLeft)

        # 内容容器
        self.stackedWidget = QStackedWidget(self)
        layout.addWidget(self.stackedWidget)

        # 子页面
        from app.view.jimeng_intl.image_gen_view import ImageGenIntlView
        from app.view.jimeng_intl.video_gen_view import VideoGenIntlView
        from app.view.jimeng_intl.account_manage_view import AccountManageIntlView

        self.imageGenView = ImageGenIntlView()
        self.videoGenView = VideoGenIntlView()
        self.accountManageView = AccountManageIntlView()

        # 添加标签页
        self.addSubInterface(self.imageGenView, "imageGenIntl", "图片生成")
        self.addSubInterface(self.videoGenView, "videoGenIntl", "视频生成")
        self.addSubInterface(self.accountManageView, "accountManageIntl", "账号管理")

        # 默认选中
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.imageGenView)
        self.pivot.setCurrentItem(self.imageGenView.objectName())

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        """添加子界面"""
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        """标签页切换事件"""
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())

