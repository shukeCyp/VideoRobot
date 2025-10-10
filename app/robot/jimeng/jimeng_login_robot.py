# -*- coding: utf-8 -*-
from datetime import datetime
from app.robot.robot_base_result import RobotBaseResult


class JimengLoginResult(RobotBaseResult):
    """即梦登录结果类"""

    def __init__(self, code, message, avatar=None, nickname=None, points=None,
                 is_vip=False, vip_expire_date=None, cookies=None):
        """
        初始化即梦登录结果

        Args:
            code: 状态码，0表示成功
            message: 返回消息
            avatar: 头像URL
            nickname: 昵称
            points: 积分
            is_vip: 是否会员
            vip_expire_date: 会员到期日期（datetime对象或字符串）
            cookies: Cookies字符串
        """
        # 构建data字典
        data = {
            "avatar": avatar,
            "nickname": nickname,
            "points": points,
            "is_vip": is_vip,
            "vip_expire_date": self._format_datetime(vip_expire_date),
            "cookies": cookies
        }

        super().__init__(code=code, message=message, data=data)

        # 设置属性方便访问
        self.avatar = avatar
        self.nickname = nickname
        self.points = points
        self.is_vip = is_vip
        self.vip_expire_date = vip_expire_date
        self.cookies = cookies

    @staticmethod
    def _format_datetime(dt):
        """格式化日期时间"""
        if dt is None:
            return None
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return str(dt)

    @classmethod
    def success(cls, avatar, nickname, points, is_vip=False, vip_expire_date=None, cookies=""):
        """
        创建成功的登录结果

        Args:
            avatar: 头像URL
            nickname: 昵称
            points: 积分
            is_vip: 是否会员
            vip_expire_date: 会员到期日期
            cookies: Cookies字符串

        Returns:
            JimengLoginResult对象
        """
        return cls(
            code=0,
            message="登录成功",
            avatar=avatar,
            nickname=nickname,
            points=points,
            is_vip=is_vip,
            vip_expire_date=vip_expire_date,
            cookies=cookies
        )

    @classmethod
    def error(cls, message="登录失败", code=-1):
        """
        创建失败的登录结果

        Args:
            message: 错误消息
            code: 错误码

        Returns:
            JimengLoginResult对象
        """
        return cls(code=code, message=message)

    def __str__(self):
        if self.is_success():
            return f"JimengLoginResult(success, nickname={self.nickname}, points={self.points}, is_vip={self.is_vip})"
        return f"JimengLoginResult(failed, code={self.code}, message={self.message})"


class JimengLoginRobot:
    """即梦登录机器人"""

    def __init__(self, headless: bool = False):
        """
        初始化登录机器人

        Args:
            headless: 是否无头模式
        """
        self.headless = headless
        self.user_info = None
        self.vip_info = None
        self.credit_info = None

    def login(self, timeout: int = 300) -> JimengLoginResult:
        """
        执行登录操作

        Args:
            timeout: 超时时间（秒），默认5分钟

        Returns:
            JimengLoginResult对象
        """
        from playwright.sync_api import sync_playwright
        from app.utils.logger import log
        import time
        import json

        try:
            log.info("开始即梦登录流程")

            # 用于存储接口响应
            responses = {
                'user_info': None,
                'subscription': None,
                'credit': None
            }

            def handle_response(response):
                """处理响应"""
                try:
                    url = response.url

                    # 打印所有请求
                    log.info(f"[响应] {response.status} {url}")

                    # 监听用户信息接口
                    if 'get_user_info' in url and response.status == 200:
                        try:
                            data = response.json()
                            log.info(f"✓✓✓ get_user_info 响应: {json.dumps(data, ensure_ascii=False)[:500]}")
                            if data.get('ret') == '0':
                                responses['user_info'] = data.get('data', {})
                                log.info(f"✓ 获取到用户信息: {responses['user_info'].get('name')}")
                        except Exception as e:
                            log.error(f"解析 get_user_info 失败: {e}")

                    # 监听会员信息接口
                    if 'subscription/user_info' in url and response.status == 200:
                        try:
                            data = response.json()
                            log.info(f"✓✓✓ subscription/user_info 响应: {json.dumps(data, ensure_ascii=False)[:500]}")
                            if data.get('ret') == '0':
                                responses['subscription'] = data.get('data', {})
                                log.info("✓ 获取到会员信息")
                        except Exception as e:
                            log.error(f"解析 subscription/user_info 失败: {e}")

                    # 监听积分信息接口
                    if 'benefits/user_credit' in url and response.status == 200:
                        try:
                            data = response.json()
                            log.info(f"✓✓✓ benefits/user_credit 响应: {json.dumps(data, ensure_ascii=False)[:500]}")
                            if data.get('ret') == '0':
                                responses['credit'] = data.get('data', {})
                                log.info("✓ 获取到积分信息")
                        except Exception as e:
                            log.error(f"解析 benefits/user_credit 失败: {e}")

                except Exception as e:
                    log.error(f"处理响应失败: {e}")

            # 启动 Playwright
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # 打开即梦首页
            log.info("打开即梦页面...")
            page.goto("https://jimeng.jianying.com/ai-tool/home", wait_until="networkidle")
            log.info(f"当前页面URL: {page.url}")

            log.info(f"等待用户登录（超时时间: {timeout}秒）...")
            log.info("请在浏览器中完成登录操作")

            # 等待登录成功标志 - 积分显示组件
            start_time = time.time()
            login_success = False

            while time.time() - start_time < timeout:
                try:
                    # 检查登录成功的标志元素（积分显示容器）
                    credit_element = page.query_selector(".credit-display-container-U2Uln7")
                    if credit_element:
                        log.info("✓ 检测到登录成功！")
                        login_success = True
                        break
                except Exception as e:
                    pass

                time.sleep(1)

            if not login_success:
                # 关闭浏览器
                page.close()
                context.close()
                browser.close()
                playwright.stop()

                return JimengLoginResult.error(
                    message="登录超时，未检测到登录成功",
                    code=-1
                )

            # 登录成功后，创建新标签页并设置监听
            log.info("创建新标签页并设置监听器...")
            new_page = context.new_page()

            # 设置监听器
            new_page.on("response", handle_response)
            log.info("✓ 监听器已设置")

            # 在新标签页打开即梦首页，触发接口请求
            log.info("在新标签页加载即梦首页...")
            new_page.goto("https://jimeng.jianying.com/ai-tool/home", wait_until="networkidle")
            log.info("页面加载完成，等待接口数据...")

            # 等待所有接口数据都获取到
            start_time = time.time()
            last_log_time = start_time
            while time.time() - start_time < 60:  # 最多等待60秒
                # 检查是否所有数据都已获取
                if all([
                    responses['user_info'],
                    responses['subscription'],
                    responses['credit']
                ]):
                    log.info("✓ 所有数据已获取完成")
                    break

                # 每5秒提示一次等待状态
                current_time = time.time()
                if current_time - last_log_time >= 5:
                    elapsed = int(current_time - start_time)
                    missing = []
                    if not responses['user_info']:
                        missing.append("用户信息")
                    if not responses['subscription']:
                        missing.append("会员信息")
                    if not responses['credit']:
                        missing.append("积分信息")
                    log.info(f"⏳ 等待接口数据... 已等待{elapsed}秒，还需要: {', '.join(missing)}")
                    last_log_time = current_time

                time.sleep(1)

            # 检查是否超时
            if not all([responses['user_info'], responses['subscription'], responses['credit']]):
                missing = []
                if not responses['user_info']:
                    missing.append("用户信息")
                if not responses['subscription']:
                    missing.append("会员信息")
                if not responses['credit']:
                    missing.append("积分信息")

                # 关闭浏览器
                new_page.close()
                page.close()
                context.close()
                browser.close()
                playwright.stop()

                return JimengLoginResult.error(
                    message=f"获取数据超时，未获取到: {', '.join(missing)}",
                    code=-1
                )

            # 解析数据
            user_info = responses['user_info']
            subscription_info = responses['subscription']
            credit_info = responses['credit']

            # 提取用户基本信息
            avatar = user_info.get('avatar_url', '')
            nickname = user_info.get('name', '')

            # 提取积分信息
            credit_data = credit_info.get('credit', {})
            total_points = (
                credit_data.get('vip_credit', 0) +
                credit_data.get('gift_credit', 0) +
                credit_data.get('purchase_credit', 0)
            )

            # 解析会员信息
            is_vip = subscription_info.get('flag', False)
            vip_expire_date = None

            if is_vip:
                vip_levels = subscription_info.get('vip_levels', [])
                if vip_levels:
                    # 获取当前会员等级的过期时间
                    current_vip = vip_levels[0]
                    end_timestamp = current_vip.get('end_time', 0)
                    if end_timestamp:
                        vip_expire_date = datetime.fromtimestamp(end_timestamp)
                        log.info(f"会员到期时间: {vip_expire_date}")

            # 获取cookies
            cookies_list = context.cookies()
            cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])

            log.info("登录成功！")

            # 关闭浏览器
            new_page.close()
            page.close()
            context.close()
            browser.close()
            playwright.stop()

            # 返回成功结果
            return JimengLoginResult.success(
                avatar=avatar,
                nickname=nickname,
                points=total_points,
                is_vip=is_vip,
                vip_expire_date=vip_expire_date,
                cookies=cookies_str
            )

        except Exception as e:
            log.error(f"登录失败: {e}")
            return JimengLoginResult.error(message=f"登录异常: {str(e)}", code=-1)
