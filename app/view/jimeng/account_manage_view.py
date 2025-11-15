# -*- coding: utf-8 -*-
import requests
from io import BytesIO
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QColor, QCursor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView, QLabel
from qfluentwidgets import (PrimaryPushButton, PushButton, TableWidget,
                            MessageBox, FluentIcon as FIF, InfoBar, InfoBarPosition,
                            RoundMenu, Action)
from app.models.jimeng_account import JimengAccount
from app.utils.logger import log


class AvatarLoader(QThread):
    """头像加载线程"""
    finished = pyqtSignal(int, QPixmap)

    def __init__(self, row, url):
        super().__init__()
        self.row = row
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.finished.emit(self.row, pixmap)
        except Exception as e:
            print(f"加载头像失败: {e}")


class AccountManageView(QWidget):
    """账号管理视图"""

    DEFAULT_AVATAR_URL = "https://p3-passport.byteacctimg.com/img/user-avatar/19365e835b806b06dc942489efb1340a~300x300.image"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.avatarLoaders = []  # 保存加载线程的引用
        self.loginWindowThread = None  # 保存登录窗口线程的引用
        self.initUI()

    def closeLoginWindow(self):
        """关闭登录窗口（不关闭界面本身）"""
        if not self.loginWindowThread or not self.loginWindowThread.isRunning():
            return

        log.info("关闭登录窗口...")

        # 调用窗口的close方法
        if hasattr(self.loginWindowThread, 'window') and self.loginWindowThread.window:
            try:
                self.loginWindowThread.window.close()
            except Exception as e:
                log.error(f"关闭窗口失败: {e}")

        # 等待线程结束
        if not self.loginWindowThread.wait(2000):
            log.warning("线程超时，强制终止")
            self.loginWindowThread.terminate()

        log.info("登录窗口已关闭")

    def closeEvent(self, event):
        """界面关闭事件处理"""
        log.info("账号管理视图正在关闭...")

        # 关闭登录窗口
        self.closeLoginWindow()

        # 清理头像加载线程
        for loader in self.avatarLoaders:
            loader.quit()
            loader.wait()

        event.accept()

    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(20)

        # 顶部按钮区域
        buttonLayout = QHBoxLayout()

        # 添加左侧弹性空间，让按钮靠右
        buttonLayout.addStretch()

        self.addAccountBtn = PrimaryPushButton(FIF.ADD, "添加账号", self)
        self.addAccountBtn.clicked.connect(self.onAddAccount)
        buttonLayout.addWidget(self.addAccountBtn)

        self.refreshBtn = PushButton(FIF.SYNC, "刷新", self)
        self.refreshBtn.clicked.connect(self.onRefresh)
        buttonLayout.addWidget(self.refreshBtn)

        layout.addLayout(buttonLayout)

        # 账号表格
        self.accountTable = TableWidget(self)
        self.accountTable.setBorderVisible(True)
        self.accountTable.setBorderRadius(8)
        self.accountTable.setWordWrap(False)
        self.accountTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.accountTable.customContextMenuRequested.connect(self.showContextMenu)

        # 设置表格列
        self.accountTable.setColumnCount(4)
        self.accountTable.setHorizontalHeaderLabels(['头像', '名字', '积分', '会员到期日'])

        # 设置列宽 - 四列等宽
        self.accountTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accountTable.verticalHeader().setVisible(False)

        layout.addWidget(self.accountTable)

        # 加载数据库数据
        self.loadAccounts()

    def loadAccounts(self):
        """从数据库加载账号数据"""
        try:
            # 清空之前的加载线程
            for loader in self.avatarLoaders:
                loader.quit()
                loader.wait()
            self.avatarLoaders.clear()

            # 从数据库获取所有账号
            accounts = JimengAccount.get_all_accounts()
            self.accountTable.setRowCount(len(accounts))

            for row, account in enumerate(accounts):
                # 头像列 - 创建QLabel显示图片
                avatarLabel = QLabel()
                avatarLabel.setAlignment(Qt.AlignCenter)
                avatarLabel.setFixedSize(60, 60)
                avatarLabel.setScaledContents(True)
                avatarLabel.setText("加载中...")

                # 创建容器widget使头像居中
                avatarWidget = QWidget()
                avatarLayout = QHBoxLayout(avatarWidget)
                avatarLayout.setContentsMargins(10, 5, 10, 5)
                avatarLayout.addWidget(avatarLabel)

                self.accountTable.setCellWidget(row, 0, avatarWidget)
                self.accountTable.setRowHeight(row, 70)

                # 异步加载头像
                avatar_url = account.avatar if account.avatar else self.DEFAULT_AVATAR_URL
                loader = AvatarLoader(row, avatar_url)
                loader.finished.connect(self.onAvatarLoaded)
                self.avatarLoaders.append(loader)
                loader.start()

                # 名字列
                nameItem = QTableWidgetItem(account.nickname)
                nameItem.setTextAlignment(Qt.AlignCenter)
                nameItem.setData(Qt.UserRole, account.id)  # 存储账号ID
                self.accountTable.setItem(row, 1, nameItem)

                # 积分列
                pointsItem = QTableWidgetItem(str(account.points))
                pointsItem.setTextAlignment(Qt.AlignCenter)
                self.accountTable.setItem(row, 2, pointsItem)

                # 会员到期日列
                vip_text = "未开通"
                if account.vip_expire_time:
                    now = datetime.now()
                    if account.vip_expire_time > now:
                        vip_text = account.vip_expire_time.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        vip_text = "已过期"

                vipItem = QTableWidgetItem(vip_text)
                vipItem.setTextAlignment(Qt.AlignCenter)
                self.accountTable.setItem(row, 3, vipItem)

            log.info(f"加载了 {len(accounts)} 个账号")

        except Exception as e:
            log.error(f"加载账号失败: {e}")
            InfoBar.error(
                title="加载失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )

    def onAvatarLoaded(self, row, pixmap):
        """头像加载完成"""
        if row < self.accountTable.rowCount():
            avatarWidget = self.accountTable.cellWidget(row, 0)
            if avatarWidget:
                avatarLabel = avatarWidget.findChild(QLabel)
                if avatarLabel:
                    # 将图片缩放为圆形
                    scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    avatarLabel.setPixmap(scaled_pixmap)

    def showContextMenu(self, pos: QPoint):
        """显示右键菜单"""
        # 获取点击的行
        item = self.accountTable.itemAt(pos)
        if not item:
            return

        row = item.row()
        account_id = self.accountTable.item(row, 1).data(Qt.UserRole)

        # 创建右键菜单 - 使用 Fluent 风格的 RoundMenu
        menu = RoundMenu(parent=self)

        # 添加登录操作
        loginAction = Action(FIF.SYNC, "登录", self)
        loginAction.triggered.connect(lambda: self.onLogin(account_id))
        menu.addAction(loginAction)

        # 添加删除操作
        deleteAction = Action(FIF.DELETE, "删除", self)
        deleteAction.triggered.connect(lambda: self.onDelete(account_id))
        menu.addAction(deleteAction)

        # 显示菜单
        menu.exec(QCursor.pos())

    def onAddAccount(self):
        """添加账号 - 调用即梦登录机器人"""
        try:
            log.info("开始添加即梦账号...")
            InfoBar.info(
                title="正在登录",
                content="请在浏览器中完成登录操作...",
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP
            )

            # 在新线程中执行登录
            from PyQt5.QtCore import QThread

            class LoginThread(QThread):
                finished = pyqtSignal(object)

                def run(self):
                    from app.robot.jimeng.jimeng_login_robot import JimengLoginRobot
                    robot = JimengLoginRobot(headless=False)
                    result = robot.login(timeout=300)
                    self.finished.emit(result)

            self.loginThread = LoginThread()
            self.loginThread.finished.connect(self.onLoginFinished)
            self.loginThread.start()

        except Exception as e:
            log.error(f"添加账号失败: {e}")
            InfoBar.error(
                title="添加失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )

    def onLoginFinished(self, result):
        """登录完成回调"""
        try:
            if result.is_success():
                # 保存到数据库
                account = JimengAccount.create(
                    avatar=result.avatar,
                    nickname=result.nickname,
                    points=result.points,
                    vip_type="标准会员" if result.is_vip else "普通会员",
                    vip_expire_time=result.vip_expire_date,
                    cookies=result.cookies
                )

                log.info(f"账号添加成功: {result.nickname}")
                InfoBar.success(
                    title="添加成功",
                    content=f"账号 {result.nickname} 已添加",
                    parent=self,
                    duration=3000,
                    position=InfoBarPosition.TOP
                )

                # 刷新列表
                self.loadAccounts()
            else:
                log.error(f"登录失败: {result.message}")
                InfoBar.error(
                    title="登录失败",
                    content=result.message,
                    parent=self,
                    position=InfoBarPosition.TOP
                )

        except Exception as e:
            log.error(f"保存账号失败: {e}")
            InfoBar.error(
                title="保存失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )

    def onRefresh(self):
        """刷新"""
        log.info("刷新账号列表")
        self.loadAccounts()
        InfoBar.success(
            title="刷新成功",
            content="账号列表已更新",
            parent=self,
            duration=2000,
            position=InfoBarPosition.TOP
        )

    def onLogin(self, account_id):
        """登录账号"""
        try:
            log.info(f"登录账号: {account_id}")

            # 从数据库获取账号信息
            account = JimengAccount.get_account_by_id(account_id)
            if not account:
                InfoBar.error(
                    title="登录失败",
                    content="账号不存在",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                return

            if not account.cookies:
                InfoBar.error(
                    title="登录失败",
                    content="该账号没有cookies信息",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                return

            InfoBar.info(
                title="正在登录",
                content=f"正在打开 {account.nickname} 的登录窗口...",
                parent=self,
                duration=2000,
                position=InfoBarPosition.TOP
            )

            # 在新线程中打开登录窗口，避免阻塞UI
            from PyQt5.QtCore import QThread

            class LoginWindowThread(QThread):
                finished = pyqtSignal()
                error = pyqtSignal(str)

                def __init__(self, cookies):
                    super().__init__()
                    self.cookies = cookies
                    self.window = None  # 保存窗口实例

                def run(self):
                    try:
                        from app.robot.jimeng.jimeng_login_window import JimengLoginWindow
                        self.window = JimengLoginWindow(self.cookies)
                        self.window.open()  # 阻塞等待用户关闭
                        self.finished.emit()
                    except Exception as e:
                        self.error.emit(str(e))

            self.loginWindowThread = LoginWindowThread(account.cookies)
            self.loginWindowThread.finished.connect(self.onLoginWindowClosed)
            self.loginWindowThread.error.connect(self.onLoginWindowError)
            self.loginWindowThread.start()

        except Exception as e:
            log.error(f"登录账号失败: {e}")
            InfoBar.error(
                title="登录失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )

    def onLoginWindowClosed(self):
        """登录窗口关闭回调"""
        log.info("登录窗口已关闭")
        InfoBar.success(
            title="提示",
            content="登录窗口已关闭",
            parent=self,
            duration=2000,
            position=InfoBarPosition.TOP
        )

    def onLoginWindowError(self, error_msg):
        """登录窗口错误回调"""
        # 如果是用户主动关闭导致的错误，不显示错误提示
        if "has been closed" in error_msg:
            log.info("用户主动关闭了登录窗口")
            return

        log.error(f"登录窗口错误: {error_msg}")
        InfoBar.error(
            title="登录失败",
            content=error_msg,
            parent=self,
            position=InfoBarPosition.TOP
        )

    def onDelete(self, account_id):
        """删除账号"""
        # 确认对话框
        w = MessageBox(
            "确认删除",
            "确定要删除这个账号吗？",
            self
        )

        if w.exec():
            try:
                # 从数据库删除
                if JimengAccount.delete_account(account_id):
                    log.info(f"账号删除成功: {account_id}")
                    InfoBar.success(
                        title="删除成功",
                        content="账号已删除",
                        parent=self,
                        duration=2000,
                        position=InfoBarPosition.TOP
                    )
                    # 刷新列表
                    self.loadAccounts()
                else:
                    InfoBar.error(
                        title="删除失败",
                        content="账号不存在",
                        parent=self,
                        position=InfoBarPosition.TOP
                    )
            except Exception as e:
                log.error(f"删除账号失败: {e}")
                InfoBar.error(
                    title="删除失败",
                    content=str(e),
                    parent=self,
                    position=InfoBarPosition.TOP
                )