
# -*- coding: utf-8 -*-
import json
from enum import Enum


class ResultCode(Enum):
    SUCCESS = (200, "操作成功")
    JM_INTL_PAGE_LOAD_TIMEOUT = (2001, "页面加载超时")
    JM_INTL_NODE_NOT_FOUND = (2002, "节点未找到")
    JM_INTL_TASK_ID_WAIT_TIMEOUT = (2003, "任务ID等待超时")
    JM_INTL_TASK_FAILED = (2004, "任务失败")
    JM_INTL_LOGIN_FAILED = (2005, "登录失败")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

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
        return self.code == ResultCode.SUCCESS.code

    @classmethod
    def success(cls, message=None, data=None):
        """创建成功结果"""
        msg = message if message is not None else ResultCode.SUCCESS.message
        return cls(code=ResultCode.SUCCESS.code, message=msg, data=data)

    @classmethod
    def error(cls, message=None, code=-1, data=None):
        """创建失败结果"""
        # 仅提供code时，自动从枚举获取message
        if message is None:
            if isinstance(code, ResultCode):
                return cls(code=code.code, message=code.message, data=data)
            # 查找枚举中对应的code
            rc = next((item for item in ResultCode if item.code == code), None)
            msg = rc.message if rc else "操作失败"
            return cls(code=code, message=msg, data=data)
        # 提供了自定义message时按入参返回
        if isinstance(code, ResultCode):
            return cls(code=code.code, message=message, data=data)
        return cls(code=code, message=message, data=data)

    def __str__(self):
        return f"RobotBaseResult(code={self.code}, message={self.message}, data={self.data})"
