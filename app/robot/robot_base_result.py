
# -*- coding: utf-8 -*-
import json


class RobotBaseResult:
    def __init__(self, code, message, data):
        self.code = code
        self.message = message
        self.data = data  # data会在to_json时转为JSON字符串

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }

    def to_json(self):
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def is_success(self):
        """判断是否成功"""
        return self.code == 0

    @classmethod
    def success(cls, message="操作成功", data=None):
        """创建成功结果"""
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message="操作失败", code=-1, data=None):
        """创建失败结果"""
        return cls(code=code, message=message, data=data)

    def __str__(self):
        return f"RobotBaseResult(code={self.code}, message={self.message}, data={self.data})"