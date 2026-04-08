<template>
  <div class="episode-page">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h2>🎞️ {{ seriesName }} - 分集管理</h2>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建分集
      </el-button>
    </div>

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

    <el-empty v-else-if="episodes.length === 0" description="暂无分集，点击上方按钮创建" />

    <div v-else class="episodes-grid">
      <el-card
        v-for="ep in episodes"
        :key="ep.id"
        class="episode-card"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <div class="episode-title">
              <span class="episode-name">{{ ep.name }}</span>
              <el-tag :type="getStatusType(ep.status)" size="small">
                {{ getStatusText(ep.status) }}
              </el-tag>
            </div>
          </div>
        </template>
        <div class="episode-info">
          <p class="episode-desc">{{ ep.description || '暂无描述' }}</p>
          <div class="episode-tasks" v-if="ep.tasks && ep.tasks.length">
            <p class="tasks-label">任务:</p>
            <div class="tasks-list">
              <TaskStatus
                v-for="task in ep.tasks"
                :key="task.id"
                :task="task"
                @retry="handleRetry(task)"
              />
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 新建分集对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建分集" width="500px">
      <el-form :model="newEpisode" label-width="80px">
        <el-form-item label="分集名称">
          <el-input v-model="newEpisode.name" placeholder="请输入分集名称" />
        </el-form-item>
        <el-form-item label="分集描述">
          <el-input
            v-model="newEpisode.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分集描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Loading, ArrowLeft } from '@element-plus/icons-vue'
import * as api from '@/api'
import TaskStatus from '@/components/TaskStatus.vue'

const router = useRouter()
const route = useRoute()
const seriesId = route.params.id

const loading = ref(false)
const error = ref('')
const seriesName = ref('')
const episodes = ref([])
const showCreateDialog = ref(false)
const submitting = ref(false)
const newEpisode = ref({ name: '', description: '' })

const fetchData = async () => {
  loading.value = true
  error.value = ''
  try {
    const series = await api.getSeriesDetail(seriesId)
    seriesName.value = series.name || `系列 ${seriesId}`

    const data = await api.getEpisodes(seriesId)
    episodes.value = data.episodes || data || []
  } catch (err) {
    error.value = '加载失败: ' + (err.message || '未知错误')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!newEpisode.value.name.trim()) {
    ElMessage.warning('请输入分集名称')
    return
  }
  submitting.value = true
  try {
    await api.createEpisode(seriesId, newEpisode.value)
    ElMessage.success('分集创建成功')
    showCreateDialog.value = false
    newEpisode.value = { name: '', description: '' }
    fetchData()
  } catch (err) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
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

const goBack = () => router.push(`/series/${seriesId}`)

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    pending: '等待中',
    running: '进行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

onMounted(fetchData)
</script>

<style scoped>
.episode-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
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

.episodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.episode-card {
  transition: box-shadow 0.2s;
}

.episode-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.episode-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.episode-name {
  font-weight: 600;
  font-size: 16px;
}

.episode-info {
  padding: 4px 0;
}

.episode-desc {
  color: #606266;
  font-size: 14px;
  margin-bottom: 12px;
}

.episode-tasks {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}

.tasks-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
