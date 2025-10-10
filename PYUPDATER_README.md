# PyUpdater 使用说明

## 安装依赖

```bash
pip install -r requirements.txt
```

## 首次初始化

```bash
# 1. 初始化 PyUpdater
./build_release.sh init

# 这会生成:
# - .pyupdater/ 目录
# - client_config.py (已存在)
# - 密钥对
```

## 配置 GitHub Release

编辑 `client_config.py`,修改:

```python
UPDATE_URLS = ['https://github.com/YOUR_USERNAME/YOUR_REPO/releases/download/']
```

替换为你的 GitHub 仓库地址。

## 构建和发布流程

### 方式一: 完整流程(推荐)

```bash
./build_release.sh all
```

这会自动执行:
1. 构建应用
2. 打包更新
3. 上传到 GitHub Release

### 方式二: 分步执行

```bash
# 1. 构建应用
./build_release.sh build

# 2. 打包更新
./build_release.sh package

# 3. 上传到 GitHub
./build_release.sh upload
```

## 更新版本号

修改 `app/version.py`:

```python
__version__ = "1.1.0"  # 修改版本号
```

## 测试更新功能

1. 首先发布一个版本 (如 v1.0.0)
2. 修改版本号为 v1.0.1
3. 构建并发布新版本
4. 运行 v1.0.0 版本,应该能检测到更新

## 注意事项

- 确保安装了 GitHub CLI: `brew install gh` (macOS)
- 首次使用需要登录: `gh auth login`
- PUBLIC_KEY 在首次 init 后会自动生成并写入 client_config.py
- pyu-data/deploy/ 目录包含打包好的更新文件

## 目录结构

```
pyu-data/
├── deploy/           # 发布文件(上传到 GitHub)
├── files/            # 构建的应用文件
└── new/              # 待打包的更新
```
