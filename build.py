#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller 打包脚本
用于将 VideoRobot 应用打包成单文件可执行文件
"""

import os
import sys
import shutil
import subprocess
import platform

def main():
    """主打包流程"""

    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))

    print(f"项目根目录: {project_root}")
    print(f"当前平台: {platform.system()}")

    # 检查必要文件
    required_files = [
        'icon.png',
        'group_qrcode.png',
        'vx_qrcode.png',
        'main.py',
        'requirements.txt'
    ]

    for file in required_files:
        file_path = os.path.join(project_root, file)
        if not os.path.exists(file_path):
            print(f"错误: 缺少文件 {file}")
            return False

    print("✓ 所有必要文件检查通过")

    # 清理旧的打包文件
    build_dir = os.path.join(project_root, 'build')
    dist_dir = os.path.join(project_root, 'dist')

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print("✓ 已清理 build 目录")

    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
        print("✓ 已清理 dist 目录")

    # 构建 PyInstaller 命令
    if platform.system() == 'Darwin':  # macOS
        # macOS 使用 onedir 模式避免兼容性问题
        pyinstaller_cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onedir',            # macOS 使用目录模式
            '--windowed',          # 不显示控制台窗口
            '--name', 'VideoRobot',
            '--icon', 'icon.png',
            '--add-data', f'icon.png{os.pathsep}.',
            '--add-data', f'group_qrcode.png{os.pathsep}.',
            '--add-data', f'vx_qrcode.png{os.pathsep}.',
            '--add-data', f'app{os.pathsep}app',
            '--copy-metadata=PyQt5',
            '--copy-metadata=PyQt-Fluent-Widgets',
            '--hidden-import=PyQt5',
            '--hidden-import=PyQt5.QtCore',
            '--hidden-import=PyQt5.QtGui',
            '--hidden-import=PyQt5.QtWidgets',
            '--hidden-import=PyQt5.sip',
            '--hidden-import=qfluentwidgets',
            '--hidden-import=peewee',
            '--hidden-import=requests',
            '--hidden-import=Crypto',
            '--hidden-import=PIL',
            'main.py'
        ]
    else:  # Windows 和 Linux
        # Windows 和 Linux 使用 onefile 模式
        pyinstaller_cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',           # 单文件模式
            '--windowed',          # 不显示控制台窗口
            '--name', 'VideoRobot',
            '--icon', 'icon.png',
            '--add-data', f'icon.png{os.pathsep}.',
            '--add-data', f'group_qrcode.png{os.pathsep}.',
            '--add-data', f'vx_qrcode.png{os.pathsep}.',
            '--add-data', f'app{os.pathsep}app',
            '--copy-metadata=PyQt5',
            '--copy-metadata=PyQt-Fluent-Widgets',
            '--hidden-import=PyQt5',
            '--hidden-import=PyQt5.QtCore',
            '--hidden-import=PyQt5.QtGui',
            '--hidden-import=PyQt5.QtWidgets',
            '--hidden-import=PyQt5.sip',
            '--hidden-import=qfluentwidgets',
            '--hidden-import=peewee',
            '--hidden-import=requests',
            '--hidden-import=Crypto',
            '--hidden-import=PIL',
            'main.py'
        ]

    print("\n开始打包...")
    print(" ".join(pyinstaller_cmd))
    print()

    # 执行打包
    result = subprocess.run(pyinstaller_cmd, cwd=project_root)

    if result.returncode == 0:
        print("\n✓ 打包成功!")

        # 获取打包后的文件
        if platform.system() == 'Windows':
            executable = os.path.join(dist_dir, 'VideoRobot.exe')
            print(f"\n执行文件位置: {executable}")
        elif platform.system() == 'Darwin':
            executable = os.path.join(dist_dir, 'VideoRobot')
            print(f"\n执行文件位置: {executable}")
        else:
            executable = os.path.join(dist_dir, 'VideoRobot')
            print(f"\n执行文件位置: {executable}")

        if os.path.exists(executable):
            file_size = os.path.getsize(executable) / (1024 * 1024)
            print(f"文件大小: {file_size:.2f} MB")

        return True
    else:
        print("\n✗ 打包失败!")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
