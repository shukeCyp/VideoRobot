# 安装说明

## 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

## 2. 安装 Playwright 浏览器

安装完 playwright 包后，需要安装浏览器驱动：

```bash
playwright install chromium
```

如果需要安装所有浏览器（Chromium、Firefox、WebKit）：

```bash
playwright install
```

## 3. 运行应用

```bash
python main.py
```

## 数据存储位置

应用数据会存储在以下位置：

- **Windows**: `C:\Users\用户名\AppData\Roaming\VideoRobot`
- **macOS**: `~/Library/Application Support/VideoRobot`
- **Linux**: `~/.local/share/VideoRobot`

包含以下内容：
- `video_robot.db` - 数据库文件
- `logs/` - 日志目录