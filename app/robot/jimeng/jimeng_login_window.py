# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from app.utils.logger import log
import time
import threading


class JimengLoginWindow:
    """即梦登录窗口 - 用于打开浏览器并注入cookies"""

    def __init__(self, cookies: str):
        """
        初始化登录窗口

        Args:
            cookies: Cookie字符串，格式为 "name1=value1; name2=value2"
        """
        self.cookies = cookies
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_closed = False
        self._close_lock = threading.Lock()

    def open(self):
        """打开浏览器窗口并注入cookies"""
        try:
            log.info("启动即梦登录窗口...")

            # 启动 Playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 解析并注入cookies
            if self.cookies:
                cookies_list = self._parse_cookies(self.cookies)
                self.context.add_cookies(cookies_list)
                log.info(f"已注入 {len(cookies_list)} 个cookies")

            # 创建页面并立即监听关闭事件
            self.page = self.context.new_page()
            self.page.on("close", self._on_page_close)

            # 打开即梦页面
            log.info("打开即梦页面...")
            try:
                self.page.goto("https://jimeng.jianying.com/ai-tool/home", wait_until="networkidle")
                log.info("即梦页面已打开")
            except Exception as goto_error:
                # 如果是因为页面被关闭导致的错误，说明用户主动关闭了
                if "has been closed" in str(goto_error):
                    log.info("页面加载过程中被用户关闭")
                    return

            # 等待浏览器关闭
            self._wait_for_close()

        except Exception as e:
            # 如果是用户主动关闭，不记录为错误
            if "has been closed" not in str(e):
                log.error(f"打开即梦登录窗口失败: {e}")
        finally:
            self._cleanup()

    def _parse_cookies(self, cookies_str: str) -> list:
        """解析cookie字符串为Playwright格式"""
        cookies_list = []
        if not cookies_str:
            return cookies_list

        # 清理空字节和其他非法字符
        cookies_str = cookies_str.replace('\x00', '').replace('\r', '').replace('\n', '').strip()

        # 分割cookie字符串
        cookie_pairs = cookies_str.split('; ')
        for pair in cookie_pairs:
            if '=' in pair:
                name, value = pair.split('=', 1)
                name = name.strip().replace('\x00', '')
                value = value.strip().replace('\x00', '')

                if name and value:
                    cookies_list.append({
                        'name': name,
                        'value': value,
                        'domain': '.jianying.com',
                        'path': '/',
                    })

        return cookies_list

    def _on_page_close(self):
        """页面关闭事件处理"""
        log.info("检测到页面被关闭")
        self.is_closed = True

    def _wait_for_close(self):
        """等待用户关闭浏览器"""
        log.info("浏览器已打开，等待关闭...")
        while not self.is_closed:
            time.sleep(0.1)
            # 检查浏览器是否还在运行
            try:
                if self.browser and not self.browser.is_connected():
                    log.info("检测到浏览器断开连接")
                    break
            except:
                break

        log.info("浏览器已关闭")

    def close(self):
        """关闭浏览器"""
        with self._close_lock:
            if self.is_closed:
                return

            log.info("强制关闭浏览器...")
            self.is_closed = True

            # 强制关闭
            self._cleanup()

    def _cleanup(self):
        """清理资源"""
        try:
            # 按顺序关闭所有资源
            if self.page:
                try:
                    self.page.close()
                except:
                    pass

            if self.context:
                try:
                    self.context.close()
                except:
                    pass

            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass

            if self.playwright:
                try:
                    self.playwright.stop()
                except:
                    pass

            # 清空引用
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

            log.info("浏览器资源已清理")
        except Exception as e:
            log.error(f"清理资源时出错: {e}")


def open_jimeng_window(cookies: str):
    """
    打开即梦登录窗口的便捷函数

    Args:
        cookies: Cookie字符串
    """
    window = JimengLoginWindow(cookies)
    window.open()
