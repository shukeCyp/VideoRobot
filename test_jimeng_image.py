#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即梦图片生成测试脚本

使用方法:
    python test_jimeng_image.py --account-id 1 --prompt "一只可爱的小猫"

参数说明:
    --account-id: 账号ID (必需)
    --prompt: 图片提示词 (必需)
    --headless: 是否无头模式 (可选,默认False)
"""
import sys
import os
import asyncio
import argparse

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app.robot.jimeng.image_generator import generate_image_with_account
from app.utils.logger import log
from app.database.init_db import init_database


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='即梦图片生成测试')
    parser.add_argument('--account-id', type=int, required=True, help='账号ID')
    parser.add_argument('--prompt', type=str, required=True, help='图片提示词')
    parser.add_argument('--headless', action='store_true', help='无头模式')

    args = parser.parse_args()

    # 初始化数据库
    log.info("初始化数据库...")
    init_database()

    # 执行图片生成
    log.info("="*60)
    log.info(f"开始测试即梦图片生成")
    log.info(f"账号ID: {args.account_id}")
    log.info(f"提示词: {args.prompt}")
    log.info(f"无头模式: {args.headless}")
    log.info("="*60)

    try:
        result = await generate_image_with_account(
            account_id=args.account_id,
            prompt=args.prompt,
            headless=args.headless
        )

        log.info("="*60)
        log.info("生成结果:")
        log.info(f"成功: {result['success']}")
        log.info(f"消息: {result['message']}")
        log.info(f"图片数量: {len(result['images'])}")

        if result['images']:
            log.info("图片URL:")
            for i, url in enumerate(result['images'], 1):
                log.info(f"  {i}. {url}")

        log.info("="*60)

        if result['success']:
            log.info("✅ 测试成功!")
        else:
            log.warning("⚠️  测试完成,但生成失败")

    except Exception as e:
        log.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
