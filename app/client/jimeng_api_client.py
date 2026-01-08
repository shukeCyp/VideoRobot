# -*- coding: utf-8 -*-
import requests
from app.utils.logger import log
from app.utils.config_manager import get_config_manager
import json


class JimengApiClient:
    """即梦API客户端"""

    # 默认超时配置
    DEFAULT_IMAGE_TIMEOUT = 300  # 图片生成默认超时（秒）
    DEFAULT_VIDEO_TIMEOUT = 600  # 视频生成默认超时（秒）

    def __init__(self, base_url: str = None):
        """
        初始化即梦API客户端

        Args:
            base_url: API基础地址，如果不传则从配置中动态读取
        """
        self._custom_base_url = base_url.rstrip('/') if base_url else None
        if self._custom_base_url:
            log.info(f"即梦API客户端使用自定义地址: {self._custom_base_url}")
        else:
            log.debug("即梦API客户端将从配置中动态读取地址")

    @property
    def base_url(self):
        """动态获取API地址，优先使用自定义地址，否则从配置中读取"""
        if self._custom_base_url:
            return self._custom_base_url

        config_manager = get_config_manager()
        url = config_manager.get("jimeng_api", "").rstrip('/')

        if not url:
            log.warning("即梦API地址未配置")

        return url

    def get_image_timeout(self) -> int:
        """获取图片生成超时时间（秒）"""
        config_manager = get_config_manager()
        return config_manager.get_int("jimeng_intl_image_timeout", self.DEFAULT_IMAGE_TIMEOUT)

    def get_video_timeout(self) -> int:
        """获取视频生成超时时间（秒）"""
        config_manager = get_config_manager()
        return config_manager.get_int("jimeng_intl_video_timeout", self.DEFAULT_VIDEO_TIMEOUT)

    def account_check(self, token: str) -> int:
        """
        检查账号积分

        Args:
            token: 账号token

        Returns:
            int: 总积分数量，失败返回0
        """
        if not self.base_url:
            log.error("即梦API地址未配置，无法检查账号")
            return 0

        url = f"{self.base_url}/token/receive"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        log.debug(f"开始查询账号积分")
        log.debug(f"  请求地址: {url}")
        log.debug(f"  Token: {token[:20]}...")

        try:
            log.debug(f"发送POST请求到 {url}")
            response = requests.post(url, headers=headers, timeout=30)

            log.debug(f"收到响应，状态码: {response.status_code}")
            response.raise_for_status()

            data = response.json()
            log.debug(f"响应数据类型: {type(data).__name__}")

            if isinstance(data, list) and len(data) > 0:
                credits = data[0].get("credits", {})
                total_credit = credits.get("totalCredit", 0)
                log.info(f"✓ 账号积分查询成功")
                log.debug(f"  Token: {token[:20]}...")
                log.debug(f"  总积分: {total_credit}")
                log.debug(f"  礼物积分: {credits.get('giftCredit', 0)}")
                log.debug(f"  购买积分: {credits.get('purchaseCredit', 0)}")
                log.debug(f"  VIP积分: {credits.get('vipCredit', 0)}")
                return int(total_credit)
            else:
                log.warning(f"✗ 账号积分查询返回数据格式异常")
                log.warning(f"  响应数据: {json.dumps(data, ensure_ascii=False)}")
                return 0

        except requests.exceptions.Timeout:
            log.error(f"✗ 账号积分查询超时")
            log.error(f"  URL: {url}")
            log.error(f"  超时时长: 30秒")
            return 0
        except requests.exceptions.ConnectionError as e:
            log.error(f"✗ 账号积分查询连接失败")
            log.error(f"  URL: {url}")
            log.error(f"  错误信息: {str(e)}")
            return 0
        except requests.exceptions.HTTPError as e:
            log.error(f"✗ 账号积分查询HTTP错误")
            log.error(f"  URL: {url}")
            log.error(f"  状态码: {response.status_code}")
            log.error(f"  错误信息: {str(e)}")
            return 0
        except requests.exceptions.RequestException as e:
            log.error(f"✗ 账号积分查询请求失败")
            log.error(f"  URL: {url}")
            log.error(f"  错误信息: {str(e)}")
            return 0
        except (ValueError, KeyError) as e:
            log.error(f"✗ 账号积分查询解析失败")
            log.error(f"  错误信息: {str(e)}")
            log.debug(f"  响应数据: {json.dumps(data, ensure_ascii=False)}")
            return 0
        except Exception as e:
            log.error(f"✗ 账号积分查询发生未知错误")
            log.error(f"  错误类型: {type(e).__name__}")
            log.error(f"  错误信息: {str(e)}")
            return 0

    def generate_image(self, token: str, prompt: str, image_paths: list = None,
                      ratio: str = "1:1", model: str = "jimeng-4.5", resolution: str = "2k") -> dict:
        """
        生成图片

        Args:
            token: 账号token
            prompt: 图片描述文本
            image_paths: 参考图片路径列表（可选）
            ratio: 图像比例，默认为 "1:1"。支持: 1:1, 4:3, 3:4, 16:9, 9:16, 3:2, 2:3, 21:9
            model: 使用的模型，默认为 "jimeng-4.5"
            resolution: 分辨率级别，默认为 "2k"。支持: 1k, 2k, 4k

        Returns:
            dict: 返回生成结果，包含 task_id 和其他信息；失败返回空字典
        """
        if not self.base_url:
            log.error("即梦API地址未配置，无法生成图片")
            return {}

        if not prompt:
            log.error("提示词不能为空")
            return {}

        url = f"{self.base_url}/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        log.debug(f"开始生成图片")
        log.debug(f"  请求地址: {url}")
        log.debug(f"  Token: {token[:20]}...")
        log.debug(f"  提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        log.debug(f"  分辨率比例: {ratio}")
        log.debug(f"  模型: {model}")
        log.debug(f"  分辨率: {resolution}")
        log.debug(f"  参考图片数: {len(image_paths) if image_paths else 0}")

        response = None
        result = None
        open_files = []
        image_timeout = self.get_image_timeout()
        log.debug(f"  超时时间: {image_timeout}秒")

        try:
            # 构建请求数据
            data = {
                "prompt": prompt,
                "model": model,
                "ratio": ratio,
                "resolution": resolution
            }

            # 检查是否有图片
            files = []
            image_count = 0
            if image_paths:
                log.debug(f"处理参考图片:")
                for idx, image_path in enumerate(image_paths):
                    try:
                        # 打开文件但保持打开状态直到请求完成
                        f = open(image_path, 'rb')
                        open_files.append(f)

                        # 使用列表方式支持多文件上传
                        file_content = f.read()
                        files.append(('images', (f"image_{idx}.jpg", file_content, 'image/jpeg')))
                        image_count += 1
                        log.debug(f"  [{idx + 1}] {image_path}")
                    except FileNotFoundError:
                        log.warning(f"  ✗ 图片文件不存在: {image_path}")
                        continue
                    except IOError as e:
                        log.warning(f"  ✗ 读取图片文件失败: {image_path}, 错误: {str(e)}")
                        continue

            log.debug(f"已添加 {image_count} 个参考图片到请求")
            log.debug(f"发送POST请求到 {url}")

            # 根据是否有文件决定请求方式
            if files:
                # 有文件时，使用图生图端点 + multipart/form-data 格式
                compositions_url = f"{self.base_url}/v1/images/compositions"
                log.debug(f"使用图生图端点: {compositions_url}")
                log.debug(f"使用 multipart/form-data 格式发送请求（包含 {image_count} 个图片）")
                response = requests.post(compositions_url, headers={"Authorization": headers["Authorization"]}, data=data, files=files, timeout=image_timeout)
            else:
                # 没有文件时，使用文生图端点 + JSON 格式
                log.debug(f"使用文生图端点: {url}")
                log.debug(f"使用 application/json 格式发送请求（不包含图片）")
                log.debug(f"请求头: {headers}")
                log.debug(f"请求体: {json.dumps(data, ensure_ascii=False)}")
                response = requests.post(url, headers=headers, json=data, timeout=image_timeout)

            log.debug(f"收到响应，状态码: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            log.info(f"✓ 图片生成请求成功")
            log.debug(f"  Token: {token[:20]}...")
            log.debug(f"  提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            log.debug(f"  响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result

        except requests.exceptions.Timeout:
            log.error(f"✗ 图片生成请求超时")
            log.error(f"  URL: {url}")
            log.error(f"  超时时长: {image_timeout}秒")
            log.error(f"  提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            return {}
        except requests.exceptions.ConnectionError as e:
            log.error(f"✗ 图片生成请求连接失败")
            log.error(f"  URL: {url}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        except requests.exceptions.HTTPError as e:
            log.error(f"✗ 图片生成请求HTTP错误")
            log.error(f"  URL: {url}")
            if response is not None:
                log.error(f"  状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    log.error(f"  响应数据: {json.dumps(error_data, ensure_ascii=False)}")
                except:
                    log.error(f"  响应文本: {response.text}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        except requests.exceptions.RequestException as e:
            log.error(f"✗ 图片生成请求失败")
            log.error(f"  URL: {url}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        except ValueError as e:
            log.error(f"✗ 图片生成响应解析失败（JSON解析错误）")
            log.error(f"  错误信息: {str(e)}")
            if response is not None:
                try:
                    log.debug(f"  响应文本: {response.text[:200]}")
                except:
                    pass
            return {}
        except KeyError as e:
            log.error(f"✗ 图片生成响应数据缺少必要字段")
            log.error(f"  缺少字段: {str(e)}")
            if result is not None:
                log.debug(f"  响应数据: {json.dumps(result, ensure_ascii=False)}")
            return {}
        except Exception as e:
            log.error(f"✗ 图片生成发生未知错误")
            log.error(f"  错误类型: {type(e).__name__}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        finally:
            # 关闭所有打开的文件
            for f in open_files:
                try:
                    f.close()
                except:
                    pass

    def generate_video(self, token: str, prompt: str, image_paths: list = None,
                      ratio: str = "16:9", model: str = "jimeng-video-3.0", duration: int = 5) -> dict:
        """
        生成视频

        Args:
            token: 账号token
            prompt: 视频描述文本
            image_paths: 图片路径列表（可选，0-2张图片）
            ratio: 视频比例，默认为 "16:9"
            model: 使用的模型，默认为 "jimeng-video-3.0"
            duration: 视频时长（秒），默认为 5

        Returns:
            dict: 返回生成结果，包含 task_id 和其他信息；失败返回空字典
        """
        if not self.base_url:
            log.error("即梦API地址未配置，无法生成视频")
            return {}

        if not prompt:
            log.error("提示词不能为空")
            return {}

        url = f"{self.base_url}/v1/videos/generations"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        log.debug(f"开始生成视频")
        log.debug(f"  请求地址: {url}")
        log.debug(f"  Token: {token[:20]}...")
        log.debug(f"  提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        log.debug(f"  视频比例: {ratio}")
        log.debug(f"  模型: {model}")
        log.debug(f"  时长: {duration}秒")
        log.debug(f"  参考图片数: {len(image_paths) if image_paths else 0}")

        response = None
        result = None
        open_files = []
        video_timeout = self.get_video_timeout()
        log.debug(f"  超时时间: {video_timeout}秒")

        try:
            # 检查是否有图片
            if image_paths and len(image_paths) > 0:
                # 有图片时，使用 multipart/form-data 格式
                log.debug(f"使用图生视频端点（包含 {len(image_paths)} 张图片）")
                log.debug(f"使用 multipart/form-data 格式发送请求")

                files = []
                data = {
                    "prompt": prompt,
                    "model": model,
                    "ratio": ratio,
                    "duration": str(duration)
                }

                # 处理图片文件
                for idx, image_path in enumerate(image_paths, 1):
                    try:
                        if image_path.startswith("http://") or image_path.startswith("https://"):
                            # 网络图片，使用 filePaths 字段
                            if "filePaths" not in data:
                                data["filePaths"] = []
                            data["filePaths"].append(image_path)
                            log.debug(f"  [{idx}] 网络图片: {image_path[:60]}...")
                        else:
                            # 本地图片，上传文件
                            f = open(image_path, 'rb')
                            open_files.append(f)

                            file_content = f.read()
                            files.append((f'image_file_{idx}', (f"image_{idx}.jpg", file_content, 'image/jpeg')))
                            log.debug(f"  [{idx}] {image_path}")
                    except FileNotFoundError:
                        log.warning(f"  ✗ 图片文件不存在: {image_path}")
                        continue
                    except IOError as e:
                        log.warning(f"  ✗ 读取图片文件失败: {image_path}, 错误: {str(e)}")
                        continue

                response = requests.post(url, headers=headers, data=data, files=files, timeout=video_timeout)
            else:
                # 没有图片时，使用 JSON 格式（文生视频）
                log.debug(f"使用文生视频端点（纯文本生成）")
                log.debug(f"使用 application/json 格式发送请求")

                headers["Content-Type"] = "application/json"
                request_data = {
                    "prompt": prompt,
                    "model": model,
                    "ratio": ratio,
                    "duration": duration
                }
                log.debug(f"请求体: {json.dumps(request_data, ensure_ascii=False)}")
                response = requests.post(url, headers=headers, json=request_data, timeout=video_timeout)

            log.debug(f"收到响应，状态码: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            log.info(f"✓ 视频生成请求成功")
            log.debug(f"  Token: {token[:20]}...")
            log.debug(f"  提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            log.debug(f"  响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result

        except requests.exceptions.Timeout:
            log.error(f"✗ 视频生成请求超时")
            log.error(f"  URL: {url}")
            log.error(f"  超时时长: {video_timeout}秒")
            log.error(f"  提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
            return {}
        except requests.exceptions.ConnectionError as e:
            log.error(f"✗ 视频生成请求连接失败")
            log.error(f"  URL: {url}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        except requests.exceptions.HTTPError as e:
            log.error(f"✗ 视频生成请求HTTP错误")
            log.error(f"  URL: {url}")
            if response is not None:
                log.error(f"  状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    log.error(f"  响应数据: {json.dumps(error_data, ensure_ascii=False)}")
                except:
                    log.error(f"  响应文本: {response.text}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        except requests.exceptions.RequestException as e:
            log.error(f"✗ 视频生成请求失败")
            log.error(f"  URL: {url}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        except ValueError as e:
            log.error(f"✗ 视频生成响应解析失败（JSON解析错误）")
            log.error(f"  错误信息: {str(e)}")
            if response is not None:
                try:
                    log.debug(f"  响应文本: {response.text[:200]}")
                except:
                    pass
            return {}
        except KeyError as e:
            log.error(f"✗ 视频生成响应数据缺少必要字段")
            log.error(f"  缺少字段: {str(e)}")
            if result is not None:
                log.debug(f"  响应数据: {json.dumps(result, ensure_ascii=False)}")
            return {}
        except Exception as e:
            log.error(f"✗ 视频生成发生未知错误")
            log.error(f"  错误类型: {type(e).__name__}")
            log.error(f"  错误信息: {str(e)}")
            return {}
        finally:
            # 关闭所有打开的文件
            for f in open_files:
                try:
                    f.close()
                except:
                    pass


# 全局单例
_jimeng_api_client = None


def get_jimeng_api_client() -> JimengApiClient:
    """获取即梦API客户端单例"""
    global _jimeng_api_client
    if _jimeng_api_client is None:
        log.debug("创建新的即梦API客户端单例")
        _jimeng_api_client = JimengApiClient()
    return _jimeng_api_client

