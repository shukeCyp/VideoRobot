<template>
  <div class="jimeng-page jimeng-account-manager-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-info">
        <h2 class="page-title">即梦账号管理</h2>
        <p class="page-subtitle">管理即梦平台的登录账号，支持批量导入和统一管理</p>
      </div>
      <div class="header-actions">
        <el-button 
          class="btn-batch-add primary-btn"
          @click="showAddDialog = true"
          size="large"
        >
          <el-icon><Plus /></el-icon>
          批量添加
        </el-button>
        <el-button 
          @click="refreshAccounts"
          :loading="loading"
          size="large"
          class="refresh-btn"
        >
          <el-icon><Refresh /></el-icon>
          刷新列表
        </el-button>

        <el-popconfirm
          title="确定要清空所有即梦账号吗？此操作不可恢复！"
          @confirm="clearAllAccounts"
          confirm-button-text="确定清空"
          cancel-button-text="取消"
          confirm-button-type="danger"
        >
          <template #reference>
            <el-button 
              class="btn-clear danger-btn"
              :disabled="accounts.length === 0"
              size="large"
            >
              <el-icon><Delete /></el-icon>
              清空所有
            </el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview" v-if="!loading">
      <div class="stats-grid">
        <div class="stat-card primary">
          <div class="stat-icon">
            <el-icon size="24"><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ accounts.length }}</div>
            <div class="stat-label">总账号数</div>
          </div>
        </div>
        
        <!-- 文生图统计 -->
        <div class="stat-card warning">
          <div class="stat-icon">
            <el-icon size="24"><Picture /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ usageStats.summary?.today_usage?.text2img || 0 }}/{{ usageStats.summary?.remaining?.text2img + (usageStats.summary?.today_usage?.text2img || 0) }}</div>
            <div class="stat-label">文生图已用/总量</div>
          </div>
        </div>
        
        <!-- 图生视频统计 -->
        <div class="stat-card danger">
          <div class="stat-icon">
            <el-icon size="24"><VideoPlay /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ usageStats.summary?.today_usage?.img2video || 0 }}/{{ usageStats.summary?.remaining?.img2video + (usageStats.summary?.today_usage?.img2video || 0) }}</div>
            <div class="stat-label">图生视频已用/总量</div>
          </div>
        </div>
        
        <!-- 数字人统计 -->
        <div class="stat-card success">
          <div class="stat-icon">
            <el-icon size="24"><Avatar /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ usageStats.summary?.today_usage?.digital_human || 0 }}/{{ usageStats.summary?.remaining?.digital_human + (usageStats.summary?.today_usage?.digital_human || 0) }}</div>
            <div class="stat-label">数字人已用/总量</div>
          </div>
        </div>
          </div>
          </div>

    <!-- 筛选和操作栏 -->
    <div class="filter-section" v-if="!loading">
      <div class="filter-left">
        <el-select
          v-model="cookieStatusFilter"
          placeholder="选择Cookie状态"
          clearable
          style="width: 200px"
          @change="handleFilterChange"
        >
          <el-option label="全部" value=""></el-option>
          <el-option label="已设置" value="true"></el-option>
          <el-option label="未设置" value="false"></el-option>
        </el-select>
      </div>
    </div>

    <!-- 状态提示 -->
    <div class="status-section" v-if="statusMessage">
      <el-alert
        :title="statusMessage"
        :type="statusType"
        :closable="true"
        @close="clearStatus"
        show-icon
        class="status-alert"
      />
    </div>

    <!-- 账号列表 -->
    <div class="account-table-container">
      <!-- 空状态 -->
      <el-empty 
        v-if="filteredAccounts.length === 0 && !loading" 
        description="暂无即梦账号数据"
        class="empty-state"
      >
        <el-button 
          class="btn-add-first"
          @click="showAddDialog = true"
          :icon="Plus"
        >
          添加第一个账号
        </el-button>
      </el-empty>

      <!-- 账号表格 -->
      <el-table 
        v-else
        :data="filteredPaginatedAccounts" 
        stripe 
        v-loading="loading"
        class="account-table"
        :default-sort="{ prop: 'id', order: 'ascending' }"
        @selection-change="handleSelectionChange"
      >
        <el-table-column 
          type="selection"
          width="55"
        />
        <el-table-column 
          prop="id" 
          label="ID" 
          width="70" 
          align="center"
          sortable
        />
        <el-table-column 
          prop="account" 
          label="账号"
          min-width="200"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <div class="account-cell">
              <el-icon color="#409EFF"><Message /></el-icon>
              <span>{{ row.account }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column 
          prop="cookies" 
          label="Cookies状态" 
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tooltip
              :content="row.has_cookies ? '已设置Cookie' : '未设置Cookie'"
              placement="top"
            >
            <el-tag 
                :type="row.has_cookies ? 'success' : 'info'" 
              size="small"
                effect="dark"
            >
                {{ row.has_cookies ? '已设置' : '未设置' }}
            </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column 
          label="今日使用情况" 
          width="200"
          align="center"
        >
          <template #default="{ row }">
            <div class="usage-details">
              <div class="usage-item">
                <span class="usage-label">图片:</span>
                <span class="usage-value">{{ row.today_usage?.text2img || 0 }}/{{ row.daily_limits?.text2img || 50 }}</span>
              <el-progress 
                  :percentage="((row.today_usage?.text2img || 0) / (row.daily_limits?.text2img || 50)) * 100" 
                  :stroke-width="3"
                :show-text="false"
                  :color="getUsageColor(row.today_usage?.text2img || 0, row.daily_limits?.text2img || 50)"
                />
              </div>
              <div class="usage-item">
                <span class="usage-label">视频:</span>
                <span class="usage-value">{{ row.today_usage?.img2video || 0 }}/{{ row.daily_limits?.img2video || 2 }}</span>
                <el-progress 
                  :percentage="((row.today_usage?.img2video || 0) / (row.daily_limits?.img2video || 2)) * 100" 
                  :stroke-width="3"
                  :show-text="false"
                  :color="getUsageColor(row.today_usage?.img2video || 0, row.daily_limits?.img2video || 2)"
                />
              </div>
              <div class="usage-item">
                <span class="usage-label">数字人:</span>
                <span class="usage-value">{{ row.today_usage?.digital_human || 0 }}/{{ row.daily_limits?.digital_human || 1 }}</span>
                <el-progress 
                  :percentage="((row.today_usage?.digital_human || 0) / (row.daily_limits?.digital_human || 1)) * 100" 
                  :stroke-width="3"
                  :show-text="false"
                  :color="getUsageColor(row.today_usage?.digital_human || 0, row.daily_limits?.digital_human || 1)"
              />
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column 
          label="状态" 
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag 
              :type="getAccountStatus(row) === 'available' ? 'success' : 'danger'"
              size="small"
            >
              {{ getAccountStatus(row) === 'available' ? '可用' : '已满' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column 
          label="操作" 
          width="240" 
          fixed="right"
          align="center"
        >
          <template #default="{ row }">
            <div class="action-buttons">

              <el-button 
                type="success" 
                size="small" 
                text
                @click="loginAccount(row.id)"
                :loading="loginLoading[row.id]"
              >
                登录
              </el-button>
            <el-popconfirm
              :title="`确定删除账号 ${row.account} 吗？`"
              @confirm="deleteAccount(row.id)"
              confirm-button-text="删除"
              cancel-button-text="取消"
              confirm-button-type="danger"
            >
              <template #reference>
                <el-button 
                  class="btn-delete"
                  size="small" 
                  text
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container" v-if="filteredAccounts.length > 0">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredAccounts.length"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 添加账号对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="批量添加即梦国际版账号"
      width="700px"
      @close="resetAddForm"
      class="add-dialog"
    >
      <div class="add-form">
        <!-- 格式说明卡片 -->
        <el-card shadow="never" class="format-card">
          <template #header>
            <div class="card-header">
              <el-icon><DocumentAdd /></el-icon>
              <span>输入格式说明</span>
            </div>
          </template>
          
          <div class="format-examples">
            <div class="format-item">
              <el-tag type="danger" size="small">格式1</el-tag>
              <code>账号----密码</code>
            </div>
            <div class="format-item">
              <el-tag type="success" size="small">格式2</el-tag>
              <code>账号----密码----cookies</code>
            </div>
          </div>
          
          <div class="format-note">
            <el-icon color="#E6A23C"><Warning /></el-icon>
            <span>每行一个账号，使用 ---- 分隔各字段</span>
          </div>
        </el-card>

        <!-- 输入区域 -->
        <div class="input-section">
          <el-input
            v-model="newAccountsText"
            type="textarea"
            :rows="8"
            placeholder="请按上述格式输入账号信息，例如：&#10;user1@email.com----password123&#10;user2@email.com----password456----cookie_data_here"
            class="account-input"
            show-word-limit
            :maxlength="10000"
          />
          
          <div class="input-stats">
            <span class="line-count">
              行数: {{ newAccountsText.split('\n').filter(line => line.trim()).length }}
            </span>
          </div>
        </div>

        <!-- 对话框按钮 -->
        <div class="dialog-actions">
          <el-button @click="showAddDialog = false" size="default">
            取消
          </el-button>
          <el-button 
            class="btn-confirm-add"
            @click="addAccounts"
            :loading="addLoading"
            :disabled="!newAccountsText.trim()"
            size="default"
          >
            <el-icon><Plus /></el-icon>
            确认添加
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, onActivated } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Refresh, 
  Delete, 
  User,
  Message,
  View,
  Hide,
  DocumentAdd,
  Warning,
  Picture,
  VideoPlay,
  Avatar
} from '@element-plus/icons-vue'
import { accountAPI } from '../utils/api'

export default {
  name: 'JimengAccountManager',
  components: {
    Plus,
    Refresh,
    Delete,
    User,
    Message,
    View,
    Hide,
    DocumentAdd,
    Warning,
    Picture,
    VideoPlay,
    Avatar
  },
  setup() {
    // 响应式数据
    const accounts = ref([])
    const loading = ref(false)
    const addLoading = ref(false)
    const showAddDialog = ref(false)
    const newAccountsText = ref('')
    const statusMessage = ref('')
    const statusType = ref('success')
    const showPassword = ref({})
    const currentPage = ref(1)
    const pageSize = ref(10)
    const usageStats = ref({
      accounts: [],
      summary: {
        total_accounts: 0,
        available_accounts: 0,
        total_today_usage: 0,
        total_remaining: 0
      }
    })

    // 多选相关
    const selectedAccounts = ref([])
    
    // 处理选择变化
    const handleSelectionChange = (selection) => {
      selectedAccounts.value = selection
    }
    

    
    // 登录状态
    const loginLoading = ref({})
    
    // 登录单个账号
    const loginAccount = async (accountId) => {
      try {
        // 设置加载状态
        loginLoading.value[accountId] = true
        
        const response = await accountAPI.loginAccount(accountId)
        if (response.data.success) {
          ElMessage.success(response.data.message)
        } else {
          ElMessage.error(response.data.message)
        }
      } catch (error) {
        console.error('登录账号失败:', error)
        ElMessage.error('登录账号失败')
      } finally {
        // 延迟一会儿再清除加载状态，让用户有时间看到加载效果
        setTimeout(() => {
          loginLoading.value[accountId] = false
        }, 1000)
      }
    }
    


    // 计算属性
    const paginatedAccounts = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return accounts.value.slice(start, end)
    })

    // 获取账号列表
    const fetchAccounts = async () => {
      loading.value = true
      try {
        const response = await accountAPI.getAccounts()
        if (response.data.success) {
          accounts.value = response.data.data
          setStatus(response.data.message, 'success')
        } else {
          setStatus(response.data.message, 'error')
        }
      } catch (error) {
        console.error('获取账号失败:', error)
        setStatus('获取账号失败，请检查后端服务是否正常运行', 'error')
      } finally {
        loading.value = false
      }
    }

    // 刷新账号
    const refreshAccounts = () => {
      fetchAccounts()
    }

    // 添加账号
    const addAccounts = async () => {
      if (!newAccountsText.value.trim()) {
        ElMessage.warning('请输入账号信息')
        return
      }

      addLoading.value = true
      try {
        const response = await accountAPI.addAccounts(newAccountsText.value)
        if (response.data.success) {
          setStatus(response.data.message, 'success')
          showAddDialog.value = false
          resetAddForm()
          await fetchAccounts()
        } else {
          setStatus(response.data.message, 'error')
        }
      } catch (error) {
        console.error('添加账号失败:', error)
        setStatus('添加账号失败', 'error')
      } finally {
        addLoading.value = false
      }
    }

    // 删除账号
    const deleteAccount = async (accountId) => {
      try {
        const response = await accountAPI.deleteAccount(accountId)
        if (response.data.success) {
          setStatus(response.data.message, 'success')
          await fetchAccounts()
        } else {
          setStatus(response.data.message, 'error')
        }
      } catch (error) {
        console.error('删除账号失败:', error)
        setStatus('删除账号失败', 'error')
      }
    }

    // 清空所有账号
    const clearAllAccounts = async () => {
      try {
        const response = await accountAPI.clearAllAccounts()
        if (response.data.success) {
          setStatus(response.data.message, 'warning')
          await fetchAccounts()
          currentPage.value = 1
        } else {
          setStatus(response.data.message, 'error')
        }
      } catch (error) {
        console.error('清空账号失败:', error)
        setStatus('清空账号失败', 'error')
      }
    }

    // 切换密码显示
    const togglePassword = (accountId) => {
      showPassword.value[accountId] = !showPassword.value[accountId]
    }

    // 密码遮盖显示
    const maskPassword = (password) => {
      if (!password) return ''
      if (password.length <= 4) return '*'.repeat(password.length)
      return password.substring(0, 2) + '*'.repeat(password.length - 4) + password.substring(password.length - 2)
    }

    // 设置状态消息
    const setStatus = (message, type) => {
      statusMessage.value = message
      statusType.value = type
      setTimeout(clearStatus, 5000)
    }

    // 清除状态消息
    const clearStatus = () => {
      statusMessage.value = ''
    }

    // 重置添加表单
    const resetAddForm = () => {
      newAccountsText.value = ''
    }

    // 分页处理
    const handlePageChange = (page) => {
      currentPage.value = page
    }
    
    // 处理每页显示数量变化
    const handleSizeChange = (size) => {
      pageSize.value = size
      // 如果当前页超出了新的页数范围，重置为第一页
      const maxPage = Math.ceil(filteredAccounts.value.length / size)
      if (currentPage.value > maxPage) {
        currentPage.value = 1
      }
    }

    // 获取使用统计
    const fetchUsageStats = async () => {
      try {
        const response = await accountAPI.getUsageStats()
        if (response.data.success) {
          usageStats.value = response.data.data
        } else {
          console.error('获取使用统计失败:', response.data.message)
        }
      } catch (error) {
        console.error('获取使用统计异常:', error)
      }
    }

    // 刷新所有数据
    const refreshAll = async () => {
      await Promise.all([
        fetchAccounts(),
        fetchUsageStats()
      ])
    }

    // 获取账号使用情况
    const getAccountUsage = (accountId) => {
      const usage = usageStats.value.accounts.find(acc => acc.id === accountId)
      return usage || {
        today_text2img: 0,
        today_remaining: 10,
        status: 'available'
      }
    }

    // 获取使用情况颜色
    const getUsageColor = (usage, limit) => {
      const percentage = (usage / limit) * 100
      if (percentage >= 100) return '#f56c6c'  // 红色 - 已满
      if (percentage >= 80) return '#e6a23c'   // 橙色 - 接近上限
      if (percentage >= 50) return '#409eff'   // 蓝色 - 中等使用
      return '#67c23a'                         // 绿色 - 使用较少
    }

    // 获取账号状态
    const getAccountStatus = (account) => {
      // 如果任何一种类型达到限制，账号就视为已满
      if (!account.today_usage || !account.daily_limits) return 'available'
      
      const textImgFull = (account.today_usage.text2img || 0) >= (account.daily_limits.text2img || 50)
      const videoFull = (account.today_usage.img2video || 0) >= (account.daily_limits.img2video || 2)
      const digitalHumanFull = (account.today_usage.digital_human || 0) >= (account.daily_limits.digital_human || 1)
      
      return (textImgFull || videoFull || digitalHumanFull) ? 'limit_reached' : 'available'
    }

    // 生命周期
    onMounted(refreshAll)
    onActivated(refreshAll)

    // Cookie状态筛选
    const cookieStatusFilter = ref('')
    
    // 处理筛选变化
    const handleFilterChange = () => {
      currentPage.value = 1 // 重置到第一页
    }
    
    // 筛选后的账号列表
    const filteredAccounts = computed(() => {
      if (!cookieStatusFilter.value) {
        return accounts.value
      }
      
      const hasFilter = cookieStatusFilter.value === 'true'
      return accounts.value.filter(account => account.has_cookies === hasFilter)
    })

    // 筛选并分页后的账号列表
    const filteredPaginatedAccounts = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return filteredAccounts.value.slice(start, end)
    })

    return {
      accounts,
      loading,
      addLoading,
      showAddDialog,
      newAccountsText,
      statusMessage,
      statusType,
      showPassword,
      currentPage,
      pageSize,
      usageStats,
      paginatedAccounts,
      filteredAccounts,
      filteredPaginatedAccounts,
      cookieStatusFilter,
      fetchAccounts,
      refreshAccounts,
      addAccounts,
      deleteAccount,
      clearAllAccounts,
      togglePassword,
      maskPassword,
      setStatus,
      clearStatus,
      resetAddForm,
      handlePageChange,
      handleSizeChange,
      handleFilterChange,
      fetchUsageStats,
      refreshAll,
      getAccountUsage,
      getUsageColor,
      getAccountStatus,
      selectedAccounts,
      handleSelectionChange,
      loginLoading,
      loginAccount,
    }
  }
}
</script>

<style scoped>
.jimeng-account-manager-page {
  padding: 24px;
  min-height: 100vh;
  background: transparent;
}

/* 页面头部 */
.page-header {
  max-width: 1200px;
  margin: 0 auto 24px auto;
  background: var(--bg-primary);
  padding: 24px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--success-gradient);
  opacity: 0.03;
  z-index: -1;
}

.header-info {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  background: var(--success-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.primary-btn {
  background: var(--primary-gradient);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.refresh-btn {
  background: var(--accent-gradient);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}



.danger-btn {
  background: var(--danger-gradient);
  border: none;
  color: white;
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: var(--transition);
  box-shadow: var(--shadow-sm);
}

.danger-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* 统计概览 */
.stats-overview {
  max-width: 1200px;
  margin: 0 auto 32px auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 32px;
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.stats-grid::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--secondary-gradient);
  opacity: 0.02;
  z-index: -1;
}

.stat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
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

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: rgba(102, 126, 234, 0.3);
}

.stat-card:hover::before {
  left: 0;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: var(--transition);
}

.stat-card.primary .stat-icon {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.stat-card.success .stat-icon {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.stat-card.warning .stat-icon {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

.stat-card.danger .stat-icon {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.stat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
  margin: 0;
}

/* 筛选和操作栏 */
.filter-section {
  max-width: 1200px;
  margin: 0 auto 24px auto;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 20px 32px;
  box-shadow: var(--shadow-lg);
  display: flex;
  justify-content: flex-start;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.filter-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--accent-gradient);
  opacity: 0.02;
  z-index: -1;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-left .el-select {
  width: 200px;
}

/* 状态提示 */
.status-section {
  margin-bottom: 24px;
}

.status-alert {
  border-radius: var(--radius-md);
}

/* 操作栏样式 */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.left-actions, .right-actions {
  display: flex;
  gap: 12px;
}

/* 统计信息样式 */
.stats-bar {
  margin-bottom: 20px;
}

.stats-card {
  border: none;
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.stat-value {
  color: #2c3e50;
  font-weight: 600;
  font-size: 16px;
}

.stat-divider {
  width: 1px;
  height: 20px;
  background: #e4e7ed;
}

/* 状态提示样式 */
.status-alert {
  margin-bottom: 20px;
  border-radius: 8px;
}

/* 表格容器样式 */
.account-table-container {
  max-width: 1200px;
  margin: 0 auto;
  overflow-x: auto;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.account-table {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}

.account-table :deep(.el-table__header-wrapper th) {
  background-color: #f8fafc;
  color: #374151;
  font-weight: 600;
}

.account-table :deep(.el-table__header-wrapper th:first-child) {
  border-top-left-radius: 12px;
}

.account-table :deep(.el-table__header-wrapper th:last-child) {
  border-top-right-radius: 12px;
}

.account-table :deep(.el-table__body-wrapper tr:last-child td:first-child) {
  border-bottom-left-radius: 12px;
}

.account-table :deep(.el-table__body-wrapper tr:last-child td:last-child) {
  border-bottom-right-radius: 12px;
}

.account-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.password-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.masked-password, .real-password {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.masked-password {
  color: #999;
}

.password-toggle {
  padding: 2px !important;
  min-height: auto !important;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

/* 对话框样式 */
.add-dialog .el-dialog__body {
  padding: 20px 24px;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.format-card {
  border: 1px solid #e1f3ff;
  background: #f6fbff;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #409EFF;
}

.format-examples {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.format-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.format-item code {
  background: #f0f2f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #2c3e50;
}

.format-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fdf6ec;
  border-left: 4px solid #E6A23C;
  border-radius: 4px;
  font-size: 13px;
  color: #E6A23C;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.account-input {
  font-family: 'Courier New', monospace;
}

.input-stats {
  display: flex;
  justify-content: flex-end;
  font-size: 12px;
  color: #999;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 使用情况样式 */
.usage-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 0;
}

.usage-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.usage-label {
  font-weight: 500;
  color: var(--el-text-color-regular);
  min-width: 40px;
  text-align: right;
}

.usage-value {
  font-weight: 600;
  color: var(--el-text-color-primary);
  min-width: 30px;
}

.usage-item .el-progress {
  flex: 1;
  min-width: 60px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .jimeng-account-manager {
    padding: 16px;
  }

  .action-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .left-actions, .right-actions {
    justify-content: center;
  }

  .stats-content {
    justify-content: center;
  }

  .add-dialog {
    width: 95% !important;
  }
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.action-buttons .el-button {
  margin: 0;
}

.el-button.el-button--text.el-button--primary {
  font-weight: 500;
}

/* 登录按钮样式 */
.el-button.el-button--text.el-button--success {
  font-weight: 500;
  color: #67c23a;
}

.el-button.el-button--text.el-button--success:hover {
  color: #85ce61;
}


</style>