"""
即梦平台自动化模块 - 图片生成视频
based on BaseTaskExecutor refactoring version
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from backend.utils.base_task_executor import BaseTaskExecutor, TaskResult, ErrorCode, TaskLogger

class JimengImage2VideoExecutor(BaseTaskExecutor):
    """即梦图片生成视频执行器"""
    
    def __init__(self, headless: bool = False):
        super().__init__(headless)
        self.task_id = None
        self.video_url = None
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
    
    async def navigate_to_image2video_page(self) -> TaskResult:
        """跳转到图片生成视频页面"""
        try:
            self.logger.info("正在跳转到AI工具生成页面")
            await self.page.goto('https://dreamina.capcut.com/ai-tool/generate')
            await self.page.wait_for_load_state('networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            # 选择AI Video选项
            self.logger.info("尝试选择AI Video选项")
            try:
                # 检查是否存在新的tabs节点
                tabs_selector = 'div.tabs-dTWN8k'
                tabs_element = await self.page.query_selector(tabs_selector)
                
                if tabs_element:
                    self.logger.info("发现新的tabs界面，使用新方式选择AI Video")
                    # 使用新的tabs方式选择AI Video
                    await self.page.click('button.tab-YSwCEn:has-text("AI Video")')
                    await asyncio.sleep(2)
                else:
                    self.logger.info("未发现新tabs界面，使用传统下拉框方式")
                    # 点击类型选择下拉框
                    await self.page.click('div.lv-select[role="combobox"][class*="type-select-"]')
                    await asyncio.sleep(1)
                    
                    # 选择AI Video选项
                    await self.page.click('span[class*="select-option-label-content"]:has-text("AI Video")')
                    await asyncio.sleep(2)
                    
            except Exception as e:
                self.logger.warning("选择AI Video时出错，尝试备用方法", error=str(e))
                # 备用方法：直接尝试传统下拉框方式
                try:
                    await self.page.click('div.lv-select[role="combobox"][class*="type-select-"]')
                    await asyncio.sleep(1)
                    await self.page.click('span[class*="select-option-label-content"]:has-text("AI Video")')
                    await asyncio.sleep(2)
                except Exception as backup_e:
                    self.logger.error("无法选择AI Video选项", error=str(backup_e))
                    return TaskResult(
                        code=ErrorCode.WEB_INTERACTION_FAILED.value,
                        data=None,
                        message=f"无法选择AI Video选项: {str(backup_e)}",
                        error_details={"error": str(backup_e)}
                    )
            
            self.logger.info("已跳转到图片生成视频页面并选择AI Video")
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="页面跳转成功")
        except Exception as e:
            self.logger.error("页面跳转失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="页面跳转失败",
                error_details={"error": str(e)}
            )
    
    async def select_video_model(self, model: str = "Video 3.0") -> TaskResult:
        """选择视频模型"""
        try:
            self.logger.info("选择视频模型", model=model)
            
            # 点击视频模型选择下拉框（第一个非类型选择的下拉框）
            video_model_selectors = await self.page.query_selector_all('div.lv-select[role="combobox"]:not([class*="type-select-"])')
            if len(video_model_selectors) >= 1:
                await video_model_selectors[0].click()
                await asyncio.sleep(1)
                
                # 等待下拉菜单出现
                await self.page.wait_for_selector('div.lv-select-popup-inner[role="listbox"]', timeout=5000)
                await asyncio.sleep(1)
                
                # 根据模型参数按照位置选择对应的视频模型
                try:
                    if "Video 3.0 Pro" in model or model == "Video 3.0 Pro":
                        # Video 3.0 Pro 在第一个位置（index 0）
                        await self.page.click('li[role="option"]:nth-child(1)')
                        self.logger.info("已选择视频模型: Video 3.0 Pro")
                    elif "Video 3.0" in model or model == "Video 3.0":
                        # Video 3.0 在第二个位置（index 1）
                        await self.page.click('li[role="option"]:nth-child(2)')
                        self.logger.info("已选择视频模型: Video 3.0")
                    elif "Video S2.0 Pro" in model or model == "Video S2.0 Pro":
                        # Video S2.0 Pro 在第三个位置（index 2）
                        await self.page.click('li[role="option"]:nth-child(3)')
                        self.logger.info("已选择视频模型: Video S2.0 Pro")
                    else:
                        # 默认选择第一个可用模型（Video 3.0 Pro）
                        await self.page.click('li[role="option"]:nth-child(1)')
                        self.logger.info("使用默认视频模型: Video 3.0 Pro")
                except Exception as e:
                    self.logger.warning("选择视频模型时出错，使用默认选项", error=str(e))
                    await self.page.click('li[role="option"]:nth-child(1)')
                await asyncio.sleep(2)
                return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="视频模型选择成功")
            else:
                self.logger.warning("未找到视频模型选择器")
                return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="未找到视频模型选择器，跳过")
                
        except Exception as e:
            self.logger.error("选择视频模型失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="选择视频模型失败",
                error_details={"error": str(e)}
            )
    
    async def select_video_duration(self, second: int = 5) -> TaskResult:
        """选择视频时长"""
        try:
            self.logger.info("选择视频时长", second=second)
            
            # 点击时长选择下拉框（第二个非类型选择的下拉框）
            duration_selectors = await self.page.query_selector_all('div.lv-select[role="combobox"]:not([class*="type-select-"])')
            if len(duration_selectors) >= 2:
                if len(duration_selectors) > 2:
                    await duration_selectors[2].click()  # 第二个非类型选择的下拉框就是时长选择
                else:
                    await duration_selectors[1].click()  # 第二个非类型选择的下拉框就是时长选择
                await asyncio.sleep(1)
                
                # 等待时长选择弹窗出现
                await self.page.wait_for_selector('div.lv-select-popup-inner[role="listbox"]', timeout=5000)
                await asyncio.sleep(1)
                
                # 根据second参数选择对应的时长
                try:
                    if second == 5:
                        # 选择5s选项
                        await self.page.click('li[role="option"] span:has-text("5s")')
                        self.logger.info("已选择时长: 5s")
                    elif second == 10:
                        # 选择10s选项
                        await self.page.click('li[role="option"] span:has-text("10s")')
                        self.logger.info("已选择时长: 10s")
                    else:
                        # 默认选择5s
                        await self.page.click('li[role="option"] span:has-text("5s")')
                        self.logger.info("使用默认时长: 5s")
                except Exception as e:
                    self.logger.warning("选择时长时出错，使用默认选项", error=str(e))
                    await self.page.click('li[role="option"]:first-child')
                
                await asyncio.sleep(2)
                return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="视频时长选择成功")
            else:
                self.logger.warning("未找到时长选择器")
                return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="未找到时长选择器，跳过")
                
        except Exception as e:
            self.logger.error("选择视频时长失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="选择视频时长失败",
                error_details={"error": str(e)}
            )

    async def upload_image(self, image_path: str) -> TaskResult:
        """上传图片"""
        try:
            self.logger.info("上传图片", image_path=image_path)
            
            # 查找文件上传输入框
            upload_selector = 'input[type="file"][accept*="image"]'
            await self.page.wait_for_selector(upload_selector, timeout=10000, state='attached')
            
            # 上传图片文件
            await self.page.set_input_files(upload_selector, image_path)
            self.logger.info("图片上传成功")
            await asyncio.sleep(3)
            return TaskResult(code=ErrorCode.SUCCESS.value, data=None, message="图片上传成功")
        except Exception as e:
            self.logger.error("图片上传失败", error=str(e))
            return TaskResult(
                code=ErrorCode.WEB_INTERACTION_FAILED.value,
                data=None,
                message="图片上传失败",
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
                                # 检查视频生成是否完成
                                if "video" in asset and asset["video"].get("finish_time", 0) != 0:
                                    try:
                                        # 获取视频URL
                                        if "item_list" in asset["video"] and len(asset["video"]["item_list"]) > 0:
                                            video_item = asset["video"]["item_list"][0]
                                            if "video" in video_item and "transcoded_video" in video_item["video"]:
                                                transcoded = video_item["video"]["transcoded_video"]
                                                if "origin" in transcoded and "video_url" in transcoded["origin"]:
                                                    self.video_url = transcoded["origin"]["video_url"]
                                        
                                        if self.video_url:
                                            self.logger.info("视频生成完成", video_url=self.video_url)
                                            self.generation_completed = True
                                        else:
                                            self.logger.warning("视频已完成但无法获取URL")
                                            self.generation_completed = True  # 标记为完成，即使没有URL
                                    except (KeyError, IndexError):
                                        self.logger.warning("视频已完成但无法获取URL")
                                        self.generation_completed = True  # 标记为完成，即使没有URL
                                else:
                                    self.logger.debug("视频生成尚未完成，继续等待")
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
            
            self.logger.info("已点击生成按钮，开始生成视频")
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
            wait_task_id_time = 30
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
                
            # 等待视频生成完成
            self.logger.info("已获取任务ID，等待视频生成完成", task_id=self.task_id)
            start_time = time.time()
            
            while not self.generation_completed and time.time() - start_time < max_wait_time:
                elapsed = time.time() - start_time
                self.logger.debug(f"等待视频生成中，已等待 {elapsed:.1f} 秒")
                await self.page.reload()
                self.logger.debug("刷新页面，检查视频生成状态")
                await asyncio.sleep(5)
            
            if self.generation_completed and self.video_url:
                self.logger.info("视频生成成功", total_time=f"{time.time() - start_time:.1f}秒", video_url=self.video_url)
                return TaskResult(
                    code=ErrorCode.SUCCESS.value,
                    data=self.video_url,
                    message="视频生成成功"
                )
            elif self.generation_completed and not self.video_url:
                self.logger.error("任务已完成但未获取到视频URL", task_id=self.task_id, wait_time=f"{time.time() - start_time:.1f}秒")
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
        """执行图片生成视频任务"""
        start_time = time.time()
        
        # 提取参数
        image_path = kwargs.get('image_path')
        prompt = kwargs.get('prompt', '')
        model = kwargs.get('model', 'Video 3.0')
        second = kwargs.get('second', 5)
        username = kwargs.get('username')
        password = kwargs.get('password')
        cookies = kwargs.get('cookies')
        
        self.logger.info("开始执行图片生成视频任务", 
                        image_path=image_path, prompt=prompt, model=model, second=second)
        
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
            else:
                # 如果有cookies，直接设置
                await self.handle_cookies(cookies)
            
            # 跳转到图片生成视频页面
            nav_result = await self.navigate_to_image2video_page()
            if nav_result.code != ErrorCode.SUCCESS.value:
                return nav_result
            
            # 设置响应监听器
            await self.setup_response_listener()
            
            # 选择视频模型
            model_result = await self.select_video_model(model)
            if model_result.code != ErrorCode.SUCCESS.value:
                return model_result
            
            # 选择视频时长
            duration_result = await self.select_video_duration(second)
            if duration_result.code != ErrorCode.SUCCESS.value:
                return duration_result
            
            # 上传图片
            upload_result = await self.upload_image(image_path)
            if upload_result.code != ErrorCode.SUCCESS.value:
                return upload_result
            
            # 输入提示词（如果有）
            if prompt:
                prompt_result = await self.input_prompt(prompt)
                if prompt_result.code != ErrorCode.SUCCESS.value:
                    return prompt_result
            
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
            self.logger.error("生成视频时出错", error=error_msg)
            
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
                message=f"生成视频时出错: {error_msg}",
                execution_time=time.time() - start_time,
                error_details={"error": error_msg}
            )
        
        finally:
            await self.close_browser()

    async def run(self, **kwargs) -> TaskResult:
        """运行任务的入口方法"""
        return await self.execute(**kwargs)

# 兼容性函数，保持向后兼容
async def image2video(image_path, prompt="", model="Video 3.0", second=5, username=None, password=None, headless=False, cookies=None):
    """
    兼容性函数，用于保持向后兼容
    """
    executor = JimengImage2VideoExecutor(headless=headless)
    result = await executor.run(
        image_path=image_path,
        prompt=prompt,
        model=model,
        second=second,
        username=username,
        password=password,
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
        username = "test@example.com"
        password = "password123"
        image_path = "/path/to/image.jpg"
        prompt = "让这张图片动起来"
        model = "Video 3.0"
        second = 10
        
        executor = JimengImage2VideoExecutor(headless=False)
        result = await executor.run(
            image_path=image_path,
            prompt=prompt,
            model=model,
            second=second,
            username=username,
            password=password
        )
        
        if result.code == 200:
            print(f"生成成功，视频链接: {result.data}")
        else:
            print(f"生成失败: {result.message}")
    
    # 运行测试
    asyncio.run(test())