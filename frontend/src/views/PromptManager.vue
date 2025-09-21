<template>
  <div class="jimeng-page prompt-manager">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">
            <el-icon size="32"><Collection /></el-icon>
          </div>
          <div class="title-content">
            <h1 class="page-title">提示词管理</h1>
            <p class="page-subtitle">搜索和管理各平台的提示词模板</p>
          </div>
        </div>
        <div class="status-section">
          <!-- 统计卡片 -->
          <div class="stats-grid" v-if="stats">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Platform /></el-icon> 
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_platforms }}</div>
            <div class="stat-label">平台数量</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_prompts }}</div>
            <div class="stat-label">提示词总数</div>
          </div>
        </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选区域 -->
    <div class="search-section">
      <div class="search-controls">
        <div class="platform-select">
          <el-select
            v-model="selectedPlatform"
            placeholder="选择平台"
            @change="handlePlatformChange"
            style="width: 140px"
          >
            <el-option
              v-for="platform in platforms"
              :key="platform.name"
              :label="platform.display_name"
              :value="platform.name"
            />
          </el-select>
        </div>
        
        <div class="search-input">
          <el-input
            v-model="searchQuery"
            placeholder="搜索提示词名称..."
            @keyup.enter="handleSearch"
            @clear="handleSearch"
            clearable
            style="width: 300px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
                  <el-button class="btn-search" @click="handleSearch">
          <el-icon><Search /></el-icon> 搜索
        </el-button>
        </div>
        
        <div class="page-size-select">
          <span>每页显示</span>
          <el-select v-model="pageSize" @change="handlePageSizeChange" style="width: 80px">
            <el-option label="10" :value="10" />
            <el-option label="20" :value="20" />
            <el-option label="50" :value="50" />
            <el-option label="100" :value="100" />
          </el-select>
          <span>条</span>
        </div>
      </div>
    </div>

    <!-- 提示词列表 -->
    <div class="prompt-list-container">
      <el-card class="list-card" v-loading="loading">
        <template #header>
          <div class="card-header">
            <span>提示词列表</span>
            <el-tag v-if="prompts.length > 0" type="info">
              找到 {{ total }} 个结果
            </el-tag>
          </div>
        </template>

        <!-- 空状态 -->
        <div v-if="!loading && prompts.length === 0" class="empty-state">
          <el-empty
            :image-size="120"
            description="暂无提示词数据"
          >
            <template #description>
              <p>请检查是否存在 <code>prompt_database/{{ selectedPlatform }}/prompt.xlsx</code> 文件</p>
            </template>
          </el-empty>
        </div>

        <!-- 提示词网格 -->
        <div v-else class="prompt-grid">
          <div
            v-for="prompt in prompts"
            :key="prompt.name"
            class="prompt-card"
            @click="showPromptDetail(prompt)"
          >
                         <div class="prompt-image" v-if="prompt.image_base64">
               <img :src="prompt.image_base64" :alt="prompt.name" />
             </div>
             <div class="prompt-image placeholder" v-else>
               <el-icon><Picture /></el-icon>
             </div>
            
            <div class="prompt-content">
              <div class="prompt-name" :title="prompt.name">{{ prompt.name }}</div>
              <div class="prompt-text" :title="prompt.prompt">{{ truncateText(prompt.prompt, 80) }}</div>
            </div>
            
            <div class="prompt-actions">
              <el-button class="btn-copy" size="small" @click.stop="copyPrompt(prompt.prompt)">
                <el-icon><CopyDocument /></el-icon> 复制
              </el-button>
              <el-button class="btn-view" size="small" @click.stop="showPromptDetail(prompt)">
                <el-icon><View /></el-icon> 查看
              </el-button>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="total > 0" class="pagination-container">
          <el-pagination
            :current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            :small="false"
            :disabled="loading"
            :background="true"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handlePageSizeChange"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 提示词详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedPrompt?.name || '提示词详情'"
      width="600px"
      :before-close="closeDetailDialog"
    >
      <div v-if="selectedPrompt" class="prompt-detail">
        <div class="detail-section">
          <h4>提示词名称</h4>
          <p>{{ selectedPrompt.name }}</p>
        </div>
        
                 <div class="detail-section" v-if="selectedPrompt.image_base64">
           <h4>参考图片</h4>
           <div class="detail-image">
             <img :src="selectedPrompt.image_base64" :alt="selectedPrompt.name" />
           </div>
         </div>
        
        <div class="detail-section">
          <h4>提示词内容</h4>
          <div class="prompt-content-box">
            <pre>{{ selectedPrompt.prompt }}</pre>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button type="info" @click="closeDetailDialog">
            关闭
          </el-button>
          <el-button class="btn-copy" @click="copyPrompt(selectedPrompt?.prompt)">
            <el-icon><CopyDocument /></el-icon> 复制提示词
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Collection, Platform, Document, Search, Picture, 
  CopyDocument, View 
} from '@element-plus/icons-vue'
import { promptAPI } from '@/utils/api'
export default {
  name: 'PromptManager',
  components: {
    Collection, Platform, Document, Search, Picture,
    CopyDocument, View
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const searchQuery = ref('')
    const selectedPlatform = ref('jimeng')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    
    const platforms = ref([])
    const prompts = ref([])
    const stats = ref(null)
    
    const detailDialogVisible = ref(false)
    const selectedPrompt = ref(null)

    // 获取平台列表
    const loadPlatforms = async () => {
      try {
        const response = await promptAPI.getPlatforms()
        if (response.data.success) {
          platforms.value = response.data.data
          // 如果当前选择的平台不存在，设置为第一个可用平台
          if (platforms.value.length > 0) {
            const platformNames = platforms.value.map(p => p.name)
            if (!platformNames.includes(selectedPlatform.value)) {
              selectedPlatform.value = platforms.value[0].name
            }
          }
        }
      } catch (error) {
        console.error('获取平台列表失败:', error)
        ElMessage.error('获取平台列表失败')
      }
    }

    // 获取统计信息
    const loadStats = async () => {
      try {
        const response = await promptAPI.getStats()
        if (response.data.success) {
          stats.value = response.data.data
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    }

    // 搜索提示词
    const searchPrompts = async () => {
      if (!selectedPlatform.value) return
      
      loading.value = true
      try {
        const response = await promptAPI.searchPrompts(
          selectedPlatform.value,
          searchQuery.value,
          currentPage.value,
          pageSize.value
        )
        
        if (response.data.success) {
          const data = response.data.data
          prompts.value = data.prompts || []
          total.value = data.total || 0
          currentPage.value = data.page || 1
        } else {
          ElMessage.error(response.data.message || '搜索失败')
          prompts.value = []
          total.value = 0
        }
      } catch (error) {
        console.error('搜索提示词失败:', error)
        ElMessage.error('搜索提示词失败')
        prompts.value = []
        total.value = 0
      } finally {
        loading.value = false
      }
    }

    // 事件处理
    const handleSearch = () => {
      currentPage.value = 1
      searchPrompts()
    }

    const handlePlatformChange = () => {
      currentPage.value = 1
      searchQuery.value = ''
      searchPrompts()
    }

    const handlePageChange = (page) => {
      currentPage.value = page
      searchPrompts()
    }

    const handlePageSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      searchPrompts()
    }

    // 显示提示词详情
    const showPromptDetail = (prompt) => {
      selectedPrompt.value = prompt
      detailDialogVisible.value = true
    }

    const closeDetailDialog = () => {
      detailDialogVisible.value = false
      selectedPrompt.value = null
    }

    // 复制提示词
    const copyPrompt = async (promptText) => {
      if (!promptText) {
        ElMessage.warning('没有可复制的内容')
        return
      }
      
      try {
        await navigator.clipboard.writeText(promptText)
        ElMessage.success('提示词已复制到剪贴板')
      } catch (error) {
        console.error('复制失败:', error)
        ElMessage.error('复制失败，请手动复制')
      }
    }

    // 工具函数
    const truncateText = (text, maxLength) => {
      if (!text) return ''
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    }

    // 生命周期
    onMounted(async () => {
      await loadPlatforms()
      await loadStats()
      if (selectedPlatform.value) {
        await searchPrompts()
      }
    })

    return {
      loading,
      searchQuery,
      selectedPlatform,
      currentPage,
      pageSize,
      total,
      platforms,
      prompts,
      stats,
      detailDialogVisible,
      selectedPrompt,
      handleSearch,
      handlePlatformChange,
      handlePageChange,
      handlePageSizeChange,
      showPromptDetail,
      closeDetailDialog,
      copyPrompt,
      truncateText
    }
  }
}
</script>

<style scoped>
@import '../styles/jimeng-common.css';

/* 提示词管理页面特定样式 */
.title-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 统计卡片样式 */
.stats-grid {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: rgba(78, 205, 196, 0.1);
  color: #4ecdc4;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1;
}

/* 原有样式保持 */
.page-title {
  font-size: 28px;
  font-weight: 600;
  color: white;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-description {
  color: var(--text-secondary);
  margin: 0;
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  max-width: 600px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* 搜索区域样式 */
.search-section {
  margin-bottom: 24px;
}

.search-controls {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.search-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-btn {
  border-radius: 8px;
}

.page-size-select {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  margin-left: auto;
}

/* 列表区域样式 */
.prompt-list-container {
  margin-bottom: 20px;
}

.list-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.empty-state code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

/* 提示词网格样式 */
.prompt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  padding: 0;
}

.prompt-card {
  background: #fafbfc;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prompt-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.prompt-image {
  width: 100%;
  height: 120px;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}

.prompt-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.prompt-image.placeholder {
  color: var(--text-muted);
  font-size: 32px;
}

.prompt-content {
  flex: 1;
}

.prompt-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prompt-text {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.prompt-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #e1e8ed;
}

.prompt-actions .el-button {
  flex: 1;
  border-radius: 6px;
}

/* 分页样式 */
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 详情对话框样式 */
.prompt-detail {
  padding: 0;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 8px 0;
  color: var(--text-primary);
  font-weight: 600;
}

.detail-section p {
  margin: 0;
  color: var(--text-secondary);
}

.detail-image {
  text-align: center;
}

.detail-image img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  border: 1px solid #e1e8ed;
}

.prompt-content-box {
  background: #f5f7fa;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.prompt-content-box pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  color: var(--text-primary);
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .prompt-manager {
    padding: 16px;
  }
  
  .search-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    justify-content: stretch;
  }
  
  .search-input .el-input {
    flex: 1;
  }
  
  .page-size-select {
    margin-left: 0;
    justify-content: center;
  }
  
  .prompt-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style> 