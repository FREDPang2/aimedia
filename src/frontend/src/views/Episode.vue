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

    <!-- 系列状态操作栏 -->
    <div class="series-action-bar" v-if="seriesInfo.id">
      <el-tag :type="getSeriesStatusType(seriesInfo.status)">
        状态: {{ getSeriesStatusText(seriesInfo.status) }}
      </el-tag>
      <div class="action-buttons">
        <el-button
          size="small"
          type="primary"
          :loading="generatingScript"
          :disabled="seriesInfo.status === 'script_generating'"
          @click="handleGenerateScript"
        >
          <el-icon><Document /></el-icon> 生成脚本
        </el-button>
        <el-button
          size="small"
          type="success"
          :loading="generatingVideo"
          :disabled="seriesInfo.status !== 'script_generated' && seriesInfo.status !== 'video_generating'"
          @click="handleGenerateVideo"
        >
          <el-icon><VideoPlay /></el-icon> 生成视频
        </el-button>
        <el-button size="small" @click="showScriptDialog = true">
          <el-icon><View /></el-icon> 查看/编辑脚本
        </el-button>
      </div>
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

    <!-- 任务队列概览 -->
    <el-card v-if="queueStatus" class="queue-card" shadow="never">
      <template #header>
        <span class="queue-title">📊 任务队列概览</span>
      </template>
      <div class="queue-stats">
        <div class="stat-item">
          <span class="stat-num">{{ queueStatus.pending }}</span>
          <span class="stat-label">等待中</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ queueStatus.active }}</span>
          <span class="stat-label">进行中</span>
        </div>
        <div class="stat-item">
          <span class="stat-num">{{ queueStatus.completed }}</span>
          <span class="stat-label">已完成</span>
        </div>
        <div class="stat-item">
          <span class="stat-num" style="color: #f56c6c">{{ queueStatus.failed }}</span>
          <span class="stat-label">失败</span>
        </div>
      </div>
    </el-card>

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
              <span class="episode-name">{{ ep.title || `第${ep.episode_number}集` }}</span>
              <el-tag :type="getStatusType(ep.status)" size="small">
                {{ getStatusText(ep.status) }}
              </el-tag>
              <span class="episode-num">#{{ ep.episode_number }}</span>
            </div>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, ep)">
              <el-icon class="more-icon" @click.stop><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="generate-script" divided>
                    <el-icon><Document /></el-icon> 生成脚本
                  </el-dropdown-item>
                  <el-dropdown-item command="generate-video">
                    <el-icon><VideoPlay /></el-icon> 生成视频
                  </el-dropdown-item>
                  <el-dropdown-item command="view-script">
                    <el-icon><View /></el-icon> 查看脚本
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <div class="episode-info">
          <p class="episode-desc">{{ ep.description || '暂无描述' }}</p>

          <!-- 分集任务列表 -->
          <div class="episode-tasks" v-if="ep.tasks && ep.tasks.length">
            <p class="tasks-label">🔄 任务进度:</p>
            <div class="tasks-list">
              <TaskStatus
                v-for="task in ep.tasks"
                :key="task.id"
                :task="task"
                @retry="handleRetry(task)"
                @pause="handlePause(task)"
                @resume="handleResume(task)"
              />
            </div>
          </div>

          <!-- 大纲展示 -->
          <div v-if="ep.outline" class="episode-outline">
            <p class="outline-label">📋 大纲:</p>
            <div class="outline-text">{{ ep.outline }}</div>
          </div>

          <!-- 视频播放器 -->
          <div v-if="ep.video_path && ep.status === 'video_completed'" class="episode-video">
            <p class="video-label">🎬 生成的视频:</p>
            <video
              :src="ep.video_path"
              controls
              width="100%"
              style="border-radius: 6px; background: #000;"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 新建分集对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建分集" width="500px">
      <el-form :model="newEpisode" label-width="90px">
        <el-form-item label="分集标题">
          <el-input v-model="newEpisode.title" placeholder="请输入分集标题" />
        </el-form-item>
        <el-form-item label="集数">
          <el-input-number v-model="newEpisode.episode_number" :min="1" :max="999" />
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

    <!-- 查看/编辑脚本对话框 -->
    <el-dialog v-model="showScriptDialog" title="脚本内容" width="700px">
      <el-input
        v-model="currentScript"
        type="textarea"
        :rows="20"
        placeholder="脚本内容将显示在这里..."
        readonly
      />
      <template #footer>
        <el-button @click="showScriptDialog = false">关闭</el-button>
        <el-button v-if="currentEpisodeId" type="primary" @click="handleSaveScript">
          保存修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Loading, ArrowLeft, MoreFilled, Document, VideoPlay, View } from '@element-plus/icons-vue'
import * as api from '@/api'
import TaskStatus from '@/components/TaskStatus.vue'

const router = useRouter()
const route = useRoute()
const seriesId = route.params.id

const loading = ref(false)
const error = ref('')
const seriesName = ref('')
const seriesInfo = ref({})
const episodes = ref([])
const showCreateDialog = ref(false)
const showScriptDialog = ref(false)
const submitting = ref(false)
const generatingScript = ref(false)
let pollingTimer = null
const generatingVideo = ref(false)
const queueStatus = ref(null)
const currentEpisodeId = ref(null)
const currentScript = ref('')
const newEpisode = ref({ title: '', episode_number: 1, description: '' })

const startPolling = () => {
  stopPolling()
  pollingTimer = setInterval(() => {
    fetchData(false)  // silent refresh, don't show loading
  }, 3000)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const isGenerating = () => generatingScript.value || generatingVideo.value

const fetchData = async (showLoader = true) => {
  if (showLoader) loading.value = true
  error.value = ''
  try {
    const series = await api.getSeriesDetail(seriesId)
    seriesName.value = series.title || `系列 ${seriesId}`
    seriesInfo.value = series

    const data = await api.getEpisodes(seriesId)
    episodes.value = data || []

    // 自动停止轮询：当所有分集都生成完毕
    if (!isGenerating()) {
      const stillGenerating = episodes.value.some(
        ep => ep.status === 'script_generating' || ep.status === 'video_generating'
      )
      if (!stillGenerating) stopPolling()
    }

    // 获取队列状态
    try {
      queueStatus.value = await api.getQueueStatus()
    } catch {}
  } catch (err) {
    error.value = '加载失败: ' + err.message
    console.error(err)
  } finally {
    if (showLoader) loading.value = false
  }
}


const handleCreate = async () => {
  if (!newEpisode.value.title.trim()) {
    ElMessage.warning('请输入分集标题')
    return
  }
  submitting.value = true
  try {
    await api.createEpisode(seriesId, newEpisode.value)
    ElMessage.success('分集创建成功')
    showCreateDialog.value = false
    newEpisode.value = { title: '', episode_number: episodes.value.length + 1, description: '' }
    fetchData()
  } catch (err) {
    ElMessage.error('创建失败: ' + err.message)
  } finally {
    submitting.value = false
  }
}

const handleGenerateScript = async () => {
  try {
    await ElMessageBox.confirm(
      '将为所有分集生成 AI 脚本，这可能需要几分钟时间。是否继续？',
      '生成脚本',
      { type: 'info', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    generatingScript.value = true
    startPolling()
    // 遍历所有分集生成脚本
    const promises = episodes.value.map(ep =>
      api.generateScript(ep.id).catch(err => ({ error: err.message, id: ep.id }))
    )
    const results = await Promise.all(promises)
    const failed = results.filter(r => r.error)
    if (failed.length === 0) {
      ElMessage.success('所有脚本生成任务已提交')
    } else {
      ElMessage.warning(`${failed.length} 个分集生成失败`)
    }
    fetchData()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('生成失败')
  } finally {
    generatingScript.value = false
    if (!isGenerating()) stopPolling()
  }
}

const handleGenerateVideo = async () => {
  try {
    await ElMessageBox.confirm(
      '将为所有已生成脚本的分集生成视频，这可能需要较长时间。是否继续？',
      '生成视频',
      { type: 'info', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    generatingVideo.value = true
    startPolling()
    const promises = episodes.value
      .filter(ep => ep.status === 'script_generated' || ep.status === 'video_generating')
      .map(ep => api.generateVideo(ep.id).catch(() => {}))
    await Promise.all(promises)
    ElMessage.success('视频生成任务已提交')
    fetchData()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('生成失败')
  } finally {
    generatingVideo.value = false
    if (!isGenerating()) stopPolling()
  }
}

const handleCommand = async (cmd, ep) => {
  if (cmd === 'generate-script') {
    try {
      await ElMessageBox.confirm(`为「${ep.title}」生成脚本？`, '生成脚本', { type: 'info', confirmButtonText: '确定', cancelButtonText: '取消' })
      await api.generateScript(ep.id)
      ElMessage.success('脚本生成任务已提交')
      fetchData()
    } catch (err) {
      if (err !== 'cancel') ElMessage.error('生成失败')
    }
  } else if (cmd === 'generate-video') {
    try {
      await ElMessageBox.confirm(`为「${ep.title}」生成视频？`, '生成视频', { type: 'info', confirmButtonText: '确定', cancelButtonText: '取消' })
      await api.generateVideo(ep.id)
      ElMessage.success('视频生成任务已提交')
      fetchData()
    } catch (err) {
      if (err !== 'cancel') ElMessage.error('生成失败')
    }
  } else if (cmd === 'view-script') {
    currentEpisodeId.value = ep.id
    currentScript.value = ep.script || '暂无脚本内容'
    showScriptDialog.value = true
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(`确定删除「${ep.title}」吗？`, '确认删除', { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' })
      ElMessage.success('删除成功')
      fetchData()
    } catch (err) {
      if (err !== 'cancel') ElMessage.error('删除失败')
    }
  }
}

const handleSaveScript = async () => {
  if (!currentEpisodeId.value) return
  try {
    await api.updateScript(currentEpisodeId.value, currentScript.value)
    ElMessage.success('脚本已保存')
    showScriptDialog.value = false
    fetchData()
  } catch (err) {
    ElMessage.error('保存失败: ' + err.message)
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

const goBack = () => router.push(`/series/${seriesId}`)

const getStatusType = (status) => {
  const map = {
    draft: 'info',
    outline_generated: 'success',
    script_generating: 'warning',
    script_generated: 'success',
    video_generating: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    draft: '草稿',
    outline_generated: '大纲已生成',
    script_generating: '脚本生成中',
    script_generated: '脚本已生成',
    video_generating: '视频生成中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const getSeriesStatusType = (status) => {
  const map = { draft: 'info', outline_generated: 'success', episodes_generating: 'warning', completed: '' }
  return map[status] || 'info'
}

const getSeriesStatusText = (status) => {
  const map = {
    draft: '草稿',
    outline_generated: '大纲已生成',
    episodes_generating: '生成中',
    completed: '完成'
  }
  return map[status] || status
}

onMounted(fetchData)
onUnmounted(stopPolling)
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
  margin-bottom: 16px;
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

.series-action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px;
  color: #909399;
}

.queue-card {
  margin-bottom: 20px;
  background: #f5f7fa;
  border: none;
}

.queue-title {
  font-weight: 600;
  font-size: 14px;
}

.queue-stats {
  display: flex;
  gap: 32px;
  padding: 8px 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  font-size: 12px;
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
  gap: 10px;
}

.episode-name {
  font-weight: 600;
  font-size: 16px;
}

.episode-num {
  font-size: 12px;
  color: #c0c4cc;
}

.more-icon {
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  font-size: 16px;
}

.more-icon:hover {
  background: #f5f7fa;
}

.episode-info {
  padding: 4px 0;
}

.episode-desc {
  color: #606266;
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.5;
}

.episode-tasks {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  margin-top: 8px;
}

.tasks-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-outline {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  margin-top: 8px;
}

.outline-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.outline-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  max-height: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  background: #f9f9f9;
  padding: 8px;
  border-radius: 4px;
}
</style>
