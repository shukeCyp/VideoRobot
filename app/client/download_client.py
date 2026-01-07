# -*- coding: utf-8 -*-
"""
下载客户端
用于执行文件下载任务
"""
import os
import requests
from typing import Optional, Callable, Tuple
from concurrent.futures import Future
from app.utils.logger import log
from app.managers.download_manager import get_download_manager


class DownloadClient:
    """下载客户端"""

    def __init__(self, timeout: int = 300, chunk_size: int = 8192):
        """
        初始化下载客户端

        Args:
            timeout: 下载超时时间（秒）
            chunk_size: 下载块大小
        """
        self.timeout = timeout
        self.chunk_size = chunk_size

    def download(
        self,
        url: str,
        save_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        headers: Optional[dict] = None
    ) -> Tuple[bool, str]:
        """
        同步下载文件

        Args:
            url: 下载地址
            save_path: 保存路径
            progress_callback: 进度回调函数，参数为(已下载字节数, 总字节数)
            headers: 自定义请求头

        Returns:
            Tuple[bool, str]: (是否成功, 消息或错误信息)
        """
        log.debug(f"开始下载文件")
        log.debug(f"  URL: {url}")
        log.debug(f"  保存路径: {save_path}")

        try:
            # 确保保存目录存在
            save_dir = os.path.dirname(save_path)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir)
                log.debug(f"  创建目录: {save_dir}")

            # 设置请求头
            request_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            if headers:
                request_headers.update(headers)

            # 发送请求
            response = requests.get(
                url,
                headers=request_headers,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()

            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            log.debug(f"  文件大小: {self._format_size(total_size)}")

            # 下载文件
            downloaded_size = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 进度回调
                        if progress_callback:
                            try:
                                progress_callback(downloaded_size, total_size)
                            except Exception as e:
                                log.warning(f"进度回调异常: {str(e)}")

            log.info(f"文件下载成功: {save_path}")
            return True, save_path

        except requests.exceptions.Timeout:
            error_msg = f"下载超时（{self.timeout}秒）"
            log.error(f"下载失败: {error_msg}")
            log.error(f"  URL: {url}")
            return False, error_msg

        except requests.exceptions.ConnectionError as e:
            error_msg = f"连接失败: {str(e)}"
            log.error(f"下载失败: {error_msg}")
            log.error(f"  URL: {url}")
            return False, error_msg

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP错误: {str(e)}"
            log.error(f"下载失败: {error_msg}")
            log.error(f"  URL: {url}")
            return False, error_msg

        except IOError as e:
            error_msg = f"文件写入失败: {str(e)}"
            log.error(f"下载失败: {error_msg}")
            log.error(f"  保存路径: {save_path}")
            return False, error_msg

        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            log.error(f"下载失败: {error_msg}")
            log.error(f"  URL: {url}")
            return False, error_msg

    def download_async(
        self,
        url: str,
        save_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        headers: Optional[dict] = None,
        done_callback: Optional[Callable[[Future], None]] = None
    ) -> Future:
        """
        异步下载文件（使用全局下载线程池）

        Args:
            url: 下载地址
            save_path: 保存路径
            progress_callback: 进度回调函数，参数为(已下载字节数, 总字节数)
            headers: 自定义请求头
            done_callback: 完成回调函数

        Returns:
            Future: 任务的Future对象，结果为Tuple[bool, str]
        """
        download_manager = get_download_manager()
        future = download_manager.submit(
            self.download,
            url,
            save_path,
            progress_callback,
            headers
        )

        if done_callback:
            future.add_done_callback(done_callback)

        return future

    def download_multiple(
        self,
        tasks: list,
        done_callback: Optional[Callable[[str, bool, str], None]] = None
    ) -> list:
        """
        批量异步下载文件

        Args:
            tasks: 下载任务列表，每个任务为dict，包含:
                   - url: 下载地址
                   - save_path: 保存路径
                   - headers: 可选的请求头
            done_callback: 单个任务完成回调，参数为(url, 是否成功, 消息)

        Returns:
            list: Future对象列表
        """
        futures = []

        for task in tasks:
            url = task.get('url')
            save_path = task.get('save_path')
            headers = task.get('headers')

            if not url or not save_path:
                log.warning(f"无效的下载任务: {task}")
                continue

            def make_callback(task_url):
                def callback(f: Future):
                    try:
                        success, msg = f.result()
                        if done_callback:
                            done_callback(task_url, success, msg)
                    except Exception as e:
                        if done_callback:
                            done_callback(task_url, False, str(e))
                return callback

            future = self.download_async(
                url=url,
                save_path=save_path,
                headers=headers,
                done_callback=make_callback(url)
            )
            futures.append(future)

        return futures

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"


# 全局单例
_download_client: Optional[DownloadClient] = None


def get_download_client() -> DownloadClient:
    """获取下载客户端单例"""
    global _download_client
    if _download_client is None:
        _download_client = DownloadClient()
    return _download_client
