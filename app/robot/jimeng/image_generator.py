# -*- coding: utf-8 -*-
"""
即梦图片生成机器人
使用 Playwright 自动化生成图片
"""
import json
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.models.jimeng_account import JimengAccount
from app.utils.logger import log


class JimengImageRobot:
    """即梦图片生成机器人"""

    # 即梦图片生成页面URL
    IMAGE_GEN_URL = "https://jimeng.jianying.com/ai-tool/generate?type=image"

    def __init__(self, account_id: int):
        """
        初始化机器人

        Args:
            account_id: 账号ID
        """
        self.account_id = account_id
        self.account = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def init(self):
        """初始化机器人,加载账号信息"""
        try:
            # 从数据库加载账号
            self.account = JimengAccount.get_account_by_id(self.account_id)

            if not self.account:
                raise Exception(f"账号不存在: ID={self.account_id}")

            log.info(f"加载账号成功: {self.account.nickname} (ID: {self.account_id})")

            return True

        except Exception as e:
            log.error(f"初始化机器人失败: {str(e)}")
            return False

    def _parse_cookies(self) -> list:
        """
        解析 Cookie 字符串为 Playwright 格式

        Returns:
            list: Cookie列表
        """
        try:
            cookies = []

            # Cookie 格式: "key1=value1; key2=value2"
            cookie_str = self.account.cookies.strip()

            if not cookie_str:
                log.warning("Cookie 为空")
                return []

            # 如果是 JSON 格式
            if cookie_str.startswith('['):
                try:
                    cookies = json.loads(cookie_str)
                    log.info(f"解析 JSON 格式 Cookie 成功: {len(cookies)} 个")
                    return cookies
                except:
                    pass

            # 解析普通格式 "key=value; key=value"
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookies.append({
                        'name': key.strip(),
                        'value': value.strip(),
                        'domain': '.jianying.com',
                        'path': '/'
                    })

            log.info(f"解析 Cookie 成功: {len(cookies)} 个")
            return cookies

        except Exception as e:
            log.error(f"解析 Cookie 失败: {str(e)}")
            return []

    async def launch_browser(self, headless: bool = False):
        """
        启动浏览器

        Args:
            headless: 是否无头模式
        """
        try:
            log.info(f"启动浏览器... (headless={headless})")

            playwright = await async_playwright().start()

            # 启动浏览器
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )

            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # 添加 Cookie
            cookies = self._parse_cookies()
            if cookies:
                await self.context.add_cookies(cookies)
                log.info(f"已添加 {len(cookies)} 个 Cookie")

            # 创建新页面
            self.page = await self.context.new_page()

            log.info("浏览器启动成功")

            return True

        except Exception as e:
            log.error(f"启动浏览器失败: {str(e)}")
            return False

    async def navigate_to_image_gen(self):
        """导航到图片生成页面"""
        try:
            log.info(f"正在打开页面: {self.IMAGE_GEN_URL}")

            # 访问页面
            response = await self.page.goto(
                self.IMAGE_GEN_URL,
                wait_until='networkidle',
                timeout=30000
            )

            if response.status != 200:
                log.warning(f"页面响应状态码: {response.status}")

            # 等待页面加载完成
            await asyncio.sleep(2)

            # 获取当前URL
            current_url = self.page.url
            log.info(f"当前页面URL: {current_url}")

            # 检查是否需要登录
            if 'login' in current_url.lower():
                log.error("需要登录,Cookie可能已失效")
                return False

            log.info("页面加载成功")
            return True

        except Exception as e:
            log.error(f"导航到页面失败: {str(e)}")
            return False

    async def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成图片

        Args:
            prompt: 图片提示词
            **kwargs: 其他参数
                - image_count: 生成数量 (默认1)
                - width: 图片宽度
                - height: 图片高度
                - style: 图片风格

        Returns:
            Dict: 生成结果
                - success: 是否成功
                - message: 消息
                - images: 图片URL列表
        """
        try:
            log.info(f"开始生成图片: {prompt}")

            # TODO: 这里需要根据即梦的实际页面结构填写
            # 1. 输入提示词
            # 2. 设置参数
            # 3. 点击生成按钮
            # 4. 等待生成完成
            # 5. 获取图片URL

            # 示例代码框架:
            """
            # 输入提示词
            await self.page.fill('textarea[placeholder="请输入提示词"]', prompt)

            # 点击生成按钮
            await self.page.click('button:has-text("生成")')

            # 等待生成完成
            await self.page.wait_for_selector('.result-image', timeout=60000)

            # 获取图片URL
            images = await self.page.eval_on_selector_all(
                '.result-image img',
                'elements => elements.map(e => e.src)'
            )
            """

            # 暂时返回示例结果
            log.warning("图片生成逻辑待实现,请根据实际页面结构完善")

            return {
                'success': False,
                'message': '图片生成逻辑待实现',
                'images': []
            }

        except Exception as e:
            error_msg = f"生成图片失败: {str(e)}"
            log.error(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'images': []
            }

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            log.info("浏览器已关闭")

        except Exception as e:
            log.error(f"关闭浏览器失败: {str(e)}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


# 便捷函数
async def generate_image_with_account(
    account_id: int,
    prompt: str,
    headless: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    使用指定账号生成图片

    Args:
        account_id: 账号ID
        prompt: 图片提示词
        headless: 是否无头模式
        **kwargs: 其他参数

    Returns:
        Dict: 生成结果
    """
    robot = JimengImageRobot(account_id)

    try:
        # 初始化
        if not await robot.init():
            return {
                'success': False,
                'message': '初始化机器人失败',
                'images': []
            }

        # 启动浏览器
        if not await robot.launch_browser(headless=headless):
            return {
                'success': False,
                'message': '启动浏览器失败',
                'images': []
            }

        # 打开页面
        if not await robot.navigate_to_image_gen():
            return {
                'success': False,
                'message': '打开页面失败',
                'images': []
            }

        # 生成图片
        result = await robot.generate_image(prompt, **kwargs)

        return result

    except Exception as e:
        log.error(f"生成图片异常: {str(e)}")
        return {
            'success': False,
            'message': str(e),
            'images': []
        }

    finally:
        await robot.close()
