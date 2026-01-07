# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView
from qfluentwidgets import (PrimaryPushButton, PushButton, TableWidget, ComboBox,
                            FluentIcon as FIF, InfoBar, InfoBarPosition, Dialog,
                            BodyLabel, CheckBox, Action, RoundMenu, MessageBox, LineEdit)
from app.models.jimeng_account import JimengAccount
from app.utils.logger import log


class AddAccountDialog(Dialog):
    """批量添加账号对话框"""

    def __init__(self, parent=None):
        super().__init__("批量添加账号", "", parent)
        self.setFixedWidth(600)
        self.setFixedHeight(400)

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # 说明
        hint_label = BodyLabel("每行一个 Session ID 或 Token，系统将自动查询积分", content)
        layout.addWidget(hint_label)

        # Session ID 输入框（文本编辑）
        from qfluentwidgets import TextEdit
        self.session_edit = TextEdit(content)
        self.session_edit.setPlaceholderText("请输入账号列表，每行一个 Session ID 或 Token")
        layout.addWidget(self.session_edit)

        self.textLayout.addWidget(content)

        self.yesButton.setText("批量添加")
        self.cancelButton.setText("取消")

    def get_session_ids(self) -> list:
        """获取所有输入的 Session ID"""
        text = self.session_edit.toPlainText()
        # 按行分割，去除空行和多余空格
        ids = [line.strip() for line in text.split('\n') if line.strip()]
        return ids


class AccountManageView(QWidget):
    """即梦国内版账号管理视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("accountManage")
        self.current_page = 1
        self.page_size = 20
        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(20)

        # 顶部操作栏
        top = QHBoxLayout()

        self.selectAllCheckBox = CheckBox("全选", self)
        self.selectAllCheckBox.stateChanged.connect(self.onSelectAllChanged)
        top.addWidget(self.selectAllCheckBox)

        top.addStretch()

        self.addAccountBtn = PrimaryPushButton(FIF.ADD, "添加账号", self)
        self.addAccountBtn.clicked.connect(self.onAddAccount)
        top.addWidget(self.addAccountBtn)

        self.refreshBtn = PushButton(FIF.SYNC, "刷新", self)
        self.refreshBtn.clicked.connect(self.onRefresh)
        top.addWidget(self.refreshBtn)

        self.checkPointsBtn = PushButton(FIF.CLOUD, "查询积分", self)
        self.checkPointsBtn.clicked.connect(self.onCheckPoints)
        top.addWidget(self.checkPointsBtn)

        self.deleteBtn = PushButton(FIF.DELETE, "删除", self)
        self.deleteBtn.clicked.connect(self.onBatchDelete)
        top.addWidget(self.deleteBtn)

        layout.addLayout(top)

        # 账号表格
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "ID", "Session ID", "积分", "创建时间"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 200)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(TableWidget.SelectRows)
        self.table.setSelectionMode(TableWidget.ExtendedSelection)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)

        layout.addWidget(self.table)

        # 底部分页
        bottom = QHBoxLayout()

        sizeLabel = BodyLabel("每页显示:", self)
        bottom.addWidget(sizeLabel)

        self.pageSizeCombo = ComboBox(self)
        self.pageSizeCombo.addItems(['10', '20', '50', '100'])
        self.pageSizeCombo.setCurrentText('20')
        self.pageSizeCombo.currentTextChanged.connect(self.onPageSizeChanged)
        self.pageSizeCombo.setFixedWidth(100)
        bottom.addWidget(self.pageSizeCombo)

        bottom.addStretch()

        self.pageInfoLabel = BodyLabel("第 1 页，共 0 条", self)
        bottom.addWidget(self.pageInfoLabel)

        bottom.addSpacing(20)

        self.prevPageBtn = PushButton(FIF.CARE_LEFT_SOLID, "上一页", self)
        self.prevPageBtn.clicked.connect(self.onPrevPage)
        bottom.addWidget(self.prevPageBtn)

        self.nextPageBtn = PushButton(FIF.CARE_RIGHT_SOLID, "下一页", self)
        self.nextPageBtn.clicked.connect(self.onNextPage)
        bottom.addWidget(self.nextPageBtn)

        layout.addLayout(bottom)

        # 加载数据
        self.loadAccounts()

    def loadAccounts(self):
        """加载账号列表"""
        try:
            accounts, total_count = JimengAccount.get_accounts_by_page(self.current_page, self.page_size)

            self.table.clearContents()
            self.table.setRowCount(len(accounts))

            for row, account in enumerate(accounts):
                # 复选框
                checkbox = CheckBox()
                container = QWidget(self.table)
                c_layout = QHBoxLayout(container)
                c_layout.setContentsMargins(0, 0, 0, 0)
                c_layout.setAlignment(Qt.AlignCenter)
                c_layout.addWidget(checkbox)
                self.table.setCellWidget(row, 0, container)

                # ID
                id_item = QTableWidgetItem(str(account.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                id_item.setData(Qt.UserRole, account.id)
                self.table.setItem(row, 1, id_item)

                # Session ID (显示全部)
                session_id = account.session_id or ""
                session_item = QTableWidgetItem(session_id)
                session_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 2, session_item)

                # 积分
                points_item = QTableWidgetItem(str(account.points))
                points_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, points_item)

                # 创建时间
                created_at = account.created_at.strftime("%Y-%m-%d %H:%M:%S") if account.created_at else "-"
                time_item = QTableWidgetItem(created_at)
                time_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 4, time_item)

            # 更新分页信息
            total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
            self.pageInfoLabel.setText(f"第 {self.current_page} 页，共 {total_count} 条")
            self.prevPageBtn.setEnabled(self.current_page > 1)
            self.nextPageBtn.setEnabled(self.current_page < total_pages)

        except Exception as e:
            log.error(f"加载账号列表失败: {e}")
            self.table.setRowCount(0)
            InfoBar.error(title="加载失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def _create_loading_dialog(self, total_items: int, title: str = "正在处理") -> tuple:
        """创建美化的加载对话框"""
        from qfluentwidgets import ProgressBar

        loading_dlg = Dialog("", "", self)
        loading_dlg.setFixedWidth(400)
        loading_dlg.setFixedHeight(150)
        loading_dlg.yesButton.setVisible(False)
        loading_dlg.cancelButton.setVisible(False)
        loading_dlg.titleLabel.setVisible(False)

        # 直接在 textLayout 中添加内容
        main_widget = QWidget(loading_dlg)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 标题
        title_label = BodyLabel(title, main_widget)
        title_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(title_label)

        # 状态文本
        status_label = BodyLabel("初始化中...", main_widget)
        status_label.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.65);")
        layout.addWidget(status_label)

        # 进度条容器
        progress_container = QWidget(main_widget)
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(10)

        # 进度条
        progress_bar = ProgressBar(progress_container)
        progress_bar.setRange(0, total_items)
        progress_bar.setFixedHeight(5)
        progress_layout.addWidget(progress_bar, 1)

        # 进度百分比文本
        progress_text = BodyLabel("0%", progress_container)
        progress_text.setStyleSheet("font-size: 11px; color: rgba(255, 255, 255, 0.6); min-width: 30px;")
        progress_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progress_layout.addWidget(progress_text)

        layout.addWidget(progress_container)

        loading_dlg.textLayout.addWidget(main_widget)

        return loading_dlg, status_label, progress_bar, progress_text

    def onAddAccount(self):
        """批量添加账号"""
        dlg = AddAccountDialog(self)
        if dlg.exec():
            session_ids = dlg.get_session_ids()
            if not session_ids:
                InfoBar.warning(title="提示", content="请输入至少一个 Session ID", parent=self, position=InfoBarPosition.TOP)
                return

            # 创建加载对话框
            loading_dlg, status_label, progress_bar, progress_text = self._create_loading_dialog(
                len(session_ids), "正在添加账号"
            )

            # 使用线程进行异步处理
            from PyQt5.QtCore import QThread, pyqtSignal

            class AddAccountsThread(QThread):
                progress = pyqtSignal(int, int, str)  # (current, total, status)
                finished = pyqtSignal(int, int)  # (success, failed)

                def __init__(self, session_ids):
                    super().__init__()
                    self.session_ids = session_ids

                def run(self):
                    try:
                        from app.client.jimeng_api_client import get_jimeng_api_client
                        client = get_jimeng_api_client()
                        success_count = 0
                        failed_count = 0

                        for idx, session_id in enumerate(self.session_ids):
                            try:
                                self.progress.emit(idx + 1, len(self.session_ids), f"正在处理 ({idx + 1}/{len(self.session_ids)}): {session_id[:30]}")

                                # 查询积分
                                total_credit = client.account_check(session_id)

                                # 创建账号
                                account = JimengAccount.create_account(session_id=session_id)
                                account.points = total_credit
                                account.save()

                                success_count += 1
                            except Exception as e:
                                log.error(f"处理账号 {session_id} 失败: {e}")
                                failed_count += 1

                        self.finished.emit(success_count, failed_count)

                    except Exception as e:
                        log.error(f"批量添加账号失败: {e}")
                        self.finished.emit(0, len(self.session_ids))

            def on_progress(current, total, status):
                status_label.setText(status)
                progress_bar.setValue(current)
                percentage = int((current / total * 100)) if total > 0 else 0
                progress_text.setText(f"{percentage}%")

            def on_finished(success, failed):
                loading_dlg.close()
                self.loadAccounts()
                if success > 0:
                    message = f"成功添加 {success} 个账号"
                    if failed > 0:
                        message += f"，{failed} 个失败"
                    InfoBar.success(
                        title="批量添加完成",
                        content=message,
                        parent=self,
                        duration=3000,
                        position=InfoBarPosition.TOP
                    )
                else:
                    InfoBar.error(
                        title="批量添加失败",
                        content=f"所有 {failed} 个账号添加失败",
                        parent=self,
                        position=InfoBarPosition.TOP
                    )

            self.addThread = AddAccountsThread(session_ids)
            self.addThread.progress.connect(on_progress)
            self.addThread.finished.connect(on_finished)
            self.addThread.start()

            # 显示加载对话框
            loading_dlg.exec()

    def onRefresh(self):
        """刷新列表"""
        self.loadAccounts()
        InfoBar.success(title="刷新成功", content="账号列表已更新", parent=self, duration=2000, position=InfoBarPosition.TOP)

    def onCheckPoints(self):
        """查询所有账号的积分"""
        # 获取所有未删除的账号
        try:
            all_accounts = JimengAccount.select().where(JimengAccount.is_deleted == 0)
            account_ids = [acc.id for acc in all_accounts]

            if not account_ids:
                InfoBar.warning(title="提示", content="没有可查询的账号", parent=self, position=InfoBarPosition.TOP)
                return

            # 创建加载对话框
            loading_dlg, status_label, progress_bar, progress_text = self._create_loading_dialog(
                len(account_ids), "正在查询全部账号积分"
            )

            # 使用线程进行异步处理
            from PyQt5.QtCore import QThread, pyqtSignal

            class CheckAllPointsThread(QThread):
                progress = pyqtSignal(int, int, str)
                finished = pyqtSignal(int, int)  # (success, failed)

                def __init__(self, account_ids):
                    super().__init__()
                    self.account_ids = account_ids

                def run(self):
                    try:
                        from app.client.jimeng_api_client import get_jimeng_api_client
                        client = get_jimeng_api_client()
                        success_count = 0
                        failed_count = 0

                        for idx, account_id in enumerate(self.account_ids):
                            try:
                                account = JimengAccount.get_account_by_id(account_id)
                                if not account:
                                    failed_count += 1
                                    continue

                                self.progress.emit(idx + 1, len(self.account_ids), f"正在查询 ({idx + 1}/{len(self.account_ids)})")

                                total_credit = client.account_check(account.session_id)
                                account.points = total_credit
                                account.save()
                                success_count += 1

                            except Exception as e:
                                log.error(f"查询账号 {account_id} 失败: {e}")
                                failed_count += 1

                        self.finished.emit(success_count, failed_count)

                    except Exception as e:
                        log.error(f"批量查询积分失败: {e}")
                        self.finished.emit(0, len(self.account_ids))

            def on_progress(current, total, status):
                status_label.setText(status)
                progress_bar.setValue(current)
                percentage = int((current / total * 100)) if total > 0 else 0
                progress_text.setText(f"{percentage}%")

            def on_finished(success, failed):
                loading_dlg.close()
                self.loadAccounts()
                if success > 0:
                    message = f"成功查询 {success} 个账号"
                    if failed > 0:
                        message += f"，{failed} 个失败"
                    InfoBar.success(
                        title="查询完成",
                        content=message,
                        parent=self,
                        duration=3000,
                        position=InfoBarPosition.TOP
                    )
                else:
                    InfoBar.error(
                        title="查询失败",
                        content=f"所有 {failed} 个账号查询失败",
                        parent=self,
                        position=InfoBarPosition.TOP
                    )

            self.checkThread = CheckAllPointsThread(account_ids)
            self.checkThread.progress.connect(on_progress)
            self.checkThread.finished.connect(on_finished)
            self.checkThread.start()

            # 显示加载对话框
            loading_dlg.exec()

        except Exception as e:
            log.error(f"查询所有账号积分失败: {e}")
            InfoBar.error(title="查询失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onBatchDelete(self):
        """批量删除"""
        selected_ids = self._getSelectedAccountIds()
        if not selected_ids:
            InfoBar.warning(title="提示", content="请先勾选要删除的账号", parent=self, position=InfoBarPosition.TOP)
            return

        msg_box = MessageBox("确认删除", f"确定要删除选中的 {len(selected_ids)} 个账号吗？", self)
        if msg_box.exec():
            success_count = 0
            for account_id in selected_ids:
                if JimengAccount.delete_account(account_id):
                    success_count += 1

            self.loadAccounts()
            InfoBar.success(
                title="删除成功",
                content=f"成功删除 {success_count} 个账号",
                parent=self,
                duration=2000,
                position=InfoBarPosition.TOP
            )

    def onSelectAllChanged(self, state):
        """全选状态改变"""
        checked = (state == Qt.Checked)
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, 0)
            if container:
                cb = container.findChild(CheckBox)
                if cb:
                    cb.setChecked(checked)

    def _getSelectedAccountIds(self):
        """获取选中的账号ID列表"""
        ids = []
        for row in range(self.table.rowCount()):
            container = self.table.cellWidget(row, 0)
            if container:
                cb = container.findChild(CheckBox)
                if cb and cb.isChecked():
                    id_item = self.table.item(row, 1)
                    if id_item:
                        account_id = id_item.data(Qt.UserRole)
                        if account_id:
                            ids.append(int(account_id))
        return ids

    def showContextMenu(self, pos):
        """显示右键菜单"""
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        id_item = self.table.item(row, 1)
        if not id_item:
            return

        account_id = id_item.data(Qt.UserRole)
        menu = RoundMenu(parent=self)

        check_action = Action(FIF.CLOUD, "查询积分", self)
        check_action.triggered.connect(lambda: self.onCheckSingleAccount(int(account_id)))
        menu.addAction(check_action)

        delete_action = Action(FIF.DELETE, "删除", self)
        delete_action.triggered.connect(lambda: self.onDeleteAccount(int(account_id)))
        menu.addAction(delete_action)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def onCheckSingleAccount(self, account_id: int):
        """查询单个账号积分"""
        try:
            from app.client.jimeng_api_client import get_jimeng_api_client
            account = JimengAccount.get_account_by_id(account_id)
            if not account:
                InfoBar.error(title="查询失败", content="账号不存在", parent=self, position=InfoBarPosition.TOP)
                return

            client = get_jimeng_api_client()
            total_credit = client.account_check(account.session_id)
            account.points = total_credit
            account.save()

            self.loadAccounts()
            InfoBar.success(
                title="查询成功",
                content=f"账号 #{account_id} 积分: {total_credit}",
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP
            )

        except Exception as e:
            log.error(f"查询积分失败: {e}")
            InfoBar.error(title="查询失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onDeleteAccount(self, account_id: int):
        """删除单个账号"""
        msg_box = MessageBox("确认删除", f"确定要删除账号 #{account_id} 吗？", self)
        if msg_box.exec():
            if JimengAccount.delete_account(account_id):
                InfoBar.success(title="删除成功", content=f"账号 #{account_id} 已删除", parent=self, duration=2000, position=InfoBarPosition.TOP)
                self.loadAccounts()
            else:
                InfoBar.error(title="删除失败", content="账号不存在", parent=self, position=InfoBarPosition.TOP)

    def onPageSizeChanged(self, size):
        """每页显示数量改变"""
        self.page_size = int(size)
        self.current_page = 1
        self.loadAccounts()

    def onPrevPage(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.loadAccounts()

    def onNextPage(self):
        """下一页"""
        self.current_page += 1
        self.loadAccounts()
