# VideoRobot

> 一个基于Web的AI视频创作工具集，主要用于AI视频生成和内容创作


## 友情赞助

如果这个项目对你有帮助，欢迎支持我们的发展！你的赞助将帮助我们持续改进和维护这个项目。

<div align="center">
  <a href="https://www.tkyds.com/?=shukeCyp" target="_blank">
    <img src="assets/yds.jpg" alt="友情赞助" width="100%"/>
  </a>
  <p><a href="https://www.tkyds.com/?=shukeCyp" target="_blank"><strong>TK云大师,专业的TikTok矩阵系统,AI赋能自动化,单人轻松管理上万账号！</strong></a></p>
</div>

您的每一份支持都是我们前进的动力！

## 📖 项目简介

VideoRobot是一个开源项目，旨在为开发者和AI爱好者提供便捷的AI视频创作工具使用体验。本项目采用前后端分离架构，支持多种AI平台的集成和管理。

### 🎯 功能描述

- **即梦国际版** - 支持文生图、图生视频、数字人三大核心功能
- **清影** - 专业的图生视频处理工具
- **Runway** - 预留接口，功能开发中

### ✨ 功能特性

| 平台 | 文生图 | 图生视频 | 数字人 |
|------|:------:|:--------:|:------:|
| 即梦国际版 | ✅ | ✅ | ✅ |
| 清影 | ❌ | ✅ | ❌ |
| Runway | ❌ | ❌ | ❌ |
| Vidu | ❌ | ❌ | ❌ |
| 海螺 | ❌ | ❌ | ❌ |

**免责声明：本项目仅供技术交流和学习使用，请勿用于商业用途。**

## ✨ 主要特性

- **现代化界面**：基于Vue 3 + Element Plus的响应式Web界面
- **模块化设计**：支持多平台AI工具的集成和扩展
- **任务管理**：智能任务队列管理和状态监控
- **账号管理**：统一的账号管理和使用统计
- **数据持久化**：基于SQLite的轻量级数据存储
- **实时更新**：任务状态实时监控和更新

## 技术栈

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **Element Plus** - Vue 3组件库
- **Vite** - 现代化构建工具

### 后端
- **Python 3.9+** - 核心开发语言
- **Flask** - 轻量级Web框架
- **Peewee** - 简洁的ORM框架
- **Playwright** - 浏览器自动化工具
- **SQLite** - 嵌入式数据库

## 环境要求

### 系统要求
- **Python 3.9+**
- **Node.js 16+**
- **现代浏览器** (Chrome、Firefox、Safari、Edge)

### 支持的操作系统
- macOS 10.14+
- Windows 10+
- Linux (Ubuntu 18.04+)

## 安装与启动

### 命令行启动方式

#### 1. 启动后端服务
```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python app.py
```

#### 2. 启动前端服务
```bash
# 进入前端目录
cd frontend

# 安装依赖和必要的开发工具
npm install --save-dev @vue/cli-service@5.0.8
npm install --save-dev @vue/compiler-sfc@3.3.4
npm install --save-dev @vue/cli-plugin-babel@5.0.8

# 构建项目
npm run build

# 启动前端开发服务器
npm run dev
```

### 3. 访问应用

启动成功后，在浏览器中访问：
- **前端界面**: http://localhost:9999
- **后端API**: http://localhost:8888

> **提示**：如果前端端口显示为5173，实际访问请使用9999端口

### 视频教程
详细的安装和使用教程可以在这里查看：[视频教程链接](https://h6vw7qmfq7.feishu.cn/docx/EHR7dcIcnodQQCxMnADczqg2nSf?from=from_copylink)

## 功能模块

- **即梦国际版文生图**
- **即梦国际版图生视频**
- **即梦国际版数字人**
- **Runway文生图**
- **Runway图生视频**
- **Vidu图生视频**

## 配置说明

### 基础配置
在 `基础配置` 页面可以设置：
- **自动化线程数**：控制并发任务数量
- **隐藏窗口**：是否在无头模式下运行浏览器

### 账号管理
在 `账号配置` 页面可以：
- 添加和管理即梦平台账号
- 查看账号使用统计
- 批量导入账号信息

## 项目结构

```
VideoRobot/
├── backend/                 # 后端代码
│   ├── api/                # API路由
│   ├── core/               # 核心模块
│   ├── managers/           # 任务管理器
│   ├── models/             # 数据模型
│   ├── utils/              # 工具函数
│   ├── requirements.txt    # Python依赖
│   └── app.py              # 主应用入口
├── frontend/               # 前端代码
│   ├── src/                # 源代码
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   └── utils/          # 工具函数
│   └── package.json        # 依赖配置
└── README.md               # 项目说明
```

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 开源协议

本项目采用 MIT 协议，详情请参见 [LICENSE](LICENSE) 文件。

## 注意事项

1. **仅供学习使用**：本项目仅用于技术交流和学习，请勿用于商业用途
2. **账号安全**：请妥善保管你的平台账号信息，本项目不对账号安全负责
3. **合规使用**：请遵守相关平台的使用条款和法律法规
4. **数据备份**：建议定期备份重要的任务数据和配置信息
5. **环境要求**：
   - 首次运行需要网络连接以下载依赖
   - Windows用户需要管理员权限来安装Node.js

## 联系方式

- **项目地址**：https://github.com/shukeCyp/VideoRobot
- **问题反馈**：https://github.com/shukeCyp/VideoRobot/issues

## 致谢

感谢所有为这个项目贡献代码和建议的开发者们！


---

**如果这个项目对你有帮助，请给它一个Star！**

## Star趋势

[![Star History Chart](https://api.star-history.com/svg?repos=shukeCyp/VideoRobot&type=Date)](https://star-history.com/#shukeCyp/VideoRobot&Date)