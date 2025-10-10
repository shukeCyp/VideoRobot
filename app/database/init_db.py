# -*- coding: utf-8 -*-
from app.database.db import db, DB_PATH
from app.models.config import Config
from app.models.jimeng_account import JimengAccount
from app.models.jimeng_image_task import JimengImageTask
from app.utils.logger import log


def init_database():
    """初始化数据库"""
    try:
        # 连接数据库（如果还未连接）
        if db.is_closed():
            db.connect()
            log.info(f"数据库连接成功: {DB_PATH}")
        else:
            log.info(f"数据库已连接: {DB_PATH}")

        # 创建表
        db.create_tables([Config, JimengAccount, JimengImageTask], safe=True)
        log.info("数据库表创建成功")

    except Exception as e:
        log.error(f"数据库初始化失败: {e}")
        raise


def close_database():
    """关闭数据库连接"""
    if not db.is_closed():
        db.close()
        log.info("数据库连接已关闭")


if __name__ == "__main__":
    init_database()