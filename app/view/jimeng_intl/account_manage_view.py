from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import PrimaryPushButton, PushButton, TableWidget, RoundMenu, Action, InfoBar, InfoBarPosition, Dialog, TextEdit, BodyLabel, FluentIcon as FIF, ComboBox
from app.models.jimeng_intl_account import JimengIntlAccount
from app.utils.logger import log


class BatchAddIntlAccountDialog(Dialog):
    def __init__(self, parent=None):
        super().__init__("", "", parent)
        self.setFixedWidth(720)
        self.titleLabel.setVisible(False)
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        header = QHBoxLayout()
        desc = BodyLabel("每行一个账号，格式：account----password")
        header.addWidget(desc)
        header.addStretch()
        clear_btn = PushButton("清空输入", content)
        clear_btn.clicked.connect(lambda: self.text_edit.clear())
        header.addWidget(clear_btn)
        layout.addLayout(header)
        self.text_edit = TextEdit(content)
        self.text_edit.setPlaceholderText("例如：\nuser1----pass1\nuser2----pass2")
        self.text_edit.setFixedHeight(260)
        layout.addWidget(self.text_edit)
        self.count_label = BodyLabel("已解析 0 行", content)
        self.count_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.count_label)
        self.text_edit.textChanged.connect(self._updateCount)
        self.textLayout.addWidget(content)
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")
        self.yesButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

    def get_lines(self):
        raw = self.text_edit.toPlainText()
        lines = [l.strip() for l in raw.splitlines()]
        return [l for l in lines if l]

    def _updateCount(self):
        raw = self.text_edit.toPlainText()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        self.count_label.setText(f"已解析 {len(lines)} 行")


class AccountManageIntlView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("accountManageIntl")
        self.loginWindowThread = None
        self.current_page = 1
        self.page_size = 20
        self._initUI()

    def _initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)
        layout.setSpacing(20)

        top = QHBoxLayout()
        top.addStretch()
        self.add_btn = PrimaryPushButton("批量添加", self)
        self.add_btn.clicked.connect(self.onBatchAdd)
        top.addWidget(self.add_btn)
        self.refresh_btn = PushButton("刷新", self)
        self.refresh_btn.clicked.connect(self.onRefresh)
        top.addWidget(self.refresh_btn)
        self.delete_all_btn = PushButton(FIF.DELETE, "删除全部", self)
        self.delete_all_btn.clicked.connect(self.onDeleteAll)
        top.addWidget(self.delete_all_btn)
        layout.addLayout(top)

        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["账号", "密码", "Cookies", "创建时间", "更新时间"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)
        layout.addWidget(self.table)

        pagination = QHBoxLayout()
        pageSizeLabel = BodyLabel("每页显示:", self)
        pagination.addWidget(pageSizeLabel)
        self.pageSizeCombo = ComboBox(self)
        self.pageSizeCombo.addItems(['10', '20', '50', '100'])
        self.pageSizeCombo.setCurrentText('20')
        self.pageSizeCombo.currentTextChanged.connect(self.onPageSizeChanged)
        self.pageSizeCombo.setFixedWidth(100)
        pagination.addWidget(self.pageSizeCombo)
        pagination.addStretch()
        self.pageInfoLabel = BodyLabel("第 1 页，共 0 条", self)
        pagination.addWidget(self.pageInfoLabel)
        pagination.addSpacing(20)
        self.firstPageBtn = PushButton(FIF.CARE_LEFT_SOLID, "首页", self)
        self.firstPageBtn.clicked.connect(self.onFirstPage)
        pagination.addWidget(self.firstPageBtn)
        self.prevPageBtn = PushButton(FIF.CARE_LEFT_SOLID, "上一页", self)
        self.prevPageBtn.clicked.connect(self.onPrevPage)
        pagination.addWidget(self.prevPageBtn)
        self.nextPageBtn = PushButton(FIF.CARE_RIGHT_SOLID, "下一页", self)
        self.nextPageBtn.clicked.connect(self.onNextPage)
        pagination.addWidget(self.nextPageBtn)
        self.lastPageBtn = PushButton(FIF.CARE_RIGHT_SOLID, "末页", self)
        self.lastPageBtn.clicked.connect(self.onLastPage)
        pagination.addWidget(self.lastPageBtn)
        layout.addLayout(pagination)

        self.loadAccounts()

    def loadAccounts(self):
        try:
            accounts, total_count = JimengIntlAccount.get_accounts_by_page(self.current_page, self.page_size)
            self.table.setRowCount(len(accounts))
            for row, acc in enumerate(accounts):
                item_account = QTableWidgetItem(acc.account)
                item_account.setTextAlignment(Qt.AlignCenter)
                item_account.setData(Qt.UserRole, acc.id)
                self.table.setItem(row, 0, item_account)

                item_pwd = QTableWidgetItem("******")
                item_pwd.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, item_pwd)

                ck = acc.cookies or ""
                display_ck = "有" if ck else "无"
                item_ck = QTableWidgetItem(display_ck)
                item_ck.setTextAlignment(Qt.AlignCenter)
                if ck:
                    item_ck.setToolTip("已保存Cookies")
                self.table.setItem(row, 2, item_ck)

                item_created = QTableWidgetItem(acc.createdate.strftime("%Y-%m-%d %H:%M:%S") if acc.createdate else "")
                item_created.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 3, item_created)

                item_updated = QTableWidgetItem(acc.updatedate.strftime("%Y-%m-%d %H:%M:%S") if acc.updatedate else "")
                item_updated.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 4, item_updated)

            self.updatePageInfo(total_count)
            log.info(f"加载第 {self.current_page} 页国际版账号，每页 {self.page_size} 条，共 {total_count} 条")
        except Exception as e:
            log.error(f"加载国际版账号失败: {e}")
            self.table.setRowCount(0)
            InfoBar.error(title="加载失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def updatePageInfo(self, total_count):
        total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
        self.pageInfoLabel.setText(f"第 {self.current_page} 页，共 {total_count} 条")
        self.firstPageBtn.setEnabled(self.current_page > 1)
        self.prevPageBtn.setEnabled(self.current_page > 1)
        self.nextPageBtn.setEnabled(self.current_page < total_pages)
        self.lastPageBtn.setEnabled(self.current_page < total_pages)

    def onBatchAdd(self):
        dlg = BatchAddIntlAccountDialog(self)
        if dlg.exec():
            lines = dlg.get_lines()
            if not lines:
                InfoBar.warning(title="提示", content="请输入账号列表", parent=self, position=InfoBarPosition.TOP)
                return
            ok, fail, skip = 0, 0, 0
            seen = set()
            for line in lines:
                try:
                    if "----" not in line:
                        fail += 1
                        continue
                    account, password = [s.strip() for s in line.split("----", 1)]
                    if not account:
                        fail += 1
                        continue
                    if account in seen:
                        skip += 1
                        continue
                    exists = JimengIntlAccount.select().where((JimengIntlAccount.account == account) & (JimengIntlAccount.isdel == 0)).exists()
                    if exists:
                        skip += 1
                        continue
                    JimengIntlAccount.create_account(account, password or "", None)
                    seen.add(account)
                    ok += 1
                except Exception as e:
                    log.error(f"批量添加国际版账号失败: {e}")
                    fail += 1
            if ok:
                msg = f"成功 {ok} 个"
                if skip:
                    msg += f"，跳过重复 {skip} 个"
                if fail:
                    msg += f"，失败 {fail} 个"
                InfoBar.success(title="批量添加完成", content=msg, parent=self, duration=3000, position=InfoBarPosition.TOP)
                self.loadAccounts()
            else:
                InfoBar.error(title="批量添加失败", content="全部失败，请检查格式", parent=self, position=InfoBarPosition.TOP)

    def onRefresh(self):
        self.loadAccounts()
        InfoBar.success(title="刷新成功", content="账号列表已更新", parent=self, duration=2000, position=InfoBarPosition.TOP)

    def onPageSizeChanged(self, size):
        self.page_size = int(size)
        self.current_page = 1
        self.loadAccounts()

    def onFirstPage(self):
        self.current_page = 1
        self.loadAccounts()

    def onPrevPage(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.loadAccounts()

    def onNextPage(self):
        self.current_page += 1
        self.loadAccounts()

    def onLastPage(self):
        try:
            _, total_count = JimengIntlAccount.get_accounts_by_page(1, self.page_size)
            total_pages = (total_count + self.page_size - 1) // self.page_size if total_count > 0 else 1
            self.current_page = total_pages
            self.loadAccounts()
        except Exception as e:
            log.error(f"跳转到末页失败: {e}")

    def showContextMenu(self, pos: QPoint):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        account_id = self.table.item(row, 0).data(Qt.UserRole)
        menu = RoundMenu(parent=self)
        delete_action = Action(FIF.DELETE, "删除", self)
        delete_action.triggered.connect(lambda: self.onDelete(account_id))
        menu.addAction(delete_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    # 登录功能按需求未提供，右键仅支持删除

    def onDelete(self, account_id: int):
        try:
            from qfluentwidgets import MessageBox
            w = MessageBox("确认删除", "确定要删除这个账号吗？", self)
            if w.exec():
                if JimengIntlAccount.delete_account(account_id):
                    InfoBar.success(title="删除成功", content="账号已删除", parent=self, duration=2000, position=InfoBarPosition.TOP)
                    self.loadAccounts()
                else:
                    InfoBar.error(title="删除失败", content="账号不存在", parent=self, position=InfoBarPosition.TOP)
        except Exception as e:
            log.error(f"删除国际版账号失败: {e}")
            InfoBar.error(title="删除失败", content=str(e), parent=self, position=InfoBarPosition.TOP)

    def onDeleteAll(self):
        try:
            from qfluentwidgets import MessageBox
            w = MessageBox("确认删除全部", "确定要删除所有账号吗？此操作不可恢复", self)
            if w.exec():
                count = JimengIntlAccount.delete_all()
                InfoBar.success(title="删除完成", content=f"已删除 {count} 个账号", parent=self, duration=3000, position=InfoBarPosition.TOP)
                self.current_page = 1
                self.loadAccounts()
        except Exception as e:
            log.error(f"删除全部国际版账号失败: {e}")
            InfoBar.error(title="删除失败", content=str(e), parent=self, position=InfoBarPosition.TOP)
