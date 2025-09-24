"""
即梦平台自动化模块 - 文本生成图片
based on BaseTaskExecutor refactoring version
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from backend.utils.base_task_executor import BaseTaskExecutor, TaskResult, ErrorCode, TaskLogger

class JimengText2ImageExecutor(BaseTaskExecutor):
    """即梦文本生成图片执行器"""
    
    def __init__(self, headless: bool = False):
        super().__init__(headless)
        self.task_id = None
        self.image_urls = []
        self.generation_completed = False
    
    async def handle_cookies(self, cookies: str):
        """处理cookies字符串格式"""
        try:
            # 将cookies字符串转换为字典列表格式
            cookie_pairs = cookies.split('; ')
            cookie_list = []
            for pair in cookie_pairs:
                if '=' in pair:
                    name, value = pair.split('=', 1)
                    cookie_list.append({
                        'name': name.strip(),
                        'value': value.strip(),
                        'domain': '.capcut.com',
                        'path': '/'
                    })
            
            await self.context.add_cookies(cookie_list)
            self.logger.info("即梦平台cookies设置成功")
            
        except Exception as e:
            self.logger.error("设置即梦平台cookies时出错", error=str(e))
    
    async def check_login_status(self) -> TaskResult:
        """检查登录状态，如果有登录按钮说明cookies过期"""
        try:
            self.logger.info("检查登录状态")
            
            # 跳转到主页面
            await self.page.goto('https://dreamina.capcut.com/ai-tool/home/en-us', timeout=60000)
            await self.page.wait_for_load_state('networkidle', timeout=60000)
            await asyncio.sleep(3)
            
            # 检查是否存在登录按钮
            login_button = await self.page.query_selector('div[class*="login-button"]:has-text("Sign in")')
            if login_button:
                self.logger.warning("检测到登录按钮，cookies已过期")
                return TaskResult(
                    code=600,
                    data=None,
                    message="cookies已过期，需要重新登录",
                    cookies=""
                )
            
            self.logger.info("登录状态正常")
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="登录状态正常")
            
        except Exception as e:
            self.logger.error("检查登录状态时出错", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="检查登录状态失败",
                error_details={"error": str(e)}
            )
            
    async def perform_login(self, username: str, password: str) -> TaskResult:
        """执行登录流程"""
        try:
            self.logger.info("开始登录即梦平台", username=username)
            
            await self.page.goto('https://dreamina.capcut.com/en-us', timeout=60000)
            await asyncio.sleep(2)
            
            # 点击语言切换按钮
            self.logger.info("点击语言切换按钮")
            await self.page.click('button.dreamina-header-secondary-button')
            await asyncio.sleep(1)
            
            # 点击切换为英文
            self.logger.info("切换为英文")
            await self.page.click('div.language-item:has-text("English")')
            await asyncio.sleep(2)
            
            # 检查并关闭可能出现的弹窗
            try:
                self.logger.info("检查是否有弹窗需要关闭")
                close_button = await self.page.query_selector('img.close-icon')
                if close_button:
                    self.logger.info("关闭弹窗")
                    await close_button.click()
                    await asyncio.sleep(1)
            except Exception as e:
                self.logger.debug("没有发现需要关闭的弹窗", error=str(e))
            
            # 点击登录按钮
            self.logger.info("点击登录按钮")
            await self.page.click('#loginButton')
            await asyncio.sleep(2)
            
            # 等待登录页面加载
            await self.page.wait_for_selector('.lv-checkbox-mask', timeout=60000)
            await asyncio.sleep(2)
            
            # 勾选同意条款复选框
            self.logger.info("勾选同意条款")
            await self.page.click('.lv-checkbox-mask')
            await asyncio.sleep(2)
            
            # 点击登录按钮
            await self.page.click('div[class^="login-button-"]:has-text("Sign in")')
            await asyncio.sleep(2)
            
            # 点击使用邮箱登录
            self.logger.info("选择邮箱登录方式")
            await self.page.click('span.lv_new_third_part_sign_in_expand-label:has-text("Continue with Email")')
            await asyncio.sleep(2)
            
            # 输入账号密码
            self.logger.info("输入账号密码")
            await self.page.fill('input[placeholder="Enter email"]', username)
            await asyncio.sleep(2)
            await self.page.fill('input[type="password"]', password)
            await asyncio.sleep(2)
            
            # 点击登录
            self.logger.info("点击登录按钮")
            await self.page.click('.lv_new_sign_in_panel_wide-sign-in-button')
            await asyncio.sleep(2)
            
            # 等待登录完成
            self.logger.info("等待登录完成")
            await self.page.wait_for_load_state('networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            # 检查是否有确认按钮，如果有则点击
            self.logger.info("检查是否需要确认")
            try:
                confirm_button = await self.page.query_selector('button:has-text("Confirm")')
                if confirm_button:
                    self.logger.info("检测到确认按钮，点击确认")
                    await confirm_button.click()
                    await asyncio.sleep(2)
            except Exception as e:
                self.logger.debug("没有确认按钮，跳过", error=str(e))
            
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="登录成功")
            
        except Exception as e:
            self.logger.error("登录失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="登录失败",
                error_details={"error": str(e)}
            )
    
    async def validate_login_success(self) -> TaskResult:
        """验证登录是否成功"""
        try:
            current_url = self.page.url
            if "dreamina.capcut.com" in current_url and "login" not in current_url:
                self.logger.info("登录验证成功")
                return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="登录验证成功")
            else:
                self.logger.error("登录验证失败", current_url=current_url)
                return TaskResult(
                    code=ErrorCode.WEB_INTERACTION_FAILED.value,
                    data=None,
                    message="登录验证失败，页面跳转异常"
                )
        except Exception as e:
            self.logger.error("登录验证异常", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="登录验证异常",
                error_details={"error": str(e)}
            )
    
    async def navigate_to_generation_page(self) -> TaskResult:
        """跳转到AI工具生成页面"""
        try:
            self.logger.info("正在跳转到AI工具生成页面")
            await self.page.goto('https://dreamina.capcut.com/ai-tool/generate?type=image')
            await self.page.wait_for_load_state('networkidle', timeout=60000)
            await asyncio.sleep(2)
            self.logger.info("已跳转到AI工具页面")
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="页面跳转成功")
        except Exception as e:
            self.logger.error("页面跳转失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="页面跳转失败",
                error_details={"error": str(e)}
            )
    
    async def input_prompt(self, prompt: str) -> TaskResult:
        """输入提示词"""
        try:
            self.logger.info("输入提示词", prompt=prompt)
            # 查找提示词输入框
            textarea_selector = 'textarea.lv-textarea'
            await self.page.wait_for_selector(textarea_selector, timeout=10000)
            await self.page.fill(textarea_selector, prompt)
            await asyncio.sleep(2)
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="提示词输入成功")
        except Exception as e:
            self.logger.error("提示词输入失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="提示词输入失败",
                error_details={"error": str(e)}
            )
    
    async def select_model(self, model: str) -> TaskResult:
        """选择模型"""
        try:
            self.logger.info("选择模型", model=model)
            await self.page.click('div.lv-select[role="combobox"]:not([class*="type-select-"])')
            await asyncio.sleep(1)
            
            # 等待下拉菜单完全加载
            await self.page.wait_for_selector('div.lv-select-popup-inner[role="listbox"]', timeout=5000)
            await asyncio.sleep(1)
            
            # 查找并点击对应的模型选项
            try:
                option_elements = await self.page.query_selector_all('li[role="option"] [class*="option-label-"]')
                model_option_found = False
                
                for element in option_elements:
                    text_content = await element.text_content()
                    if model in text_content:
                        await element.click()
                        model_option_found = True
                        self.logger.info("已选择模型", model=model)
                        break
                
                if not model_option_found:
                    raise Exception("未找到模型选项")
                    
            except Exception as e:
                self.logger.warning("未找到指定模型，尝试通用选择方式", model=model, error=str(e))
                await self.page.click(f'span[class*="select-option-label-content"]:has-text("{model}")')
            
            await asyncio.sleep(1)
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="模型选择成功")
            
        except Exception as e:
            self.logger.error("模型选择失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="模型选择失败",
                error_details={"error": str(e)}
            )
    
    async def select_aspect_ratio(self, aspect_ratio: str) -> TaskResult:
        """选择比例"""
        try:
            self.logger.info("选择比例", aspect_ratio=aspect_ratio)
            
            # 重试机制，最多尝试3次
            max_retries = 3
            ratio_selected = False
            
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"第 {attempt + 1} 次尝试选择比例")
                    
                    # 点击比例选择按钮
                    await self.page.click('button.lv-btn.lv-btn-secondary.lv-btn-size-default.lv-btn-shape-square:has([class*="button-text-"])')
                    await asyncio.sleep(1)
                    
                    # 定义比例选项的映射（从比例值到索引位置）
                    ratio_index_map = {
                        "21:9": 0,
                        "16:9": 1,
                        "3:2": 2,
                        "4:3": 3,
                        "1:1": 4,
                        "3:4": 5,
                        "2:3": 6,
                        "9:16": 7
                    }
                    
                    # 获取对应比例的索引
                    if aspect_ratio in ratio_index_map:
                        ratio_index = ratio_index_map[aspect_ratio]
                        # 在弹出的比例选择框中选择对应位置的比例选项
                        await self.page.click(f'div.lv-radio-group.radio-group-ME1Gqz label.lv-radio:nth-child({ratio_index + 1})')
                        await asyncio.sleep(1)
                    else:
                        # 如果找不到对应的比例，抛出异常
                        raise Exception(f"不支持的比例: {aspect_ratio}")

                    # 关闭选择
                    await self.page.click('button.lv-btn.lv-btn-secondary.lv-btn-size-default.lv-btn-shape-square:has([class*="button-text-"])')
                    await asyncio.sleep(1)
                    
                    # 检查是否选择成功 - 查找按钮中是否包含目标比例
                    button_element = await self.page.query_selector('button.lv-btn.lv-btn-secondary.lv-btn-size-default.lv-btn-shape-square:has([class*="button-text-"])')
                    if button_element:
                        button_text = await button_element.text_content()
                        if aspect_ratio in button_text:
                            self.logger.info("比例选择成功", aspect_ratio=aspect_ratio)
                            ratio_selected = True
                            break
                        else:
                            self.logger.warning("比例选择失败", current=button_text, expected=aspect_ratio)
                    else:
                        self.logger.warning("未找到比例按钮元素")
                        
                except Exception as e:
                    self.logger.warning(f"第 {attempt + 1} 次选择比例时出错", error=str(e))
                    
                await asyncio.sleep(1)
            
            # 如果3次尝试都失败，返回错误
            if not ratio_selected:
                self.logger.error(f"比例选择失败，已尝试 {max_retries} 次")
                return TaskResult(
                    code=ErrorCode.WEB_INTERACTION_FAILED.value,
                    data=None,
                    message=f"比例选择失败，已尝试 {max_retries} 次"
                )
            
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="比例选择成功")
            
        except Exception as e:
            self.logger.error("比例选择失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="比例选择失败",
                error_details={"error": str(e)}
            )
    
    async def setup_response_listener(self):
        """设置响应监听器"""
        async def handle_response(response):
            if "aigc_draft/generate" in response.url:
                try:
                    data = await response.json()
                    self.logger.info("监测到生成请求响应")
                    if data.get("ret") == "0" and "data" in data and "aigc_data" in data["data"]:
                        self.task_id = data["data"]["aigc_data"]["task"]["task_id"]
                        self.logger.info("获取到任务ID", task_id=self.task_id)
                except:
                    pass
            
            if "/v1/get_asset_list" in response.url and self.task_id:
                try:
                    data = await response.json()
                    if "data" in data and "asset_list" in data["data"]:
                        asset_list = data["data"]["asset_list"]
                        for asset in asset_list:
                            if "id" in asset and asset.get("id") == self.task_id:
                                if "image" in asset and asset["image"].get("finish_time", 0) != 0:
                                    try:
                                        self.image_urls = []
                                        for i in range(4):
                                            try:
                                                url = asset["image"]["item_list"][i]["image"]["large_images"][0]["image_url"]
                                                self.image_urls.append(url)
                                            except (KeyError, IndexError):
                                                self.logger.debug(f"无法获取第{i+1}张图片URL")
                                        
                                        if self.image_urls:
                                            self.logger.info("图片生成完成", count=len(self.image_urls))
                                            for i, url in enumerate(self.image_urls):
                                                self.logger.info(f"图片{i+1} URL", url=url)
                                            self.generation_completed = True
                                        else:
                                            self.logger.warning("图片已完成但无法获取任何URL")
                                            self.generation_completed = True  # 标记为完成，即使没有URL
                                    except (KeyError, IndexError):
                                        self.logger.warning("图片已完成但无法获取URL")
                                        self.generation_completed = True  # 标记为完成，即使没有URL
                                else:
                                    self.logger.debug("图片生成尚未完成，继续等待")
                except:
                    pass
        
        # 注册响应监听器
        self.page.on("response", handle_response)
    
    async def start_generation(self) -> TaskResult:
        """点击生成按钮开始生成"""
        try:
            self.logger.info("等待生成按钮可用并点击")
            await self.page.wait_for_selector('button[class^="lv-btn lv-btn-primary"][class*="submit-button-"]:not(.lv-btn-disabled)', timeout=60000)
            
            # 使用JavaScript强制点击生成按钮
            self.logger.info("使用JavaScript强制点击生成按钮")
            await self.page.evaluate('''
                () => {
                    const button = document.querySelector('button[class^="lv-btn lv-btn-primary"][class*="submit-button-"]:not(.lv-btn-disabled)');
                    if (button) {
                        button.click();
                        return true;
                    }
                    return false;
                }
            ''')
            
            self.logger.info("已点击生成按钮，开始生成图片")
            await asyncio.sleep(2)
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="开始生成")
        except Exception as e:
            self.logger.error("点击生成按钮失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="点击生成按钮失败",
                error_details={"error": str(e)}
            )
    
    async def wait_for_generation_complete(self, max_wait_time: int = 3600) -> TaskResult:
        """等待生成完成"""
        try:
            # 等待获取到任务ID
            self.logger.info("等待获取任务ID")
            wait_task_id_time = 120
            task_id_start_time = time.time()
            
            while not self.task_id and time.time() - task_id_start_time < wait_task_id_time:
                elapsed = time.time() - task_id_start_time
                self.logger.debug(f"等待任务ID中，已等待 {elapsed:.1f} 秒")
                await asyncio.sleep(1)
            
            if not self.task_id:
                self.logger.error("未能获取到任务ID，生成可能失败")
                return TaskResult(
                    code=ErrorCode.TASK_ID_NOT_OBTAINED.value,
                    data=None,
                    message="任务ID等待超时"
                )
                
            # 等待图片生成完成
            self.logger.info("已获取任务ID，等待图片生成完成", task_id=self.task_id)
            start_time = time.time()
            
            while not self.generation_completed and time.time() - start_time < max_wait_time:
                elapsed = time.time() - start_time
                self.logger.debug(f"等待图片生成中，已等待 {elapsed:.1f} 秒")
                await self.page.reload()
                self.logger.debug("刷新页面，检查图片生成状态")
                await asyncio.sleep(5)
            
            if self.generation_completed and self.image_urls:
                self.logger.info("图片生成成功", total_time=f"{time.time() - start_time:.1f}秒", count=len(self.image_urls))
                for i, url in enumerate(self.image_urls):
                    self.logger.info(f"图片{i+1} URL", url=url)
                return TaskResult(
                    code=ErrorCode.SUCCESS.value,
                    data=self.image_urls,
                    message="图片生成成功"
                )
            elif self.generation_completed and not self.image_urls:
                self.logger.error("任务已完成但未获取到图片URL", task_id=self.task_id, wait_time=f"{time.time() - start_time:.1f}秒")
                return TaskResult(
                    code=ErrorCode.GENERATION_FAILED.value,
                    data=None,
                    message="当前任务生成失败，请手动生成"
                )
            else:
                self.logger.warning("等待超时，任务未完成", wait_time=f"{time.time() - start_time:.1f}秒", task_id=self.task_id)
                return TaskResult(
                    code=ErrorCode.GENERATION_FAILED.value,
                    data=None,
                    message="当前任务生成失败，请手动生成"
                )
                
        except Exception as e:
            self.logger.error("等待生成完成时出错", error=str(e))
            return TaskResult(
                code=ErrorCode.OTHER_ERROR.value,
                data=None,
                message="等待生成完成时出错",
                error_details={"error": str(e)}
            )
    
    async def execute(self, **kwargs) -> TaskResult:
        """执行文本生成图片任务"""
        start_time = time.time()
        
        # 提取参数
        prompt = kwargs.get('prompt')
        username = kwargs.get('username')
        password = kwargs.get('password')
        model = kwargs.get('model', 'Image 3.1')
        aspect_ratio = kwargs.get('aspect_ratio', '1:1')
        quality = kwargs.get('quality', '1K')
        cookies = kwargs.get('cookies')
        
        self.logger.info("开始执行文本生成图片任务", 
                        prompt=prompt, model=model, 
                        aspect_ratio=aspect_ratio, quality=quality)
        
        try:
            # 初始化浏览器
            init_result = await self.init_browser(cookies)
            if init_result.code != ErrorCode.SUCCESS.value:
                return init_result
            
            # 如果有cookies，先设置cookies并检查登录状态
            if cookies:
                await self.handle_cookies(cookies)
                # 检查登录状态
                login_status_result = await self.check_login_status()
            
            # 如果没有cookies或cookies检查失败，需要登录
            if not cookies or login_status_result.code == 600:
                login_result = await self.perform_login(username, password)
                if login_result.code != ErrorCode.SUCCESS.value:
                    return login_result
                
                validate_result = await self.validate_login_success()
                if validate_result.code != ErrorCode.SUCCESS.value:
                    return validate_result
            
            # 跳转到生成页面
            nav_result = await self.navigate_to_generation_page()
            if nav_result.code != ErrorCode.SUCCESS.value:
                return nav_result
            
            # 设置响应监听器
            await self.setup_response_listener()
            
            # 输入提示词
            prompt_result = await self.input_prompt(prompt)
            if prompt_result.code != ErrorCode.SUCCESS.value:
                return prompt_result
            
            # 选择模型
            model_result = await self.select_model(model)
            if model_result.code != ErrorCode.SUCCESS.value:
                return model_result
            
            # 选择比例
            if model != 'Nano Banana':
                ratio_result = await self.select_aspect_ratio(aspect_ratio)
                if ratio_result.code != ErrorCode.SUCCESS.value:
                    return ratio_result
            else:
                self.logger.info("Nano Banana模型，不选择比例")
            
            # 开始生成
            gen_result = await self.start_generation()
            if gen_result.code != ErrorCode.SUCCESS.value:
                return gen_result
            
            # 等待生成完成
            complete_result = await self.wait_for_generation_complete()
            
            # 获取最新的cookies
            final_cookies = await self.get_cookies()
            complete_result.cookies = final_cookies
            complete_result.execution_time = time.time() - start_time
            
            return complete_result
            
        except asyncio.TimeoutError as e:
            self.logger.error("Playwright等待超时", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message=f"Playwright等待超时: {str(e)}",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            error_msg = str(e)
            self.logger.error("生成图片时出错", error=error_msg)
            
            # 根据错误信息判断错误类型
            if "selector" in error_msg.lower() or "element" in error_msg.lower() or "not found" in error_msg.lower():
                error_code = ErrorCode.WEB_INTERACTION_FAILED.value
            elif "timeout" in error_msg.lower():
                error_code = ErrorCode.WEB_INTERACTION_FAILED.value
            else:
                error_code = ErrorCode.OTHER_ERROR.value
                
            return TaskResult(
                code=error_code,
                data=None,
                message=f"生成图片时出错: {error_msg}",
                execution_time=time.time() - start_time,
                error_details={"error": error_msg}
            )
        
        finally:
            await self.close_browser()

    async def run(self, **kwargs) -> TaskResult:
        """运行任务的入口方法"""
        return await self.execute(**kwargs)

# 兼容性函数，保持向后兼容
async def text2image(prompt, username, password, model="Image 3.1", aspect_ratio="1:1", quality="1K", headless=False, cookies=None):
    """
    兼容性函数，用于保持向后兼容
    """
    executor = JimengText2ImageExecutor(headless=headless)
    result = await executor.run(
        prompt=prompt,
        username=username,
        password=password,
        model=model,
        aspect_ratio=aspect_ratio,
        quality=quality,
        cookies=cookies
    )
    
    # 转换为旧格式的返回值
    return {
        "code": result.code,
        "data": result.data,
        "message": result.message
    }

# 使用示例
if __name__ == "__main__":
    async def test():
        username = "hsabqiq2bqnr@maildrop.cc"
        password = "123456"
        prompt = "一只可爱的猫咪在阳光下玩耍"
        model = "Image 3.1"
        aspect_ratio = "1:1"
        quality = "1K"
        cookies = "faceu-commerce-user-info=U19xKzQpj3FOtLUIN8ecOFLt_kRh1dlEZ8xhDCSIc_CAhci-xH0kl4-B9p1k4QJDyb3bQXwRFulN9G8hgvgUPJ1Jw5GRFZoI5R29tuEC05uy7-AwMrbQmVmdtEwY0JEVMia9HzhByRVg1lDjtdCv8hzFv_djVRenN6fdMiWQWhwwOhS0cyv5NDat6Un-fwDv6aSv7bEQoxcgkHqUp5drJRr99Z-E9I_McJotKhNEZ9TCVSy4f1rKmVW5E-lQH4fuYWNONUy2aH6MtDBeoW2vNZLhwh05iHlaothh8GAXagxIhu3mGKOknoO22lXfdLPpiCUiU-AgfPFYwUeeIq_I3zLVWwl77ivxTHSZuvIdAZsnOFFouzqbrua1E-2_ga_R13M7NJQ9S=GS2.1.s1757648995$o1$g1$t1757649015$j40$l0$h0; uifid_temp=455d7194fb3030a9c1fd263cebe74df90113e22092f6daad0427de1b7f41a2e9b77c56e4177b112b8983ebd64cf5fc9d413f46625ce887736fbfbdba7df2af5fac8a459f6488ef3e1b07c8e0c56d47ba; fpk1=c40c6a0e21650f53942fb9038168e96a23e6ecd1a46982c8087cedb2c27da6c7cd83836ac8695e11d7c8057151c2695d; s_v_web_id=verify_mfgaur92_1vPUMg70_EZxG_4FDY_9flF_nbVDH5PwyLCF; passport_csrf_token=87cfb78370b506cc86b2a1ec199feb61; passport_csrf_token_default=87cfb78370b506cc86b2a1ec199feb61; sid_guard=5fe20bddb672d697c2bd8bbdf9ec3e12%7C1757649043%7C5184000%7CTue%2C+11-Nov-2025+03%3A50%3A43+GMT; uid_tt=4fcec1e103b7d8673099ca0df4fb961fc1c2acb03a3b7f8bc7629abe29f4ab14; uid_tt_ss=4fcec1e103b7d8673099ca0df4fb961fc1c2acb03a3b7f8bc7629abe29f4ab14; sid_tt=5fe20bddb672d697c2bd8bbdf9ec3e12; sessionid=5fe20bddb672d697c2bd8bbdf9ec3e12; sessionid_ss=5fe20bddb672d697c2bd8bbdf9ec3e12; sid_ucp_v1=1.0.0-KDkwMDgyOTlkYzY0YmY0NDNmODM5MmQyMTRhMjA0ZWQ0NWQxNDI3MGMKGQiQiJDsisrE22gQk7GOxgYY6awfOAFA6wcQAxoDbXkyIiA1ZmUyMGJkZGI2NzJkNjk3YzJiZDhiYmRmOWVjM2UxMg; ssid_ucp_v1=1.0.0-KDkwMDgyOTlkYzY0YmY0NDNmODM5MmQyMTRhMjA0ZWQ0NWQxNDI3MGMKGQiQiJDsisrE22gQk7GOxgYY6awfOAFA6wcQAxoDbXkyIiA1ZmUyMGJkZGI2NzJkNjk3YzJiZDhiYmRmOWVjM2UxMg; store-idc=alisg; store-country-code=tw; store-country-code-src=uid; cc-target-idc=alisg; tt-target-idc-sign=j1gi6RRElkOy2S8lFGZZOi6sgRdq3rvZxBsfxbUFPanUX4SS_7c2_H778z1E6VHTus_q5KIBd3-yUkH_7fHMfe9OgaVR-0u9VSYiXZEuECLbi6ws0dOZD1x9F53Ms8tV2G_FL2G114WtfmGLAnBszsba8bkwKHlmEMyEtuRjSgkTWKaJXefX8aSByZ8it8EJlWustQ9gyhaG4vLANRG9ViAf-Cz40TzhebioRwI6g-SIlmv0U89SW4lwKxXuBFSamz25LyD-XXO-xOfHOzkHpIP9ob-WAudufIbw8Pg8RmsQwwJ0-PmbF8fiWo43Tr2AnNsd0-CA2HU4iURscnosyK3GQbj9arTd9_7LN8v0Zbt"
        
        executor = JimengText2ImageExecutor(headless=False)
        result = await executor.run(
            prompt=prompt,
            username=username,
            password=password,
            model=model,
            aspect_ratio=aspect_ratio,
            quality=quality,
            cookies=cookies
        )
        
        if result.code == 200:
            print(f"生成成功，图片链接列表: {result.data}")
        else:
            print(f"生成失败: {result.message}")
    
    # 运行测试
    asyncio.run(test())