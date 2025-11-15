# -*- coding: utf-8 -*-
"""
即梦图片生成结果数据结构
"""


class JimengImageResultData:
    """即梦图片生成结果数据"""

    def __init__(self, jimeng_task_id: str = "", image_urls: list = None, cookies: str = ""):
        """
        初始化即梦图片生成结果数据

        Args:
            jimeng_task_id: 即梦平台返回的任务ID
            image_urls: 图片URL列表
            cookies: 账号Cookie（可能需要更新）
        """
        self.jimeng_task_id = jimeng_task_id
        self.image_urls = image_urls if image_urls is not None else []
        self.cookies = cookies

    def to_dict(self):
        """转换为字典"""
        return {
            "jimeng_task_id": self.jimeng_task_id,
            "image_urls": self.image_urls,
            "cookies": self.cookies
        }

    def __str__(self):
        return f"JimengImageResultData(jimeng_task_id={self.jimeng_task_id}, image_count={len(self.image_urls)})"
