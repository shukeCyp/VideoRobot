# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView
from qfluentwidgets import (PrimaryPushButton, PushButton, TableWidget, ComboBox,
                            FluentIcon as FIF, InfoBar, InfoBarPosition, Dialog,
                            BodyLabel, CheckBox, Action, RoundMenu, MessageBox, LineEdit)
from app.models.jimeng_intl_account import JimengIntlAccount
from app.utils.logger import log
from datetime import datetime


class AddAccountDialog(Dialog):
    """批量添加账号对话框"""

    def __init__(self, parent=None):
        super().__init__("批量添加账号", "", parent)
        self.setFixedWidth(600)
        self.setFixedHeight(450)

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # 地区选择
        region_layout = QHBoxLayout()
        region_label = BodyLabel("地区选择:", content)
        region_layout.addWidget(region_label)

        from qfluentwidgets import RadioButton
        self.region_group = []
        regions = [
            ("美国(us)", "us"),
            ("香港(hk)", "hk"),
            ("日本(jp)", "jp"),
            ("新加坡(sg)", "sg")
        ]

        for text, value in regions:
            radio = RadioButton(text, content)
            radio.value = value
            self.region_group.append(radio)
            region_layout.addWidget(radio)
            # 默认选择香港
            if value == "hk":
                radio.setChecked(True)

        region_layout.addStretch()
        layout.addLayout(region_layout)

        # 说明
        hint_label = BodyLabel("每行一个 Session ID 或 Token，系统将自动添加地区前缀并查询积分", content)
        layout.addWidget(hint_label)

        # Session ID 输入框（文本编辑）
        from qfluentwidgets import TextEdit
        self.session_edit = TextEdit(content)
        self.session_edit.setPlaceholderText("请输入账号列表，每行一个 Session ID 或 Token")
        layout.addWidget(self.session_edit)

        self.textLayout.addWidget(content)

        self.yesButton.setText("批量添加")
        self.cancelButton.setText("取消")

    def get_region(self) -> str:
        """获取选择的地区"""
        for radio in self.region_group:
            if radio.isChecked():
                return radio.value
        return "hk"  # 默认香港

    def get_session_ids(self) -> list:
        """获取所有输入的 Session ID"""
        text = self.session_edit.toPlainText()
        # 按行分割，去除空行和多余空格
        ids = [line.strip() for line in text.split('\n') if line.strip()]
        return ids


class AccountManageIntlView(QWidget):
    """即梦国际版账号管理视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("accountManageIntl")
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

        self.batchDeleteBtn = PushButton(FIF.DELETE, "批量删除", self)
        self.batchDeleteBtn.clicked.connect(self.onBatchDelete)
        top.addWidget(self.batchDeleteBtn)

        layout.addLayout(top)

        # 账号表格
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["", "ID", "Session ID", "积分", "账号类型", "禁用状态", "操作"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 200)

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
            accounts, total_count = JimengIntlAccount.get_accounts_by_page(self.current_page, self.page_size)

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

                # 账号类型
                account_type_text = "积分账号" if account.account_type == 1 else "0积分账号"
                type_item = QTableWidgetItem(account_type_text)
                type_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 4, type_item)

                # 禁用状态
                today = datetime.now().date()
                is_disabled = account.disabled_at and account.disabled_at.date() <= today

                status_item = QTableWidgetItem("禁用" if is_disabled else "正常")
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setData(Qt.UserRole, account.id)

                if is_disabled:
                    status_item.setForeground(QColor("#FF3B30"))  # 红色
                else:
                    status_item.setForeground(QColor("#34C759"))  # 绿色

                self.table.setItem(row, 5, status_item)

                # 操作按钮
                action_container = QWidget(self.table)
                action_layout = QHBoxLayout(action_container)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setSpacing(5)
                action_layout.setAlignment(Qt.AlignCenter)

                # 积分按钮
                points_btn = PushButton("积分", action_container)
                points_btn.setFixedWidth(60)
                points_btn.clicked.connect(lambda checked, aid=account.id: self.onCheckSingleAccount(aid))
                action_layout.addWidget(points_btn)

                # 禁用/解禁按钮
                toggle_btn = PushButton("解禁" if is_disabled else "禁用", action_container)
                toggle_btn.setFixedWidth(60)
                toggle_btn.clicked.connect(lambda checked, aid=account.id: self.onToggleDisable(aid))
                action_layout.addWidget(toggle_btn)

                # 删除按钮
                delete_btn = PushButton("删除", action_container)
                delete_btn.setFixedWidth(60)
                delete_btn.clicked.connect(lambda checked, aid=account.id: self.onDeleteAccount(aid))
                action_layout.addWidget(delete_btn)

                self.table.setCellWidget(row, 6, action_container)

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
            region = dlg.get_region()

            if not session_ids:
                InfoBar.warning(title="提示", content="请输入至少一个 Session ID", parent=self, position=InfoBarPosition.TOP)
                return

            # 为每个 session_id 添加地区前缀
            prefixed_session_ids = [f"{region}-{sid}" for sid in session_ids]

            # 创建加载对话框
            loading_dlg, status_label, progress_bar, progress_text = self._create_loading_dialog(
                len(prefixed_session_ids), "正在添加账号"
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
                                account = JimengIntlAccount.create_account(session_id=session_id)
                                account.points = total_credit
                                account.account_type = 1 if total_credit > 0 else 0

                                # 如果有积分账号的积分小于4，自动禁用
                                if account.account_type == 1 and total_credit < 4:
                                    account.disabled_at = datetime.now()
                                    log.warning(f"新添加账号 {session_id[:30]} 积分不足({total_credit})，已自动禁用")

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

            self.addThread = AddAccountsThread(prefixed_session_ids)
            self.addThread.progress.connect(on_progress)
            self.addThread.finished.connect(on_finished)
            self.addThread.start()

            # 显示加载对话框
            loading_dlg.exec()

    def onRefresh(self):
        """刷新列表"""
        self.loadAccounts()
        InfoBar.success(title="刷新成功", content="账号列表已更新", parent=self, duration=2000, position=InfoBarPosition.TOP)

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
                if JimengIntlAccount.delete_account(account_id):
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
            account = JimengIntlAccount.get_account_by_id(account_id)
            if not account:
                InfoBar.error(title="查询失败", content="账号不存在", parent=self, position=InfoBarPosition.TOP)
                return

            client = get_jimeng_api_client()
            total_credit = client.account_check(account.session_id)
            account.points = total_credit
            account.account_type = 1 if total_credit > 0 else 0

            # 如果有积分账号的积分小于4，自动禁用
            if account.account_type == 1 and total_credit < 4:
                account.disabled_at = datetime.now()
                log.warning(f"账号 {account_id} 积分不足({total_credit})，已自动禁用")

            account.save()

            self.loadAccounts()

            message = f"账号 #{account_id} 积分: {total_credit}"
            if account.account_type == 1 and total_credit < 4:
                message += " (已自动禁用)"

            InfoBar.success(
                title="查询成功",
                content=message,
                parent=self,
                duration=3000,
                position=InfoBarPosition.TOP
            )

        except Exception as e:
            log.error(f"查询积分失败: {e}")
            InfoBar.error(title="查询失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onToggleDisable(self, account_id: int):
        """禁用/解禁账号"""
        try:
            account = JimengIntlAccount.get_account_by_id(account_id)
            if not account:
                InfoBar.error(title="错误", content="账号不存在", parent=self, position=InfoBarPosition.TOP)
                return

            today = datetime.now().date()
            is_currently_disabled = account.disabled_at and account.disabled_at.date() <= today

            if is_currently_disabled:
                # 解禁：设置disabled_at为None
                action_text = "解禁"
                account.disabled_at = None
            else:
                # 禁用：设置disabled_at为今天
                action_text = "禁用"
                account.disabled_at = datetime.now()

            account.save()
            self.loadAccounts()

            InfoBar.success(
                title="操作成功",
                content=f"账号 #{account_id} 已{action_text}",
                parent=self,
                duration=2000,
                position=InfoBarPosition.TOP
            )

        except Exception as e:
            log.error(f"禁用/解禁账号失败: {e}")
            InfoBar.error(title="操作失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onDeleteAccount(self, account_id: int):
        """删除单个账号"""
        msg_box = MessageBox("确认删除", f"确定要删除账号 #{account_id} 吗？", self)
        if msg_box.exec():
            if JimengIntlAccount.delete_account(account_id):
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
