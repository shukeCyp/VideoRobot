# -*- coding: utf-8 -*-
"""
配置管理器
用于读取和保存应用配置
"""
from app.models.config import Config
from app.utils.logger import log


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        pass

    def get(self, key: str, default=None):
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值（字符串）或默认值
        """
        try:
            value = Config.get_value(key, default)

            # 如果是布尔值字符串，转换为布尔类型
            if isinstance(value, str):
                if value.lower() == 'true':
                    return True
                elif value.lower() == 'false':
                    return False

            return value

        except Exception as e:
            log.error(f"获取配置失败 key={key}: {str(e)}")
            return default

    def set(self, key: str, value):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值

        Returns:
            bool: 是否成功
        """
        try:
            # 将布尔值转换为字符串
            if isinstance(value, bool):
                value = 'true' if value else 'false'
            else:
                value = str(value)

            Config.set_value(key, value)
            log.debug(f"配置已保存: {key}={value}")
            return True

        except Exception as e:
            log.error(f"保存配置失败 key={key}: {str(e)}")
            return False

    def get_int(self, key: str, default: int = 0) -> int:
        """
        获取整数配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            int: 配置值
        """
        try:
            value = self.get(key, default)
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        获取浮点数配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            float: 配置值
        """
        try:
            value = self.get(key, default)
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        获取布尔配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            bool: 配置值
        """
        value = self.get(key, default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')

        return bool(value)

    def delete(self, key: str) -> bool:
        """
        删除配置

        Args:
            key: 配置键

        Returns:
            bool: 是否成功
        """
        try:
            config = Config.get(Config.key == key)
            config.delete_instance()
            log.debug(f"配置已删除: {key}")
            return True
        except Config.DoesNotExist:
            log.warning(f"配置不存在: {key}")
            return False
        except Exception as e:
            log.error(f"删除配置失败 key={key}: {str(e)}")
            return False


# 全局单例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
