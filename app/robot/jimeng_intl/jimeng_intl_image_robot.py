
from app.robot.jimeng_intl.jimeng_intl_robot_base import JimengIntlRobotBase
from playwright.sync_api import sync_playwright
from app.utils.logger import log
from app.robot.robot_base_result import RobotBaseResult, ResultCode
from app.constants import JIMENG_INTL_IMAGE_MODE_MAP
import time


class JimengIntlImageResultData:
    def __init__(self, cookies=None, images=None):
        self.cookies = cookies or []
        self.images = images or []

    def to_dict(self):
        return {
            "cookies": self.cookies,
            "images": self.images,
        }


class JimengIntlImageRobot(JimengIntlRobotBase):
    def __init__(self,username,password,prompt,model,cookies = [],input_images = [],ratio = None,quality = None, headless=True):
        self.username = username
        self.password = password
        self.prompt = prompt
        self.model = model
        self.cookies = cookies
        self.input_images = input_images
        self.ratio = ratio
        self.quality = quality
        self.headless = headless
        self.task_id = None
        self.output_images = None
        self.generation_completed = False

    def run(self):
        result_data = JimengIntlImageResultData()
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                if self.cookies:
                    page.context.add_cookies(self.cookies)
                # 跳转登录界面
                try: 
                    page.goto("https://dreamina.capcut.com/ai-tool/login", timeout=60000)
                except Exception as e:
                    log.error(f"打开登录页失败: {e}")
                    return RobotBaseResult.error(code=ResultCode.JM_INTL_PAGE_LOAD_TIMEOUT.code, data=result_data.to_dict())
                # 添加登录页的localStorage项，防止弹窗展示
                page.evaluate('window.localStorage.setItem("app_download_modal_first_screen_shown", "true")')
                try:
                    page.wait_for_url("https://dreamina.capcut.com/ai-tool/home", timeout=30000)
                except Exception:
                    page.locator(".lv-checkbox-mask").first.click()
                    page.locator("div[class^='login-button-']").first.click()

                    page.get_by_text("Continue with email", exact=True).click()

                    page.get_by_placeholder("Enter email").first.fill(self.username)
                    page.get_by_placeholder("Enter password").first.fill(self.password)
                    page.click('.lv_new_sign_in_panel_wide-sign-in-button')

                try:
                    page.wait_for_selector("div[class^='credit-amount-text-']", timeout=60000)
                except Exception as e:
                    log.error(f"登录失败: {e}")
                    return RobotBaseResult.error(code=ResultCode.JM_INTL_LOGIN_FAILED.code, data=result_data.to_dict())
                # 登录成功

                # 初始化变量

                def handle_response(response):
                    if "aigc_draft/generate" in response.url:
                        try:
                            data = response.json()
                            log.info("监测到生成请求响应")
                            if data.get("ret") == "0" and "data" in data and "aigc_data" in data["data"]:
                                self.task_id = data["data"]["aigc_data"]["task"]["task_id"]
                                log.info("获取到任务ID", task_id=self.task_id)
                        except:
                            pass
                    if "/v1/get_asset_list" in response.url and self.task_id:
                        try:
                            data = response.json()
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
                                                        log.debug(f"无法获取第{i+1}张图片URL")
                                                
                                                if self.image_urls:
                                                    log.info("图片生成完成", count=len(self.image_urls))
                                                    for i, url in enumerate(self.image_urls):
                                                        log.info(f"图片{i+1} URL", url=url)
                                                    self.generation_completed = True
                                                else:
                                                    log.warning("图片已完成但无法获取任何URL")
                                                    self.generation_completed = True  # 标记为完成，即使没有URL
                                            except (KeyError, IndexError):
                                                log.warning("图片已完成但无法获取URL")
                                                self.generation_completed = True  # 标记为完成，即使没有URL
                                        else:
                                            log.debug("图片生成尚未完成，继续等待")
                        except:
                            pass

                # 设置监听
                page.on("response", handle_response)

                # 跳转图片生成界面https://dreamina.capcut.com/ai-tool/generate?type=image
                try:
                    page.goto("https://dreamina.capcut.com/ai-tool/generate?type=image", timeout=60000)
                except Exception as e:
                    log.error(f"跳转图片生成界面失败: {e}")
                    return RobotBaseResult.error(code=ResultCode.JM_INTL_PAGE_LOAD_TIMEOUT.code, data=result_data.to_dict())
                # 跳转完成，需要开始执行任务
                # 开始选择模型
                page.fill("textarea.lv-textarea", self.prompt)

                # 选择模型
                page.click('div.lv-select[role="combobox"]:not([class*="type-select-"])')
                page.wait_for_selector('div.lv-select-popup-inner[role="listbox"]', timeout=5000)
                try:
                    option_elements = page.query_selector_all('li[role="option"] [class*="option-label-"]')
                    model_option_found = False
                    
                    for element in option_elements:
                        text_content = element.text_content()
                        if self.model == text_content:
                            element.click()
                            model_option_found = True
                            log.info("已选择模型", model=self.model)
                            break
                    
                    if not model_option_found:
                        raise Exception("未找到模型选项")
                        
                except Exception as e:
                    log.warning("未找到指定模型，尝试通用选择方式", model=self.model, error=str(e))
                    page.click(f'span[class*="select-option-label-content"]:has-text("{self.model}")')

                # 开始选择比例
                page.click('button.lv-btn.lv-btn-secondary.lv-btn-size-default.lv-btn-shape-square:has([class*="button-text-"])')
                if self.ratio:
                    ratio_index_map = JIMENG_INTL_IMAGE_MODE_MAP.get(self.model, {}).get("ratio", {})

                    for index, ratio in ratio_index_map.items():
                        if ratio == self.ratio:
                            page.click(f'div.lv-radio-group.radio-group-ME1Gqz label.lv-radio:nth-child({index + 1})')
                            log.info("已选择比例", ratio=self.ratio)
                            break
                if self.quality:
                    pass

                # 上传图片
                page.query_selector('input[type="file"][accept*="image"]').input_files(self.input_images)

                # 开始点击生成
                page.wait_for_selector('button[class^="lv-btn lv-btn-primary"][class*="submit-button-"]:not(.lv-btn-disabled)', timeout=60000)
                log.info("使用JavaScript强制点击生成按钮")
                page.evaluate('''
                    () => {
                        const button = document.querySelector('button[class^="lv-btn lv-btn-primary"][class*="submit-button-"]:not(.lv-btn-disabled)');
                        if (button) {
                            button.click();
                            return true;
                        }
                        return false;
                    }
                ''')
                log.info("点击生成按钮完成")

                self.task_id = self.task_id or None
                for _ in range(60):
                    if self.task_id:
                        break
                    page.wait_for_timeout(1000)
                if not self.task_id:
                    log.error("任务ID等待超时")
                    return RobotBaseResult.error(code=ResultCode.JM_INTL_TASK_ID_WAIT_TIMEOUT.code, data=result_data.to_dict())

                max_wait_seconds = 600
                start_ts = time.time()
                while True:
                    if self.generation_completed:
                        break
                    if time.time() - start_ts > max_wait_seconds:
                        log.error("生成超时")
                        return RobotBaseResult.error(code=ResultCode.JM_INTL_TASK_FAILED.code, data=result_data.to_dict())
                    page.reload()
                    page.wait_for_timeout(5000)

                if not getattr(self, "image_urls", None):
                    log.error("生成完成但无图片")
                    return RobotBaseResult.error(code=ResultCode.JM_INTL_TASK_FAILED.code, data=result_data.to_dict())

                result_data.images = self.image_urls
                # 获取cookies
                cookies = page.context.cookies()
                result_data.cookies = cookies
                log.info("生成完成，返回图片链接", count=len(self.image_urls))
                return RobotBaseResult.success(data=result_data.to_dict())

        except Exception as e:
            log.error(f"生成图片失败: {e}")
            return RobotBaseResult.error(code=ResultCode.JM_INTL_TASK_FAILED.code, data=result_data.to_dict())
       
       
