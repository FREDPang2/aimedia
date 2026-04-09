<template>
  <div class="tasks-page">
    <div class="page-header">
      <h2>📋 任务管理</h2>
      <el-button text @click="fetchData">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 队列概览 -->
    <el-row :gutter="16" class="queue-overview">
      <el-col :span="6">
        <div class="stat-card pending">
          <div class="stat-icon"><el-icon><Clock /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ queueStatus.pending }}</span>
            <span class="stat-label">等待中</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card active">
          <div class="stat-icon"><el-icon class="is-loading"><Loading /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ queueStatus.active }}</span>
            <span class="stat-label">进行中</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card completed">
          <div class="stat-icon"><el-icon style="color:#67c23a"><Check /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ queueStatus.completed }}</span>
            <span class="stat-label">已完成</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card failed">
          <div class="stat-icon"><el-icon style="color:#f56c6c"><Close /></el-icon></div>
          <div class="stat-info">
            <span class="stat-value">{{ queueStatus.failed }}</span>
            <span class="stat-label">失败</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 任务列表 -->
    <el-tabs v-else v-model="activeTab" class="tasks-tabs">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="进行中" name="in_progress" />
      <el-tab-pane label="等待中" name="pending" />
      <el-tab-pane label="失败" name="failed" />
      <el-tab-pane label="已完成" name="completed" />

      <div class="tab-content">
        <el-empty v-if="filteredTasks.length === 0" :description="`暂无${activeTabLabel}的任务`" />

        <el-table
          v-else
          :data="filteredTasks"
          stripe
          style="width: 100%"
          :default-sort="{ prop: 'created_at', order: 'descending' }"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column label="类型" width="120">
            <template #default="{ row }">
              <el-tag size="small">{{ getTaskTypeText(row.task_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="进度" width="180">
            <template #default="{ row }">
              <el-progress
                v-if="row.status === 'in_progress'"
                :percentage="row.progress || 0"
                :stroke-width="8"
                :show-text="true"
              />
              <span v-else-if="row.progress" style="color: #909399; font-size: 12px">
                {{ row.progress }}%
              </span>
              <span v-else style="color: #c0c4cc; font-size: 12px">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="result_url" label="结果" min-width="200">
            <template #default="{ row }">
              <a v-if="row.result_url" :href="row.result_url" target="_blank" class="result-link">
                {{ row.result_url }}
              </a>
              <span v-else style="color: #c0c4cc">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="错误信息" min-width="150">
            <template #default="{ row }">
              <span v-if="row.error_message" style="color: #f56c6c; font-size: 12px">
                {{ row.error_message }}
              </span>
              <span v-else style="color: #c0c4cc">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'failed'"
                size="small"
                type="danger"
                @click="handleRetry(row)"
              >
                重试
              </el-button>
              <el-button
                v-if="row.status === 'in_progress'"
                size="small"
                @click="handlePause(row)"
              >
                暂停
              </el-button>
              <el-button
                v-if="row.status === 'paused'"
                size="small"
                type="success"
                @click="handleResume(row)"
              >
                恢复
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Loading, Clock, Check, Close } from '@element-plus/icons-vue'
import * as api from '@/api'

const loading = ref(false)
const error = ref('')
const activeTab = ref('all')
const tasks = ref([])
const queueStatus = ref({ pending: 0, active: 0, completed: 0, failed: 0 })

const activeTabLabel = computed(() => {
  const map = {
    all: '全部',
    in_progress: '进行中',
    pending: '等待中',
    failed: '失败',
    completed: '已完成'
  }
  return map[activeTab.value]
})

const filteredTasks = computed(() => {
  if (activeTab.value === 'all') return tasks.value
  return tasks.value.filter(t => t.status === activeTab.value)
})

const fetchData = async () => {
  loading.value = true
  error.value = ''
  try {
    const [tasksData, queueData] = await Promise.all([
      api.getTasks().catch(() => []),
      api.getQueueStatus().catch(() => ({ pending: 0, active: 0, completed: 0, failed: 0 }))
    ])
    tasks.value = tasksData || []
    queueStatus.value = queueData
  } catch (err) {
    error.value = '加载失败: ' + err.message
  } finally {
    loading.value = false
  }
}

const handleRetry = async (task) => {
  try {
    await api.retryTask(task.id)
    ElMessage.success('任务已重新提交')
    fetchData()
  } catch (err) {
    ElMessage.error('重试失败')
  }
}

const handlePause = async (task) => {
  try {
    await api.pauseTask(task.id)
    ElMessage.success('任务已暂停')
    fetchData()
  } catch (err) {
    ElMessage.error('暂停失败')
  }
}

const handleResume = async (task) => {
  try {
    await api.resumeTask(task.id)
    ElMessage.success('任务已恢复')
    fetchData()
  } catch (err) {
    ElMessage.error('恢复失败')
  }
}

const getTaskTypeText = (type) => {
  const map = {
    script: '脚本生成',
    voiceover: '配音',
    video: '视频生成',
    subtitle: '字幕生成',
    background_music: '背景音乐',
    compose: '视频合成',
    outline: '大纲生成'
  }
  return map[type] || type || '任务'
}

const getStatusTagType = (status) => {
  const map = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    failed: 'danger',
    paused: 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '等待中',
    in_progress: '进行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return map[status] || status
}

// 定时刷新
let refreshTimer = null
onMounted(() => {
  fetchData()
  // 每10秒自动刷新
  refreshTimer = setInterval(fetchData, 10000)
})
</script>

<style scoped>
.tasks-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 20px;
  color: #303133;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px;
  color: #909399;
}

.queue-overview {
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  font-size: 28px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-card.pending .stat-icon {
  background: #ecf5ff;
  color: #409eff;
}

.stat-card.active .stat-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-card.completed .stat-icon {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-card.failed .stat-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.tasks-tabs {
  background: #fff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tab-content {
  padding-top: 16px;
}

.result-link {
  color: #409eff;
  font-size: 12px;
  word-break: break-all;
  text-decoration: none;
}

.result-link:hover {
  text-decoration: underline;
}
</style>
