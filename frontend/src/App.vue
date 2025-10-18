<template>
  <div id="app">
    <!-- 主应用 -->
    <el-container class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <img src="/icon.png" alt="VideoRobot" class="logo-icon" />
            <h1>VideoRobot</h1>
          </div>
          <div class="center-slogan">
            <span class="logo-slogan">用科技让复杂的世界更简单</span>
          </div>
          <div class="header-actions">
            <el-button 
              text 
              @click="checkHealth"
              :loading="healthChecking"
              style="color: white;"
            >
              <el-icon><Connection /></el-icon>
              {{ healthStatus }}
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 主体内容 -->
      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="200px" class="app-sidebar">
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            @select="handleMenuSelect"
            :default-openeds="[]"
          >
            <el-menu-item index="home">
              <el-icon><House /></el-icon>
              <span>工具分享</span>
            </el-menu-item>
            
            <el-menu-item index="task-manager">
              <el-icon><Monitor /></el-icon>
              <span>任务管理器</span>
            </el-menu-item>
            
            <el-menu-item index="prompt-manager">
              <el-icon><Collection /></el-icon>
              <span>提示词</span>
            </el-menu-item>
            
            <!-- 即梦国际版 -->
            <el-sub-menu index="jimeng">
              <template #title>
                <el-icon><Picture /></el-icon>
                <span>即梦国际版</span>
              </template>
              <el-menu-item index="jimeng-text2img">
                <el-icon><EditPen /></el-icon>
                <span>文生图</span>
              </el-menu-item>
              <el-menu-item index="jimeng-img2img">
                <el-icon><Picture /></el-icon>
                <span>图生图</span>
              </el-menu-item>
              <el-menu-item index="jimeng-img2video">
                <el-icon><VideoPlay /></el-icon>
                <span>图生视频</span>
              </el-menu-item>
              <el-menu-item index="jimeng-digital-human">
                <el-icon><Avatar /></el-icon>
                <span>数字人</span>
              </el-menu-item>
            </el-sub-menu>
            
            <!-- 清影平台 -->
            <el-sub-menu index="qingying">
              <template #title>
                <el-icon><VideoCamera /></el-icon>
                <span>智谱清影</span>
              </template>
              <el-menu-item index="qingying-img2video">
                <el-icon><VideoPlay /></el-icon>
                <span>图生视频</span>
              </el-menu-item>
            </el-sub-menu>
            
            <!-- 账号配置 -->
            <el-sub-menu index="accounts">
              <template #title>
                <el-icon><User /></el-icon>
                <span>账号配置</span>
              </template>
              <el-menu-item index="jimeng-accounts">
                <el-icon><UserFilled /></el-icon>
                <span>即梦账号</span>
              </el-menu-item>
              <el-menu-item index="qingying-accounts">
                <el-icon><UserFilled /></el-icon>
                <span>清影账号</span>
              </el-menu-item>
            </el-sub-menu>
            
            <!-- 个人中心 -->
            <el-sub-menu index="my-profile">
              <template #title>
                <el-icon><User /></el-icon>
                <span>我的</span>
              </template>
              <el-menu-item index="base-config">
                <el-icon><Setting /></el-icon>
                <span>基础配置</span>
              </el-menu-item>
            </el-sub-menu>
            

            <el-menu-item index="about">
              <el-icon><InfoFilled /></el-icon>
              <span>关于我们</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- 主要内容区域 -->
        <el-main class="app-main">
          <div class="content-wrapper">
            <!-- 工具分享界面 -->
            <div v-if="activeMenu === 'home'" class="page-content">
              <div class="tools-share-page">
                <!-- 页面标题 -->
                <div class="page-header">
                  <div class="header-content">
                    <div class="title-section">
                      <div class="title-icon">
                        <el-icon size="32"><Share /></el-icon>
                      </div>
                      <h1 class="page-title">工具分享</h1>
                    </div>
                    <div class="status-section">
                      <span class="page-subtitle">分享实用工具，让效率加倍</span>
                    </div>
                  </div>
                </div>
                
                <!-- 工具分享内容区域 -->
                <div class="tools-container">
                  <div class="tools-grid">
                    <!-- 舒克数字人工具 -->
                    <div class="tool-card" @click="showToolDialog('shukeDigitalHuman')">
                      <div class="tool-image">
                        <img src="./assets/skszr.png" alt="舒克数字人" />
                      </div>
                      <div class="tool-content">
                        <h3 class="tool-title">舒克数字人</h3>
                        <p class="tool-description">智能数字人生成工具</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 即梦国际版功能页面 -->
            <div v-if="activeMenu === 'jimeng-text2img'" class="page-content">
              <JimengText2Img />
            </div>
            
            <div v-if="activeMenu === 'jimeng-img2img'" class="page-content">
              <JimengImg2Img />
            </div>
            
            <div v-if="activeMenu === 'jimeng-img2video'" class="page-content">
              <JimengImg2Video />
            </div>
            
            <div v-if="activeMenu === 'jimeng-digital-human'" class="page-content">
              <JimengDigitalHuman />
            </div>

            <!-- 清影平台功能页面 -->
            <div v-if="activeMenu === 'qingying-img2video'" class="page-content">
              <QingyingImg2Video />
            </div>

            <!-- 账号配置页面 -->
            <div v-if="activeMenu === 'jimeng-accounts'" class="page-content">
              <JimengAccountManager />
            </div>

            <div v-if="activeMenu === 'qingying-accounts'" class="page-content">
              <QingyingAccountManager />
            </div>

            <!-- 任务管理器 -->
            <div v-if="activeMenu === 'task-manager'" class="page-content">
              <TaskManager />
            </div>

            <!-- 提示词管理 -->
            <div v-if="activeMenu === 'prompt-manager'" class="page-content">
              <PromptManager />
            </div>

            <!-- 基础配置 -->
            <div v-if="activeMenu === 'base-config'" class="page-content">
              <BaseConfig />
            </div>

            <!-- 关于我们 -->
            <div v-if="activeMenu === 'about'" class="page-content">
                <div class="about-content">
                  <h2>关于VideoRobot</h2>
                <p><strong>版本:</strong> 1.0.0</p>
                <p><strong>技术栈:</strong> Vue 3 + Element Plus + Flask + SQLite + Playwright</p>
                <p><strong>开发者:</strong> 舒克AI团队</p>
                <p><strong>特色功能:</strong> 多平台AI工具集成、智能任务管理、账号统一管理</p>
                <p><strong>更新时间:</strong> {{ new Date().toLocaleDateString() }}</p>
                </div>
            </div>
          </div>
        </el-main>
      </el-container>
    </el-container>

    <!-- 联系我们对话框 -->
    <el-dialog 
      v-model="contactDialogVisible" 
      title="联系我们" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="contact-content">
        <div class="contact-simple">
          <div class="wechat-info">
            <div class="contact-item">
              <el-icon class="contact-icon" color="#67C23A">
                <ChatDotRound />
              </el-icon>
              <div class="contact-text">
                <div class="contact-label">微信号</div>
                <div class="contact-value">zhaxinyu--</div>
              </div>
            </div>
          </div>
          
          <div class="qrcode-section">
            <div class="qrcode-container">
              <img src="./assets/vx.png" alt="微信二维码" class="qrcode-image" />
              <p class="qrcode-text">扫码添加微信好友</p>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="contact-footer">
          <el-button @click="contactDialogVisible = false">关闭</el-button>
          <el-button class="btn-copy" @click="copyContactInfo">复制微信号</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 友情赞助弹窗 -->
    <el-dialog 
      v-model="sponsorDialogVisible" 
      :title="null"
      width="600px"
      :close-on-click-modal="false"
      :show-close="false"
      center
      class="sponsor-dialog"
      :modal="true"
      :modal-class="'sponsor-modal'"
    >
      <div class="sponsor-container">
        <!-- 悬浮关闭按钮 -->
        <div class="sponsor-close-btn" @click="sponsorDialogVisible = false">
          <el-icon><Close /></el-icon>
        </div>
        
        <!-- 介绍文字 -->
        <div class="sponsor-text">
          <h3>TK云大师,专业的TikTok矩阵系统,AI赋能自动化,单人轻松管理上万账号！</h3>
        </div>
        
        <!-- 图片 -->
        <div class="sponsor-image-container">
          <a @click="openSponsorLink" class="sponsor-link">
            <img src="/yundashi.png" alt="TK云大师" class="sponsor-image" />
          </a>
        </div>
      </div>
    </el-dialog>

    <!-- 交流群悬浮窗 -->
    <div class="group-float" @click="toggleGroupDialog">
      <el-icon size="24"><Message /></el-icon>
      <span>交流群</span>
    </div>

    <!-- 作者微信悬浮窗 -->
    <div class="wechat-float" @click="toggleWechatDialog">
      <el-icon size="24"><ChatDotRound /></el-icon>
      <span>微信</span>
    </div>

    <!-- 交流群弹窗 -->
    <el-dialog 
      v-model="groupDialogVisible" 
      :title="null"
      width="400px"
      :close-on-click-modal="false"
      :show-close="false"
      center
      class="group-dialog"
      :modal="true"
      :modal-class="'group-modal'"
    >
      <div class="group-container">
        <!-- 悬浮关闭按钮 -->
        <div class="group-close-btn" @click="groupDialogVisible = false">
          <el-icon><Close /></el-icon>
        </div>
        
        <!-- 介绍文字 -->
        <div class="group-text">
          <h3>VideoRobot交流群</h3>
        </div>
        
        <!-- 二维码图片 -->
        <div class="group-image-container">
          <img src="./assets/wx_group_qrcode.png" alt="交流群二维码" class="group-image" />
        </div>
      </div>
    </el-dialog>

    <!-- 作者微信弹窗 -->
    <el-dialog 
      v-model="wechatDialogVisible" 
      :title="null"
      width="400px"
      :close-on-click-modal="false"
      :show-close="false"
      center
      class="wechat-dialog"
      :modal="true"
      :modal-class="'wechat-modal'"
    >
      <div class="wechat-container">
        <!-- 悬浮关闭按钮 -->
        <div class="wechat-close-btn" @click="wechatDialogVisible = false">
          <el-icon><Close /></el-icon>
        </div>
        
        <!-- 介绍文字 -->
        <div class="wechat-text">
          <h3>联系作者微信</h3>
        </div>
        
        <!-- 二维码图片 -->
        <div class="wechat-image-container">
          <img src="/benyue.png" alt="作者微信" class="wechat-image" />
        </div>
      </div>
    </el-dialog>

    <!-- 工具详情弹窗 -->
    <el-dialog 
      v-model="toolDialogVisible" 
      :title="currentTool.title"
      width="400px"
      :close-on-click-modal="false"
      :show-close="true"
      class="tool-dialog"
    >
      <div class="tool-dialog-content">
        <!-- 功能介绍 -->
        <div class="tool-features">
          <h4>功能特色</h4>
          <ul class="features-list">
            <li v-for="feature in currentTool.features" :key="feature">
              <el-icon class="feature-icon"><Check /></el-icon>
              {{ feature }}
            </li>
          </ul>
        </div>
        
        <!-- 微信联系 -->
        <div class="tool-contact">
          <div class="wechat-info">
            <div class="wechat-id-container" @click="copyWechatId">
              <el-icon class="wechat-icon"><ChatDotRound /></el-icon>
              <div class="wechat-content">
                <span class="wechat-label">微信号</span>
                <span class="wechat-id">zhaxinyu--</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Connection,
  House,
  User,
  Picture,
  InfoFilled,
  UserFilled,
  SuccessFilled,
  WarningFilled,
  EditPen,
  VideoPlay,
  Avatar,
  Setting,
  Monitor,
  Collection,
  VideoCamera,
  Share,
  Message,
  Check,
  Star,
  Close,
  ChatDotRound
} from '@element-plus/icons-vue'
import AccountConfiguration from './views/AccountConfiguration.vue'
import JimengPlatform from './views/JimengPlatform.vue'
import JimengAccountManager from './components/JimengAccountManager.vue'
import QingyingAccountManager from './components/QingyingAccountManager.vue'
import JimengText2Img from './views/JimengText2Img.vue'
import JimengImg2Img from './views/JimengImg2Img.vue'
import BaseConfig from './views/BaseConfig.vue'
import JimengImg2Video from './views/JimengImg2Video.vue'
import JimengDigitalHuman from './views/JimengDigitalHuman.vue'
import QingyingImg2Video from './views/QingyingImg2Video.vue'
import TaskManager from './views/TaskManager.vue'
import PromptManager from './views/PromptManager.vue'

import { accountAPI } from './utils/api'

export default {
  name: 'App',
  components: {
    AccountConfiguration,
    JimengPlatform,
    JimengAccountManager,
    QingyingAccountManager,
    JimengText2Img,
    JimengImg2Img,
    JimengImg2Video,
    JimengDigitalHuman,
    QingyingImg2Video,
    TaskManager,
    PromptManager,
    BaseConfig,
    Connection,
    House,
    User,
    Picture,
    InfoFilled,
    UserFilled,
    SuccessFilled,
    WarningFilled,
    EditPen,
    VideoPlay,
    Avatar,
    Setting,
    Monitor,
    Collection,
    VideoCamera
  },
  setup() {
    const activeMenu = ref('home')
    const healthStatus = ref('检查中...')
    const healthChecking = ref(false)
    const contactDialogVisible = ref(false)
    const sponsorDialogVisible = ref(false)
    const wechatDialogVisible = ref(false)
    const groupDialogVisible = ref(false) // 新增：交流群弹窗可见性
    
    // 工具弹窗相关
    const toolDialogVisible = ref(false)
    const currentTool = ref({
      title: '',
      features: []
    })
    
    // 工具数据
    const toolsData = {
      shukeDigitalHuman: {
        title: '舒克数字人',
        features: [
          '支持批量生成',
          '支持无限长度视频生成',
          '支持音色克隆',
          '支持试用'
        ]
      }
    }

    // 切换菜单
    const handleMenuSelect = (index) => {
      activeMenu.value = index
    }

    // 健康检查
    const checkHealth = async () => {
      healthChecking.value = true
      try {
        const response = await accountAPI.healthCheck()
        if (response.data.success) {
          healthStatus.value = '服务正常'
          ElMessage.success('后端服务连接正常')
        } else {
          healthStatus.value = '服务异常'
        }
      } catch (error) {
        console.error('健康检查失败:', error)
        healthStatus.value = '连接失败'
        ElMessage.error('无法连接到后端服务，请确保服务已启动')
      } finally {
        healthChecking.value = false
      }
    }

    // 联系我们
    const contactUs = () => {
      contactDialogVisible.value = true
    }
    
    // 显示工具详情弹窗
    const showToolDialog = (toolKey) => {
      if (toolsData[toolKey]) {
        currentTool.value = toolsData[toolKey]
        toolDialogVisible.value = true
      }
    }
    
    // 复制微信号
    const copyWechatId = async () => {
      try {
        await navigator.clipboard.writeText('zhaxinyu--')
        ElMessage.success('微信号已复制到剪贴板')
      } catch (error) {
        // 降级方案：使用传统方法复制
        const textArea = document.createElement('textarea')
        textArea.value = 'zhaxinyu--'
        document.body.appendChild(textArea)
        textArea.select()
        try {
          document.execCommand('copy')
          ElMessage.success('微信号已复制到剪贴板')
        } catch (err) {
          ElMessage.error('复制失败，请手动复制')
        }
        document.body.removeChild(textArea)
      }
    }

    // 复制联系信息
    const copyContactInfo = () => {
      const contactInfo = `微信号：zhaxinyu--`
      
      navigator.clipboard.writeText(contactInfo).then(() => {
        ElMessage.success('微信号已复制到剪贴板')
        contactDialogVisible.value = false
      }).catch(() => {
        ElMessage.error('复制失败，请手动复制')
      })
    }

    // 打开赞助链接
    const openSponsorLink = () => {
      window.open('https://www.tkyds.com/?=shukeCyp', '_blank')
    }

    // 切换微信弹窗
    const toggleWechatDialog = () => {
      wechatDialogVisible.value = true
    }

    // 切换交流群弹窗
    const toggleGroupDialog = () => {
      groupDialogVisible.value = true
    }

    // 检查是否应该显示赞助弹窗
    const checkSponsorDialog = () => {
      // 延迟3秒后显示赞助弹窗
      setTimeout(() => {
        sponsorDialogVisible.value = true
      }, 3000)
    }
    
    onMounted(() => {
      checkHealth()
      checkSponsorDialog()
    })

    return {
      activeMenu,
      healthStatus,
      healthChecking,
      contactDialogVisible,
      sponsorDialogVisible,
      wechatDialogVisible,
      groupDialogVisible, // 新增：返回交流群弹窗可见性
      toolDialogVisible,
      currentTool,
      handleMenuSelect,
      checkHealth,
      contactUs,
      copyContactInfo,
      openSponsorLink,
      toggleWechatDialog,
      toggleGroupDialog, // 新增：返回切换交流群弹窗的方法
      showToolDialog,
      copyWechatId
    }
  }
}
</script>

<style>
/* 全局样式变量 */
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --secondary-gradient: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-gradient: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  --text-primary: #1a202c;
  --text-secondary: #718096;
  --text-muted: #a0aec0;
  --border-color: #e2e8f0;
  --border-light: #f1f5f9;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 30px rgba(0, 0, 0, 0.12);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  height: 100vh;
  background: var(--bg-gradient);
  color: var(--text-primary);
}

.app-container {
  min-height: 100vh;
  background: var(--bg-gradient);
}

/* 顶部导航栏样式 */
.app-header {
  background: var(--bg-primary);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
  padding: 0;
  box-shadow: var(--shadow-md);
  position: relative;
  z-index: 1000;
}

.app-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--primary-gradient);
  opacity: 0.1;
  z-index: -1;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 32px;
  backdrop-filter: blur(10px);
  position: relative;
}

.logo {
  display: flex;
  align-items: center;
  gap: 16px;
  font-weight: 700;
}

.logo .logo-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
}

.logo h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.center-slogan {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-slogan {
  font-size: 20px;
  font-weight: 500;
  letter-spacing: 0.5px;
  white-space: nowrap;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-actions {
  display: flex;
  align-items: center;
}

.header-actions .el-button {
  border-radius: var(--radius-md);
  font-weight: 500;
  padding: 12px 20px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  color: var(--text-primary) !important;
  transition: var(--transition);
}

.header-actions .el-button:hover {
  background: rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

/* 侧边栏样式 */
.app-sidebar {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(20px);
  position: relative;
}

.app-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--secondary-gradient);
  opacity: 0.03;
  z-index: -1;
}

.sidebar-menu {
  border-right: none;
  height: 100%;
  background: transparent;
  padding: 16px 0;
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 16px;
  border-radius: var(--radius-md);
  font-weight: 500;
  color: var(--text-secondary);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.sidebar-menu .el-menu-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--primary-gradient);
  transition: var(--transition);
  opacity: 0.1;
  z-index: -1;
}

.sidebar-menu .el-menu-item:hover::before {
  left: 0;
}

.sidebar-menu .el-menu-item:hover {
  background-color: rgba(102, 126, 234, 0.08);
  color: var(--text-primary);
  transform: translateX(4px);
}

.sidebar-menu .el-sub-menu__title {
  height: 48px;
  line-height: 48px;
  font-weight: 600;
  margin: 4px 16px;
  border-radius: var(--radius-md);
  color: var(--text-primary);
  transition: var(--transition);
}

.sidebar-menu .el-sub-menu__title:hover {
  background-color: rgba(102, 126, 234, 0.05);
  transform: translateX(2px);
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--primary-gradient);
  color: white;
  border-right: none;
  box-shadow: var(--shadow-sm);
  transform: translateX(2px);
}

.sidebar-menu .el-menu-item.is-active::before {
  left: 0;
  opacity: 0.2;
}

.sidebar-menu .el-sub-menu .el-menu-item {
  height: 40px;
  line-height: 40px;
  padding-left: 60px !important;
  font-size: 14px;
  margin: 2px 16px;
  font-weight: 400;
}

.sidebar-menu .el-sub-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.8) 0%, rgba(118, 75, 162, 0.8) 100%);
  color: white;
  font-weight: 500;
  box-shadow: var(--shadow-sm);
}

/* 主内容区域样式 */
.app-main {
  background: transparent;
  padding: 0;
  overflow-y: auto;
  position: relative;
  height: calc(100vh - 64px);
  max-height: calc(100vh - 64px);
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
}

.page-content {
  animation: fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 工具分享界面样式 */
.tools-share-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}

.tools-share-page .page-header {
  background: var(--primary-gradient);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  margin-bottom: 24px;
  padding: 32px;
  position: relative;
  overflow: hidden;
}



.tools-share-page .header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 工具分享页面标题样式 */
.tools-share-page .title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tools-share-page .title-icon {
  width: 64px;
  height: 64px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.tools-share-page .page-title {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: white;
}

.tools-share-page .status-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tools-share-page .page-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  font-weight: 400;
}

.tools-container {
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  min-height: 300px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.tool-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--border-light);
  overflow: hidden;
  transition: var(--transition);
  cursor: pointer;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
  border-color: rgba(102, 126, 234, 0.3);
}

.tool-image {
  width: 100%;
  aspect-ratio: 4/3;
  overflow: hidden;
  position: relative;
}

.tool-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: var(--transition);
}

.tool-card:hover .tool-image img {
  transform: scale(1.05);
}

.tool-content {
  padding: 20px;
}

.tool-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tool-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

/* 工具详情弹窗样式 - 微信风格 */
.tool-dialog .el-dialog {
  border-radius: 24px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important;
  background: white !important;
  overflow: hidden !important;
}

.el-dialog.tool-dialog {
  border-radius: 24px !important;
}

.tool-dialog .el-dialog__header {
  background: white;
  color: var(--text-primary);
  padding: 24px 28px 20px 28px;
  margin: 0;
  border-bottom: 1px solid #f0f0f0;
}

.tool-dialog .el-dialog__title {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 17px;
}

.tool-dialog .el-dialog__headerbtn {
  top: 24px;
  right: 24px;
  width: 28px;
  height: 28px;
  border-radius: 14px;
  background: #f8f8f8;
}

.tool-dialog .el-dialog__close {
  color: #999;
  font-size: 16px;
}

.tool-dialog .el-dialog__body {
  padding: 0 28px 28px 28px;
}

.tool-dialog-content {
  padding: 0;
}

.tool-features {
  margin-bottom: 20px;
}

.tool-features h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.features-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  color: #666;
  font-size: 14px;
}

.feature-icon {
  color: #07c160;
  font-size: 14px;
}

.tool-contact {
  border-top: 1px solid #f0f0f0;
  padding-top: 20px;
}

.wechat-info {
  display: flex;
  justify-content: center;
}

.wechat-id-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 16px;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: var(--transition);
}

.wechat-id-container:hover {
  background: #f0f0f0;
  border-color: #07c160;
  transform: translateY(-1px);
}



.wechat-icon {
  font-size: 32px;
  color: #07c160;
}

.wechat-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.wechat-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.wechat-id {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  user-select: all;
}





.feature-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 32px;
  margin-top: 40px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px 24px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.feature-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--primary-gradient);
  transition: var(--transition);
  opacity: 0.05;
  z-index: -1;
}

.feature-item:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(102, 126, 234, 0.3);
}

.feature-item:hover::before {
  left: 0;
}

.feature-item .el-icon {
  font-size: 32px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: rgba(102, 126, 234, 0.1);
  transition: var(--transition);
}

.feature-item:hover .el-icon {
  background: var(--primary-gradient);
  color: white;
  transform: scale(1.1);
}

.feature-item span {
  font-size: 16px;
  color: var(--text-primary);
  font-weight: 600;
  transition: var(--transition);
}

.feature-item small {
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.4;
  margin-top: 4px;
}

/* 关于我们样式 */
.about-content {
  padding: 60px 40px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.about-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--secondary-gradient);
  opacity: 0.03;
  z-index: -1;
}

.about-content h2 {
  color: var(--text-primary);
  margin-bottom: 32px;
  font-size: 32px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.about-content p {
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.8;
  font-size: 16px;
  font-weight: 400;
}

/* 定制化服务区域样式 */
.services-section {
  max-width: 1200px;
  margin: 60px auto 0;
  padding: 40px;
  background: var(--bg-secondary);
  border-radius: 20px;
  border: 2px solid var(--border-light);
  position: relative;
  overflow: hidden;
}

.services-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--primary-gradient);
  transition: var(--transition);
  opacity: 0.03;
  z-index: -1;
}

.services-section:hover::before {
  left: 0;
}

.services-header {
  text-align: center;
  margin-bottom: 40px;
}

.services-icon {
  font-size: 48px;
  margin-bottom: 20px;
  animation: pulse 2s infinite;
  display: inline-block;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.services-header h3 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 15px;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.services-header p {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 500px;
  margin: 0 auto;
}

.services-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 30px;
  margin: 40px 0;
}

.service-item {
  background: var(--bg-primary);
  padding: 30px;
  border-radius: 16px;
  border: 1px solid var(--border-light);
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.service-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--primary-gradient);
  transition: var(--transition);
  opacity: 0.05;
  z-index: -1;
}

.service-item:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(102, 126, 234, 0.3);
}

.service-item:hover::before {
  left: 0;
}

.service-icon {
  font-size: 36px;
  margin-bottom: 16px;
  display: inline-block;
}

.service-item h4 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.service-item p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.5;
}

.service-item ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.service-item li {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding-left: 20px;
  position: relative;
}

.service-item li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #4ecdc4;
  font-weight: 600;
}

.services-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 30px;
  border-top: 2px dashed var(--border-color);
  gap: 40px;
}

.brand-highlight {
  text-align: center;
  flex: 1;
}

.brand-logo {
  font-size: 36px;
  margin-bottom: 12px;
  display: inline-block;
}

.brand-highlight h4 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-highlight p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 500;
}

.contact-info {
  text-align: center;
  flex: 1;
}

.contact-info p {
  font-size: 16px;
  color: var(--text-secondary);
  margin-bottom: 0;
}

.contact-info .el-button {
  background: var(--primary-gradient);
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 25px;
  transition: var(--transition);
}

.contact-info .el-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}



/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 滚动条样式 */
.app-main::-webkit-scrollbar {
  width: 8px;
}

.app-main::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.app-main::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 4px;
  transition: var(--transition);
}

.app-main::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-wrapper {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .app-sidebar {
    width: 180px !important;
  }
  
  .header-content {
    padding: 0 20px;
  }
  
  .logo h1 {
    font-size: 24px;
  }
  
  .app-main {
    padding: 16px;
  }
  
  .welcome-header {
    padding: 40px 24px;
  }
  
  .welcome-header h2 {
    font-size: 28px;
  }
  
  .about-content {
    padding: 40px 24px;
  }
  
  .feature-list {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .services-section {
    margin: 40px 20px 0;
    padding: 30px 20px;
  }
  
  .services-container {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .services-header h3 {
    font-size: 24px;
  }
  
  .services-footer {
    flex-direction: column;
    gap: 30px;
  }
}

@media (max-width: 480px) {
  .app-sidebar {
    width: 160px !important;
  }
  
  .header-content {
    padding: 0 16px;
  }
  
  .logo h1 {
    font-size: 20px;
  }
  
  .welcome-header h2 {
    font-size: 24px;
  }
  
  .feature-item {
    padding: 24px 16px;
  }
}

/* 联系我们对话框样式 */
.contact-content {
  padding: 20px 0;
}

.contact-simple {
  display: flex;
  gap: 40px;
  align-items: center;
  justify-content: center;
}

.wechat-info {
  flex: 1;
  max-width: 300px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%);
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.contact-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.contact-text {
  flex: 1;
}

.contact-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 4px;
  font-weight: 500;
}

.contact-value {
  color: #303133;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
}

.qrcode-section {
  flex-shrink: 0;
  text-align: center;
}

.qrcode-section h3 {
  color: #409eff;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.qrcode-container {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e4e7ed;
}

.qrcode-image {
  width: 160px;
  height: 160px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 12px;
}

.qrcode-text {
  color: #606266;
  font-size: 14px;
  margin: 0;
  font-weight: 500;
}

/* 联系弹窗响应式设计 */
@media (max-width: 768px) {
  .contact-simple {
    flex-direction: column;
    gap: 30px;
    text-align: center;
  }
  
  .wechat-info {
    max-width: 100%;
  }
  
  .qrcode-image {
    width: 140px;
    height: 140px;
  }
}

@media (max-width: 480px) {
  .contact-item {
    padding: 16px;
  }
  
  .contact-icon {
    font-size: 24px;
  }
  
  .contact-value {
    font-size: 16px;
  }
  
  .qrcode-image {
    width: 120px;
    height: 120px;
  }
}

.contact-item:last-child {
  margin-bottom: 0;
}

.contact-item strong {
  color: #303133;
  min-width: 60px;
  display: inline-block;
}

.contact-footer {
  text-align: right;
}

.contact-footer .el-button {
  margin-left: 12px;
}

/* 友情赞助弹窗样式 */
.sponsor-dialog {
  background: transparent !important;
}

.sponsor-dialog .el-dialog {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  border: none !important;
  margin: 0 !important;
}

.sponsor-dialog .el-dialog__header {
  display: none !important;
}

.sponsor-dialog .el-dialog__body {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
}

.sponsor-dialog .el-dialog__wrapper {
  background: transparent !important;
}

.sponsor-dialog .el-overlay-dialog {
  background: transparent !important;
}

.sponsor-modal {
  background: rgba(0, 0, 0, 0.5) !important;
}

/* 全局覆盖弹窗样式 */
.el-dialog.sponsor-dialog,
.el-dialog.sponsor-dialog .el-dialog__body,
.el-dialog.sponsor-dialog .el-dialog__header,
.sponsor-dialog {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.sponsor-container {
  position: relative;
  padding: 0;
  margin: 0;
  background: transparent;
}

.sponsor-close-btn {
  position: absolute;
  top: -15px;
  right: -15px;
  width: 30px;
  height: 30px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
  color: white;
  font-size: 16px;
}

.sponsor-close-btn:hover {
  background: rgba(0, 0, 0, 0.9);
  transform: scale(1.1);
}

.sponsor-text {
  text-align: center;
  margin-bottom: 20px;
  padding: 0;
}

.sponsor-text h3 {
  color: white;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
}

.sponsor-image-container {
  width: 100%;
  position: relative;
}

.sponsor-link {
  display: block;
  cursor: pointer;
  width: 100%;
}

.sponsor-image {
  width: 100%;
  height: auto;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: block;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.sponsor-image:hover {
  transform: scale(1.02);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
}

/* 响应式设计 */
@media (max-width: 480px) {
  .sponsor-text {
    margin-bottom: 15px;
    padding: 12px 15px;
    border-radius: 12px;
  }
  
  .sponsor-text h3 {
    font-size: 14px;
  }
  
  .sponsor-image {
    border-radius: 15px;
  }
}

/* 交流群悬浮窗样式 */
.group-float {
  position: fixed;
  bottom: 100px;
  right: 30px;
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(255, 107, 107, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
  color: white;
}

.group-float:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
}

.group-float span {
  font-size: 10px;
  font-weight: 500;
  margin-top: 2px;
  line-height: 1;
}

/* 作者微信悬浮窗样式 */
.wechat-float {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 60px;
  height: 60px;
  background: var(--primary-gradient);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
  color: white;
}

.wechat-float:hover {
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.wechat-float span {
  font-size: 10px;
  font-weight: 500;
  margin-top: 2px;
  line-height: 1;
}

/* 作者微信弹窗样式 - 与赞助弹窗保持一致 */
.wechat-dialog {
  background: transparent !important;
}

.wechat-dialog .el-dialog {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  border: none !important;
  margin: 0 !important;
}

.wechat-dialog .el-dialog__header {
  display: none !important;
}

.wechat-dialog .el-dialog__body {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
}

.wechat-dialog .el-dialog__wrapper {
  background: transparent !important;
}

.wechat-dialog .el-overlay-dialog {
  background: transparent !important;
}

.wechat-modal {
  background: rgba(0, 0, 0, 0.5) !important;
}

/* 全局覆盖微信弹窗样式 */
.el-dialog.wechat-dialog,
.el-dialog.wechat-dialog .el-dialog__body,
.el-dialog.wechat-dialog .el-dialog__header,
.wechat-dialog {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.wechat-container {
  position: relative;
  padding: 0;
  margin: 0;
  background: transparent;
}

.wechat-close-btn {
  position: absolute;
  top: -15px;
  right: -15px;
  width: 30px;
  height: 30px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
  color: white;
  font-size: 16px;
}

.wechat-close-btn:hover {
  background: rgba(0, 0, 0, 0.9);
  transform: scale(1.1);
}

.wechat-text {
  text-align: center;
  margin-bottom: 20px;
  padding: 0;
}

.wechat-text h3 {
  color: white;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
}

.wechat-image-container {
  width: 100%;
  position: relative;
}

.wechat-image {
  width: 100%;
  height: auto;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: block;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.wechat-image:hover {
  transform: scale(1.02);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
}

/* 悬浮窗响应式设计 */
@media (max-width: 768px) {
  .group-float {
    bottom: 80px;
    right: 20px;
    width: 50px;
    height: 50px;
  }
  
  .group-float .el-icon {
    font-size: 20px;
  }
  
  .group-float span {
    font-size: 9px;
  }
  
  .wechat-float {
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
  }
  
  .wechat-float .el-icon {
    font-size: 20px;
  }
  
  .wechat-float span {
    font-size: 9px;
  }
  
  .wechat-text h3 {
    font-size: 20px;
  }
  
  .wechat-image {
    border-radius: 15px;
  }
}

/* 交流群弹窗样式 */
.group-dialog {
  background: transparent !important;
}

.group-dialog .el-dialog {
  background: transparent !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  border: none !important;
  margin: 0 !important;
}

.group-dialog .el-dialog__header {
  display: none !important;
}

.group-dialog .el-dialog__body {
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
}

.group-dialog .el-dialog__wrapper {
  background: transparent !important;
}

.group-dialog .el-overlay-dialog {
  background: transparent !important;
}

.group-modal {
  background: rgba(0, 0, 0, 0.5) !important;
}

/* 全局覆盖交流群弹窗样式 */
.el-dialog.group-dialog,
.el-dialog.group-dialog .el-dialog__body,
.el-dialog.group-dialog .el-dialog__header,
.group-dialog {
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.group-container {
  position: relative;
  padding: 0;
  margin: 0;
  background: transparent;
}

.group-close-btn {
  position: absolute;
  top: -15px;
  right: -15px;
  width: 30px;
  height: 30px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1000;
  color: white;
  font-size: 16px;
}

.group-close-btn:hover {
  background: rgba(0, 0, 0, 0.9);
  transform: scale(1.1);
}

.group-text {
  text-align: center;
  margin-bottom: 20px;
  padding: 0;
}

.group-text h3 {
  color: white;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
}

.group-image-container {
  width: 100%;
  position: relative;
}

.group-image {
  width: 100%;
  height: auto;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: block;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.group-image:hover {
  transform: scale(1.02);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
}

/* 悬浮窗响应式设计 */
@media (max-width: 768px) {
  .group-float {
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
  }
  
  .group-float .el-icon {
    font-size: 20px;
  }
  
  .group-float span {
    font-size: 9px;
  }
  
  .group-text h3 {
    font-size: 20px;
  }
  
  .group-image {
    border-radius: 15px;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .contact-layout {
    flex-direction: column;
    gap: 20px;
  }
  
  .qrcode-section {
    width: 100%;
  }
  
  .qrcode-image {
    width: 140px;
    height: 140px;
  }
}
</style>