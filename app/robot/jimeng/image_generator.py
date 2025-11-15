# -*- coding: utf-8 -*-
"""
即梦图片生成机器人
使用 Playwright 自动化生成图片
"""
import json
import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.models.jimeng_account import JimengAccount
from app.robot.robot_base_result import RobotBaseResult
from app.robot.jimeng.jimeng_image_result import JimengImageResultData
from app.utils.logger import log


class JimengImageRobot:
    """即梦图片生成机器人"""

    # 即梦图片生成页面URL
    IMAGE_GEN_URL = "https://jimeng.jianying.com/ai-tool/generate?type=image"

    # 图片 4.0 模型的比例选项映射（包含"智能"，共9个选项）
    ASPECT_RATIO_MAP_V4 = {
        "智能": "",
        "auto": "",
        "21:9": "21:9",
        "16:9": "16:9",
        "3:2": "3:2",
        "4:3": "4:3",
        "1:1": "1:1",
        "3:4": "3:4",
        "2:3": "2:3",
        "9:16": "9:16"
    }

    # 图片 4.0 模型的索引映射（0-8）
    ASPECT_RATIO_INDEX_MAP_V4 = {
        0: "",      # 智能
        1: "21:9",
        2: "16:9",
        3: "3:2",
        4: "4:3",
        5: "1:1",
        6: "3:4",
        7: "2:3",
        8: "9:16"
    }

    # 其他模型的比例选项映射（不含"智能"，共8个选项）
    ASPECT_RATIO_MAP_OTHER = {
        "21:9": "21:9",
        "16:9": "16:9",
        "3:2": "3:2",
        "4:3": "4:3",
        "1:1": "1:1",
        "3:4": "3:4",
        "2:3": "2:3",
        "9:16": "9:16"
    }

    # 其他模型的索引映射（0-7）
    ASPECT_RATIO_INDEX_MAP_OTHER = {
        0: "21:9",
        1: "16:9",
        2: "3:2",
        3: "4:3",
        4: "1:1",
        5: "3:4",
        6: "2:3",
        7: "9:16"
    }

    # 模型选项索引映射（索引 -> 模型名称）
    IMAGE_MODEL_INDEX_MAP = {
        0: "图片 4.0",
        1: "图片 3.5",
        2: "Flux 1.1 Pro Ultra",
        3: "Flux 1.1 Pro",
        4: "Flux Pro"
    }

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
        self.current_model: str = ""  # 当前选择的模型

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

            # 创建浏览器上下文（不设置viewport，使用默认大小）
            self.context = await self.browser.new_context(
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

    async def get_updated_cookies(self) -> str:
        """
        获取当前浏览器的最新Cookie

        Returns:
            str: Cookie字符串
        """
        try:
            if not self.context:
                log.warning("浏览器上下文不存在，无法获取Cookie")
                return ""

            # 获取所有Cookie
            cookies = await self.context.cookies()

            if not cookies:
                log.warning("未获取到Cookie")
                return ""

            # 转换为 "key=value; key=value" 格式
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            log.info(f"成功获取最新Cookie，共 {len(cookies)} 个")
            return cookie_str

        except Exception as e:
            log.error(f"获取Cookie失败: {str(e)}")
            return ""

    async def _select_image_model(self, image_model: str) -> bool:
        """
        选择图片生成模型

        Args:
            image_model: 模型名称（如：图片 4.0）或索引（0-4）

        Returns:
            bool: 是否选择成功
        """
        if not image_model:
            return True

        log.info(f"选择模型: {image_model}")
        try:
            # 如果传入的是数字字符串，转换为模型名称
            model_name = image_model
            if image_model.isdigit():
                index = int(image_model)
                model_name = self.IMAGE_MODEL_INDEX_MAP.get(index)
                if model_name is None:
                    log.warning(f"无效的模型索引: {index}")
                    return False
                log.info(f"使用索引 {index} 对应的模型: {model_name}")

            # 点击模型选择下拉框（第二个 combobox，包含模型图标的那个）
            # 使用更精确的选择器：包含 SVG path 中特定图标的 combobox
            model_selector = await self.page.query_selector('div[role="combobox"]:has(svg path[d*="M13.25 2.682"])')

            if model_selector:
                await model_selector.click()
                log.info("已点击模型选择器")
                await asyncio.sleep(1)

                # 在弹出的选项中查找对应的模型
                # 使用文本内容匹配
                model_option = await self.page.query_selector(f'li[role="option"]:has-text("{model_name}")')

                if model_option:
                    await model_option.click()
                    log.info(f"已选择模型: {model_name}")
                    # 保存当前模型
                    self.current_model = model_name
                    await asyncio.sleep(1)
                    return True
                else:
                    log.warning(f"未找到模型选项: {model_name}")
                    return False
            else:
                log.warning("未找到模型选择器")
                return False
        except Exception as e:
            log.error(f"选择模型失败: {str(e)}")
            return False

    def _is_v4_model(self) -> bool:
        """
        判断当前是否为图片 4.0 模型

        Returns:
            bool: 是否为4.0模型
        """
        return "4.0" in self.current_model or "4.O" in self.current_model.upper()

    async def _select_aspect_ratio(self, aspect_ratio: str) -> bool:
        """
        选择图片比例

        Args:
            aspect_ratio: 比例值（如：16:9, 1:1, 智能等）
                         也可以使用索引（如：0-8 for v4, 0-7 for others）

        Returns:
            bool: 是否选择成功
        """
        if not aspect_ratio:
            return True

        log.info(f"选择比例: {aspect_ratio}")
        try:
            # 根据当前模型选择对应的映射表
            is_v4 = self._is_v4_model()
            aspect_map = self.ASPECT_RATIO_MAP_V4 if is_v4 else self.ASPECT_RATIO_MAP_OTHER
            index_map = self.ASPECT_RATIO_INDEX_MAP_V4 if is_v4 else self.ASPECT_RATIO_INDEX_MAP_OTHER

            log.info(f"当前模型: {self.current_model}, 使用{'V4' if is_v4 else '其他'}模型的比例映射")

            # 如果传入的是数字字符串，转换为索引
            if aspect_ratio.isdigit():
                index = int(aspect_ratio)
                ratio_value = index_map.get(index)
                if ratio_value is None:
                    log.warning(f"无效的比例索引: {index}")
                    return False
                log.info(f"使用索引 {index} 对应的比例值: {ratio_value if ratio_value else '智能'}")
            else:
                # 否则使用名称映射查找value
                ratio_value = aspect_map.get(aspect_ratio, aspect_ratio)
                # 如果在非V4模型中使用了"智能"选项，给出警告
                if not is_v4 and aspect_ratio in ["智能", "auto"]:
                    log.warning(f"当前模型 {self.current_model} 不支持'智能'选项，将使用默认比例")
                    return False

            # 查找包含 radio-group 的容器（第一个 radiogroup 是比例选择）
            ratio_radio = await self.page.query_selector(
                f'div[role="radiogroup"] label.lv-radio input[type="radio"][value="{ratio_value}"]'
            )

            if ratio_radio:
                await ratio_radio.click()
                log.info(f"已选择比例: {aspect_ratio}")
                await asyncio.sleep(0.5)
                return True
            else:
                log.warning(f"未找到比例选项: {aspect_ratio}")
                return False
        except Exception as e:
            log.error(f"选择比例失败: {str(e)}")
            return False

    async def _select_resolution(self, resolution: str) -> bool:
        """
        选择图片分辨率

        Args:
            resolution: 分辨率值（如：2K, 4K）

        Returns:
            bool: 是否选择成功
        """
        if not resolution:
            return True

        log.info(f"选择分辨率: {resolution}")
        try:
            # 查找分辨率 radio group（包含 resolution-radio-group 类名）
            resolution_value = resolution.lower()  # 转换为小写（2k 或 4k）
            resolution_radio = await self.page.query_selector(f'div.resolution-radio-group-KRnjKo label.lv-radio input[type="radio"][value="{resolution_value}"]')

            if resolution_radio:
                await resolution_radio.click()
                log.info(f"已选择分辨率: {resolution}")
                await asyncio.sleep(0.5)
                return True
            else:
                log.warning(f"未找到分辨率选项: {resolution}")
                return False
        except Exception as e:
            log.error(f"选择分辨率失败: {str(e)}")
            return False

    async def _open_settings_panel(self) -> bool:
        """
        打开比例和分辨率设置面板

        Returns:
            bool: 是否打开成功
        """
        try:
            # 查找包含比例和分辨率信息的按钮（在 toolbar-settings 容器中，包含 button-text 的按钮）
            settings_button = await self.page.query_selector('div.toolbar-settings-xxo_Ok button.button-wtoV7J:has(span.button-text-JXxV0g)')

            if settings_button:
                await settings_button.click()
                log.info("已点击比例/分辨率设置按钮")
                await asyncio.sleep(1)
                return True
            else:
                log.warning("未找到比例/分辨率设置按钮")
                return False
        except Exception as e:
            log.error(f"打开设置面板失败: {str(e)}")
            return False

    async def _close_settings_panel(self):
        """
        关闭设置面板
        """
        try:
            # 关闭设置面板（按 ESC 键）
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(0.5)
            log.info("已关闭设置面板")
        except Exception as e:
            log.error(f"关闭设置面板失败: {str(e)}")

    async def _upload_reference_images(self, input_image_paths: list) -> bool:
        """
        上传参考图片

        Args:
            input_image_paths: 参考图片路径列表

        Returns:
            bool: 是否上传成功
        """
        if not input_image_paths:
            return True

        log.info(f"开始上传 {len(input_image_paths)} 张参考图片")
        try:
            # 等待文件上传input出现（不要求可见，因为input是hidden的）
            await self.page.wait_for_selector('input[type="file"][accept*="image"]', state='attached', timeout=5000)

            # 查找文件上传input（即使是隐藏的也可以操作）
            file_input = await self.page.query_selector('input[type="file"][accept*="image"]')

            if file_input:
                # 上传所有参考图片（即使input是hidden也可以set_input_files）
                await file_input.set_input_files(input_image_paths)
                log.info(f"已上传 {len(input_image_paths)} 张参考图片")

                # 等待图片上传完成（根据图片数量调整等待时间）
                wait_time = max(2, len(input_image_paths) * 1)
                await asyncio.sleep(wait_time)
                return True
            else:
                log.warning("未找到文件上传控件")
                return False
        except asyncio.TimeoutError:
            log.error("等待文件上传控件超时")
            return False
        except Exception as e:
            log.error(f"上传参考图片失败: {str(e)}")
            return False

    async def _input_prompt(self, prompt: str) -> bool:
        """
        输入提示词

        Args:
            prompt: 提示词内容

        Returns:
            bool: 是否输入成功
        """
        log.info("输入提示词")
        try:
            # 查找输入框（textarea）
            textarea = await self.page.query_selector('textarea')

            if textarea:
                # 清空现有内容
                await textarea.fill('')
                # 输入新的提示词
                await textarea.fill(prompt)
                log.info("提示词已输入")
                await asyncio.sleep(1)
                return True
            else:
                raise Exception("未找到提示词输入框")
        except Exception as e:
            log.error(f"输入提示词失败: {str(e)}")
            return False

    async def _click_generate_button(self) -> bool:
        """
        点击生成按钮

        Returns:
            bool: 是否点击成功
        """
        log.info("点击生成按钮")
        try:
            # 查找生成按钮（通常包含"生成"文字）
            generate_button = await self.page.query_selector('button:has-text("生成")')

            if generate_button:
                await generate_button.click()
                log.info("已点击生成按钮")
                await asyncio.sleep(2)
                return True
            else:
                raise Exception("未找到生成按钮")
        except Exception as e:
            log.error(f"点击生成按钮失败: {str(e)}")
            return False

    async def _wait_for_generation_complete(self) -> bool:
        """
        等待图片生成完成

        Returns:
            bool: 是否生成成功
        """
        log.info("等待图片生成...")
        try:
            # 等待结果图片加载（超时60秒）
            # 结果图片通常在特定的容器中，使用img标签
            await self.page.wait_for_selector('img[src*="dreamina"]', timeout=60000)
            log.info("图片生成完成")
            await asyncio.sleep(2)
            return True
        except Exception as e:
            log.error(f"等待图片生成超时: {str(e)}")
            return False

    async def _get_generated_image_urls(self) -> list:
        """
        获取生成的图片URL列表

        Returns:
            list: 图片URL列表
        """
        log.info("获取生成的图片URL")
        try:
            # 获取所有图片元素，筛选出结果图片
            images = await self.page.query_selector_all('img[src*="dreamina"]')

            image_urls = []
            for img in images:
                src = await img.get_attribute('src')
                if src and 'dreamina' in src:
                    image_urls.append(src)

            # 去重
            image_urls = list(set(image_urls))

            log.info(f"获取到 {len(image_urls)} 张图片URL")

            if not image_urls:
                raise Exception("未能获取到图片URL")

            return image_urls

        except Exception as e:
            log.error(f"获取图片URL失败: {str(e)}")
            raise

    async def generate_image(self, prompt: str, **kwargs) -> RobotBaseResult:
        """
        生成图片

        Args:
            prompt: 图片提示词
            **kwargs: 其他参数
                - image_model: 图片模型（如：图片 4.0）
                - aspect_ratio: 分辨率比例
                - resolution: 分辨率
                - input_image_paths: 参考图片路径列表

        Returns:
            RobotBaseResult: 生成结果
                - code: 状态码（0成功，-1失败）
                - message: 消息
                - data: JimengImageResultData对象
        """
        try:
            log.info(f"开始生成图片: {prompt}")

            image_model = kwargs.get('image_model', '')
            input_image_paths = kwargs.get('input_image_paths', [])
            aspect_ratio = kwargs.get('aspect_ratio', '')
            resolution = kwargs.get('resolution', '')

            log.info(f"image_model: {image_model}")
            log.info(f"input_image_paths: {input_image_paths}")
            log.info(f"aspect_ratio: {aspect_ratio}")
            log.info(f"resolution: {resolution}")

            # 1. 选择模型
            await self._select_image_model(image_model)

            # 2. 上传参考图片
            await self._upload_reference_images(input_image_paths)

            # 3. 输入提示词
            if not await self._input_prompt(prompt):
                raise Exception("输入提示词失败")

            # 4. 设置比例和分辨率
            if aspect_ratio or resolution:
                # 打开设置面板
                if await self._open_settings_panel():
                    # 选择比例
                    await self._select_aspect_ratio(aspect_ratio)
                    # 选择分辨率
                    await self._select_resolution(resolution)
                    # 关闭设置面板
                    await self._close_settings_panel()

            # 5. 点击生成按钮
            if not await self._click_generate_button():
                raise Exception("点击生成按钮失败")

            # 6. 等待生成完成
            if not await self._wait_for_generation_complete():
                raise Exception("图片生成超时，可能生成失败")

            # 7. 获取生成的图片URL
            image_urls = await self._get_generated_image_urls()

            # 8. 获取更新后的Cookie
            updated_cookies = await self.get_updated_cookies()

            # 9. 返回成功结果
            result_data = JimengImageResultData(
                jimeng_task_id="",  # 即梦没有返回任务ID，留空
                image_urls=image_urls,
                cookies=updated_cookies
            )

            return RobotBaseResult.success(
                message=f"生成成功，共 {len(image_urls)} 张图片",
                data=result_data.to_dict()
            )

        except Exception as e:
            error_msg = f"生成图片失败: {str(e)}"
            log.error(error_msg)

            # 即使失败也尝试获取Cookie
            try:
                updated_cookies = await self.get_updated_cookies()
            except:
                updated_cookies = ""

            result_data = JimengImageResultData(
                jimeng_task_id="",
                image_urls=[],
                cookies=updated_cookies
            )

            return RobotBaseResult.error(
                message=error_msg,
                data=result_data.to_dict()
            )

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
) -> RobotBaseResult:
    """
    使用指定账号生成图片

    Args:
        account_id: 账号ID
        prompt: 图片提示词
        headless: 是否无头模式
        **kwargs: 其他参数

    Returns:
        RobotBaseResult: 生成结果
    """
    robot = JimengImageRobot(account_id)

    try:
        # 初始化
        if not await robot.init():
            result_data = JimengImageResultData()
            return RobotBaseResult.error(
                message='初始化机器人失败',
                data=result_data.to_dict()
            )

        # 启动浏览器
        if not await robot.launch_browser(headless=headless):
            result_data = JimengImageResultData()
            return RobotBaseResult.error(
                message='启动浏览器失败',
                data=result_data.to_dict()
            )

        # 打开页面
        if not await robot.navigate_to_image_gen():
            result_data = JimengImageResultData()
            return RobotBaseResult.error(
                message='打开页面失败',
                data=result_data.to_dict()
            )

        # 生成图片
        result = await robot.generate_image(prompt, **kwargs)

        return result

    except Exception as e:
        log.error(f"生成图片异常: {str(e)}")
        result_data = JimengImageResultData()
        return RobotBaseResult.error(
            message=str(e),
            data=result_data.to_dict()
        )

    finally:
        await robot.close()
