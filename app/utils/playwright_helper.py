# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from app.utils.logger import log
from typing import Optional
import os


class PlaywrightHelper:
    """Playwright 浏览器助手"""

    def __init__(self, headless: bool = False, user_data_dir: Optional[str] = None):
        """
        初始化 Playwright 助手

        Args:
            headless: 是否无头模式
            user_data_dir: 用户数据目录（用于保存cookies等）
        """
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """上下文管理器进入"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

    def start(self):
        """启动浏览器"""
        try:
            log.info("启动 Playwright 浏览器...")
            self.playwright = sync_playwright().start()

            # 启动 Chromium 浏览器
            if self.user_data_dir:
                # 使用持久化上下文（保存cookies）
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            else:
                # 普通模式
                self.browser = self.playwright.chromium.launch(
                    headless=self.headless
                )
                self.context = self.browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                self.page = self.context.new_page()

            log.info("浏览器启动成功")

        except Exception as e:
            log.error(f"启动浏览器失败: {e}")
            raise

    def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            log.info("浏览器已关闭")
        except Exception as e:
            log.error(f"关闭浏览器失败: {e}")

    def goto(self, url: str, wait_until: str = "domcontentloaded"):
        """
        访问URL

        Args:
            url: 目标URL
            wait_until: 等待条件 (load, domcontentloaded, networkidle)
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        log.info(f"访问URL: {url}")
        self.page.goto(url, wait_until=wait_until)

    def get_cookies(self) -> list:
        """获取cookies"""
        if not self.context:
            raise RuntimeError("浏览器未启动")
        return self.context.cookies()

    def set_cookies(self, cookies: list):
        """设置cookies"""
        if not self.context:
            raise RuntimeError("浏览器未启动")
        self.context.add_cookies(cookies)

    def wait_for_selector(self, selector: str, timeout: int = 30000):
        """
        等待元素出现

        Args:
            selector: CSS选择器
            timeout: 超时时间（毫秒）
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")
        self.page.wait_for_selector(selector, timeout=timeout)

    def click(self, selector: str):
        """点击元素"""
        if not self.page:
            raise RuntimeError("浏览器未启动")
        self.page.click(selector)

    def fill(self, selector: str, value: str):
        """填充表单"""
        if not self.page:
            raise RuntimeError("浏览器未启动")
        self.page.fill(selector, value)

    def get_text(self, selector: str) -> str:
        """获取元素文本"""
        if not self.page:
            raise RuntimeError("浏览器未启动")
        return self.page.text_content(selector) or ""

    def screenshot(self, path: str):
        """截图"""
        if not self.page:
            raise RuntimeError("浏览器未启动")
        self.page.screenshot(path=path)
        log.info(f"截图已保存: {path}")