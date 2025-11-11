# -*- coding: utf-8 -*-
import os
import sys
import platform
import traceback

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 设置Qt插件路径（解决跨平台问题）
lib_folder = "Lib" if platform.system() == "Windows" else "lib"
plugin_path = os.path.join(
    sys.prefix, lib_folder, "site-packages", "PyQt5", "Qt5", "plugins"
)
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentIcon as FIF, NavigationItemPosition, MSFluentWindow, setTheme, Theme
from app.view.home_interface import HomeInterface
from app.view.jimeng_interface import JiMengInterface
from app.view.jimeng_intl_interface import JiMengIntlInterface
from app.view.keling_interface import KeLingInterface
from app.view.qingying_interface import QingYingInterface
from app.view.vidu_interface import ViduInterface
from app.view.hailuo_interface import HaiLuoInterface
from app.view.runway_interface import RunwayInterface
from app.view.settings_interface import SettingsInterface
from app.database.init_db import init_database, close_database
from app.utils.logger import log


class VideoRobotWindow(MSFluentWindow):
    """视频机器人主窗口"""

    def __init__(self):
        super().__init__()
        self.initWindow()
        self.initNavigation()

        # 启动全局任务管理器
        self.initTaskManager()

        # 自定义导航栏样式，增大图标
        self.setStyleSheet("""
            NavigationInterface {
                icon-size: 24px;
            }
            NavigationTreeWidget {
                icon-size: 24px;
            }
        """)

        # 监听导航栏切换事件
        self.stackedWidget.currentChanged.connect(self.onNavigationChanged)

    def initTaskManager(self):
        """初始化并启动任务管理器"""
        from app.managers.global_task_manager import get_global_task_manager

        self.task_manager = get_global_task_manager()

        # 设置默认参数
        self.task_manager.set_max_workers(3)
        self.task_manager.set_poll_interval(5)

        # 启动任务管理器
        self.task_manager.start()

        log.info("全局任务管理器已自动启动")

    def onNavigationChanged(self, index):
        """主导航切换事件处理"""
        current_widget = self.stackedWidget.widget(index)

        # 如果切换离开即梦界面，通知即梦界面的账号管理关闭浏览器
        if current_widget != self.jimengInterface:
            if hasattr(self.jimengInterface, 'accountManageView'):
                if hasattr(self.jimengInterface.accountManageView, 'closeLoginWindow'):
                    self.jimengInterface.accountManageView.closeLoginWindow()

    def initWindow(self):
        """初始化窗口"""
        self.resize(1200, 800)
        self.setWindowTitle("视频机器人")

        # 设置应用图标
        icon_path = os.path.join(project_root, "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            log.info(f"应用图标已设置: {icon_path}")
        else:
            log.warning(f"应用图标文件不存在: {icon_path}")

        # 居中显示
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def initNavigation(self):
        """初始化导航栏"""
        # 创建页面实例
        self.homeInterface = HomeInterface(self)
        self.jimengInterface = JiMengInterface(self)
        self.jimengIntlInterface = JiMengIntlInterface(self)
        self.kelingInterface = KeLingInterface(self)
        self.qingyingInterface = QingYingInterface(self)
        self.viduInterface = ViduInterface(self)
        self.hailuoInterface = HaiLuoInterface(self)
        self.runwayInterface = RunwayInterface(self)
        self.settingsInterface = SettingsInterface(self)

        # 添加顶部导航项
        self.addSubInterface(self.homeInterface, FIF.HOME, "首页")

        # 即梦图标 - 使用自定义图标
        jimeng_icon_path = os.path.join(project_root, "app", "assets", "jimeng_icon.png")
        if os.path.exists(jimeng_icon_path):
            jimeng_icon = QIcon(jimeng_icon_path)
        else:
            jimeng_icon = FIF.VIDEO
        self.addSubInterface(self.jimengInterface, jimeng_icon, "即梦")
        # 即梦国际版 - 复用即梦图标
        self.addSubInterface(self.jimengIntlInterface, jimeng_icon, "即梦国际版")

        # 可灵图标
        keling_icon_path = os.path.join(project_root, "app", "assets", "keling_icon.png")
        if os.path.exists(keling_icon_path):
            keling_icon = QIcon(keling_icon_path)
        else:
            keling_icon = FIF.VIDEO
        self.addSubInterface(self.kelingInterface, keling_icon, "可灵")

        # 清影图标
        qingying_icon_path = os.path.join(project_root, "app", "assets", "qingying_icon.png")
        if os.path.exists(qingying_icon_path):
            qingying_icon = QIcon(qingying_icon_path)
        else:
            qingying_icon = FIF.VIDEO
        self.addSubInterface(self.qingyingInterface, qingying_icon, "清影")

        # Vidu图标
        vidu_icon_path = os.path.join(project_root, "app", "assets", "vidu_icon.svg")
        if os.path.exists(vidu_icon_path):
            vidu_icon = QIcon(vidu_icon_path)
        else:
            vidu_icon = FIF.VIDEO
        self.addSubInterface(self.viduInterface, vidu_icon, "Vidu")

        # 海螺图标
        hailuo_icon_path = os.path.join(project_root, "app", "assets", "hailuo_icon.png")
        if os.path.exists(hailuo_icon_path):
            hailuo_icon = QIcon(hailuo_icon_path)
        else:
            hailuo_icon = FIF.VIDEO
        self.addSubInterface(self.hailuoInterface, hailuo_icon, "海螺")

        # Runway图标
        runway_icon_path = os.path.join(project_root, "app", "assets", "runway_icon.png")
        if os.path.exists(runway_icon_path):
            runway_icon = QIcon(runway_icon_path)
        else:
            runway_icon = FIF.VIDEO
        self.addSubInterface(self.runwayInterface, runway_icon, "Runway")

        # 添加底部设置项
        self.addSubInterface(self.settingsInterface, FIF.SETTING, "设置")


def exception_hook(exctype, value, tb):
    """全局异常处理"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    log.error(f"未捕获的异常:\n{error_msg}")
    sys.__excepthook__(exctype, value, tb)


def check_for_updates(parent=None):
    """检查更新"""
    try:
        from app.utils.update_manager import get_update_manager
        from app.view.update_dialog import UpdateDialog

        log.info("开始检查更新...")

        # TODO: 替换为你的 GitHub 仓库信息
        manager = get_update_manager(
            repo_owner="YOUR_GITHUB_USERNAME",
            repo_name="YOUR_REPO_NAME"
        )

        update_checker = manager.check_for_updates()

        if not update_checker:
            log.warning("无法启动更新检查")
            return

        # 连接信号
        def on_update_available(update_info):
            log.info(f"发现新版本: {update_info.get('version')}")
            # 显示更新对话框
            dialog = UpdateDialog(update_info, parent)
            dialog.exec_()

        def on_no_update():
            log.info("当前已是最新版本")

        def on_error(error_msg):
            log.error(f"检查更新出错: {error_msg}")

        update_checker.update_available.connect(on_update_available)
        update_checker.no_update.connect(on_no_update)
        update_checker.error_occurred.connect(on_error)

        # 启动检查
        update_checker.start()

    except Exception as e:
        log.error(f"检查更新功能异常: {str(e)}")


def init_app_with_splash(splash, app):
    """带启动界面的初始化"""
    from PyQt5.QtCore import QTimer

    def do_init():
        try:
            # 步骤1: 检查日志目录
            splash.update_progress(20, "检查日志目录...")
            from app.utils.path_helper import get_logs_dir
            log_dir = get_logs_dir()
            log.info(f"日志目录: {log_dir}")

            QTimer.singleShot(100, step2)

        except Exception as e:
            log.error(f"初始化失败: {e}")
            splash.close()

    def step2():
        try:
            # 步骤2: 检查数据库目录
            splash.update_progress(40, "检查数据库目录...")
            from app.utils.path_helper import get_app_data_dir
            data_dir = get_app_data_dir()
            log.info(f"数据目录: {data_dir}")

            QTimer.singleShot(100, step3)

        except Exception as e:
            log.error(f"初始化失败: {e}")
            splash.close()

    def step3():
        try:
            # 步骤3: 初始化数据库
            splash.update_progress(60, "初始化数据库...")
            init_database()

            QTimer.singleShot(100, step4)

        except Exception as e:
            log.error(f"数据库初始化失败: {e}")
            splash.close()

    def step4():
        try:
            # 步骤4: 检查数据库表
            splash.update_progress(80, "检查数据库表...")
            from app.database.db import db
            from app.models.config import Config
            from app.models.jimeng_account import JimengAccount
            from app.models.jimeng_image_task import JimengImageTask

            # 验证表是否存在
            tables = [Config, JimengAccount, JimengImageTask]
            for table in tables:
                table.select().limit(1).execute()

            log.info("数据库表检查完成")

            QTimer.singleShot(100, step5)

        except Exception as e:
            log.error(f"数据库表检查失败: {e}")
            splash.close()

    def step5():
        # 步骤5: 完成初始化
        splash.update_progress(100, "启动完成！")
        log.info("初始化完成")

    # 开始初始化
    QTimer.singleShot(200, do_init)


def main():
    """主函数"""
    log.info("=" * 60)
    log.info("视频机器人启动中...")
    log.info("=" * 60)

    # 设置全局异常处理
    sys.excepthook = exception_hook

    # 启用高DPI缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # 创建应用
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    # 设置应用图标（用于程序坞）
    icon_path = os.path.join(project_root, "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        log.info(f"程序坞图标已设置: {icon_path}")
    else:
        log.warning(f"图标文件不存在: {icon_path}")

    # 设置暗夜模式
    setTheme(Theme.DARK)
    log.info("应用主题设置为暗夜模式")

    # 显示启动界面
    from app.view.splash_screen import SplashScreen
    splash = SplashScreen()
    splash.show()

    # 先初始化数据库（避免主窗口加载数据时出错）
    init_database()

    # 创建主窗口（但不显示）
    window = VideoRobotWindow()

    # 启动界面完成后显示主窗口
    def show_main_window():
        window.show()
        log.info("主窗口已显示")

        # 延迟检查更新(启动后3秒)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(3000, lambda: check_for_updates(window))

    splash.finished.connect(show_main_window)

    # 开始初始化
    init_app_with_splash(splash, app)

    # 运行应用
    log.info("应用运行中...")
    result = app.exec_()

    # 关闭数据库连接
    close_database()

    log.info("视频机器人已退出")
    sys.exit(result)


if __name__ == '__main__':
    main()
