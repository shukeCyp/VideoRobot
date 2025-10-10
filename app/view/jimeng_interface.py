from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from qfluentwidgets import Pivot


class JiMengInterface(QWidget):
    """即梦平台界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("jimengInterface")
        self.initUI()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建Pivot（标签页导航）
        self.pivot = Pivot(self)
        layout.addWidget(self.pivot, 0, Qt.AlignLeft)

        # 创建StackedWidget（内容容器）
        self.stackedWidget = QStackedWidget(self)
        layout.addWidget(self.stackedWidget)

        # 创建各个子页面
        from app.view.jimeng.image_gen_view import ImageGenView
        self.imageGenView = ImageGenView()

        self.videoGenView = QWidget()
        self.videoGenLayout = QVBoxLayout(self.videoGenView)
        self.videoGenLayout.setContentsMargins(40, 20, 40, 40)

        self.digitalHumanView = QWidget()
        self.digitalHumanLayout = QVBoxLayout(self.digitalHumanView)
        self.digitalHumanLayout.setContentsMargins(40, 20, 40, 40)

        # 账号管理页面
        from app.view.jimeng.account_manage_view import AccountManageView
        self.accountManageView = AccountManageView()
        self.accountManageLayout = self.accountManageView.layout()

        # 添加标签页
        self.addSubInterface(self.imageGenView, "imageGen", "图片生成")
        self.addSubInterface(self.videoGenView, "videoGen", "视频生成")
        self.addSubInterface(self.digitalHumanView, "digitalHuman", "数字人")
        self.addSubInterface(self.accountManageView, "accountManage", "账号管理")

        # 设置默认选中第一个标签页
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

        # 如果切换离开账号管理页面，通知其关闭浏览器
        if widget != self.accountManageView and hasattr(self.accountManageView, 'closeLoginWindow'):
            self.accountManageView.closeLoginWindow()