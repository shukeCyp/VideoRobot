# VideoRobot 打包指南

## 自动打包（GitHub Actions）

### 触发条件
当你推送一个带有版本标签的提交时，GitHub Actions 会自动触发打包流程：

```bash
# 创建并推送版本标签（例如 V2.0.0）
git tag V2.0.0
git push origin V2.0.0
```

### 打包流程
1. 自动在 Windows 环境下打包成 `VideoRobot.exe`
2. 自动在 macOS 环境下打包成 `VideoRobot.dmg`
3. 自动创建 GitHub Release，并上传两个打包文件

### 查看打包结果
在 GitHub 仓库的 Actions 标签页可以查看打包进度，打包完成后会自动发布到 Releases 页面。

## 本地打包

### 环境要求
- Python 3.9+
- 所有依赖已安装（见 requirements.txt）

### 安装打包工具
```bash
pip install pyinstaller
```

### 执行打包
```bash
# 方式一：使用打包脚本（推荐）
python build.py

# 方式二：直接使用 PyInstaller
pyinstaller --onefile \
  --windowed \
  --name "VideoRobot" \
  --icon=icon.png \
  --add-data "icon.png:." \
  --add-data "group_qrcode.png:." \
  --add-data "vx_qrcode.png:." \
  --add-data "app:app" \
  --hidden-import=PyQt5 \
  --hidden-import=qfluentwidgets \
  --hidden-import=peewee \
  --hidden-import=requests \
  main.py
```

### 打包输出
打包完成后，可执行文件会生成在 `dist/` 目录下：
- **Windows**: `dist/VideoRobot.exe`
- **macOS**: `dist/VideoRobot.app` (或 `dist/VideoRobot` 单文件)
- **Linux**: `dist/VideoRobot`

## 打包配置说明

### 关键参数
- `--onefile`: 打包成单个可执行文件
- `--windowed`: 不显示命令行窗口（GUI 应用）
- `--icon`: 应用程序图标
- `--add-data`: 包含的数据文件（如图片、配置等）
- `--hidden-import`: 隐式导入的模块（PyInstaller 无法自动检测）

### 包含的资源文件
- `icon.png`: 应用图标
- `group_qrcode.png`: 群二维码
- `vx_qrcode.png`: 微信二维码
- `app/`: 整个应用模块

## 文件大小预期
单文件打包的可执行文件大小通常在 80-150 MB 之间，取决于依赖库的大小。

## 常见问题

### Q: 打包后无法找到资源文件？
A: 确保 `icon.png`, `group_qrcode.png`, `vx_qrcode.png` 都在项目根目录中，并且 `--add-data` 参数正确。

### Q: PyInstaller 版本不兼容？
A: 建议使用最新的 PyInstaller：
```bash
pip install --upgrade pyinstaller
```

### Q: macOS 打包时出现代码签名错误？
A: 这是正常的，可以使用 `--codesign-identity=''` 跳过代码签名：
```bash
pyinstaller ... --codesign-identity='' ...
```

### Q: 如何清理打包文件？
A: 删除以下目录：
```bash
rm -rf build/
rm -rf dist/
rm -f VideoRobot.spec
```
