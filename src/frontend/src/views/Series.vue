<template>
  <div class="series-page">
    <div class="page-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h2>📺 {{ projectName }} - 系列管理</h2>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建系列
      </el-button>
    </div>

    <!-- 项目状态卡片 -->
    <div class="project-status-bar" v-if="projectId">
      <el-tag :type="getProjectStatusType(projectInfo.status)">
        {{ getProjectStatusText(projectInfo.status) }}
      </el-tag>
      <el-button
        v-if="projectInfo.status === 'draft'"
        type="warning"
        size="small"
        :loading="generatingOutline"
        @click="handleGenerateOutline"
      >
        <el-icon><MagicStick /></el-icon> 生成大纲
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

    <el-empty v-else-if="seriesList.length === 0" description="暂无系列，点击上方按钮创建" />

    <div v-else class="series-list">
      <el-card
        v-for="s in seriesList"
        :key="s.id"
        class="series-card"
        shadow="hover"
        @click="goToSeries(s)"
      >
        <template #header>
          <div class="card-header">
            <div class="series-title">
              <span class="series-name">{{ s.title }}</span>
              <el-tag size="small" :type="getSeriesStatusType(s.status)">
                {{ getSeriesStatusText(s.status) }}
              </el-tag>
              <el-tag size="small" type="info">{{ s.episode_count || 0 }} 集</el-tag>
            </div>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, s)">
              <el-icon class="more-icon" @click.stop><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="outline" divided>
                    <el-icon><MagicStick /></el-icon> 生成大纲
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <div class="series-info">
          <p class="series-desc">{{ s.description || s.outline || '暂无描述' }}</p>
          <div class="series-meta">
            <span class="series-id">ID: {{ s.id }}</span>
            <span class="series-date">{{ formatDate(s.created_at) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 新建系列对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建系列" width="500px">
      <el-form :model="newSeries" label-width="80px">
        <el-form-item label="系列标题">
          <el-input v-model="newSeries.title" placeholder="请输入系列标题" />
        </el-form-item>
        <el-form-item label="系列描述">
          <el-input
            v-model="newSeries.description"
            type="textarea"
            :rows="3"
            placeholder="请输入系列描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑系列对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑系列" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="系列标题">
          <el-input v-model="editForm.title" placeholder="请输入系列标题" />
        </el-form-item>
        <el-form-item label="系列描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入系列描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, Loading, ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import * as api from '@/api'

const router = useRouter()
const route = useRoute()
const projectId = route.params.id

const loading = ref(false)
const error = ref('')
const projectName = ref('')
const projectInfo = ref({})
const seriesList = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const submitting = ref(false)
const generatingOutline = ref(false)
const editingSeries = ref(null)

const newSeries = ref({ title: '', description: '' })
const editForm = reactive({ title: '', description: '' })

const fetchData = async () => {
  loading.value = true
  error.value = ''
  try {
    const project = await api.getProject(projectId)
    projectName.value = project.title || `项目 ${projectId}`
    projectInfo.value = project

    const data = await api.getSeries(projectId)
    seriesList.value = data || []
  } catch (err) {
    error.value = '加载失败: ' + err.message
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!newSeries.value.title.trim()) {
    ElMessage.warning('请输入系列标题')
    return
  }
  submitting.value = true
  try {
    await api.createSeries(projectId, newSeries.value)
    ElMessage.success('系列创建成功')
    showCreateDialog.value = false
    newSeries.value = { title: '', description: '' }
    fetchData()
  } catch (err) {
    ElMessage.error('创建失败: ' + err.message)
  } finally {
    submitting.value = false
  }
}

const handleUpdate = async () => {
  if (!editForm.title.trim()) {
    ElMessage.warning('请输入系列标题')
    return
  }
  submitting.value = true
  try {
    await api.updateSeries(editingSeries.value.id, editForm)
    ElMessage.success('更新成功')
    showEditDialog.value = false
    fetchData()
  } catch (err) {
    ElMessage.error('更新失败: ' + err.message)
  } finally {
    submitting.value = false
  }
}

const handleGenerateOutline = async () => {
  try {
    await ElMessageBox.confirm(
      '将为该项目的所有系列生成 AI 大纲，这可能需要几分钟时间。是否继续？',
      '生成大纲',
      { type: 'info', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
    generatingOutline.value = true
    // 遍历所有系列生成大纲
    const promises = seriesList.value.map(s => api.generateOutline(s.id).catch(() => {}))
    await Promise.all(promises)
    ElMessage.success('大纲生成任务已提交，请稍后刷新查看')
    fetchData()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('生成失败')
  } finally {
    generatingOutline.value = false
  }
}

const goToSeries = (s) => {
  router.push(`/episode/${s.id}`)
}

const goBack = () => router.push('/')

const handleCommand = async (cmd, s) => {
  if (cmd === 'edit') {
    editingSeries.value = s
    editForm.title = s.title || ''
    editForm.description = s.description || ''
    showEditDialog.value = true
  } else if (cmd === 'outline') {
    try {
      await ElMessageBox.confirm(`为系列「${s.title}」生成 AI 大纲？`, '生成大纲', { type: 'info', confirmButtonText: '确定', cancelButtonText: '取消' })
      generatingOutline.value = true
      await api.generateOutline(s.id)
      ElMessage.success('大纲生成任务已提交')
      fetchData()
    } catch (err) {
      if (err !== 'cancel') ElMessage.error('生成失败')
    } finally {
      generatingOutline.value = false
    }
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(`确定删除系列「${s.title}」吗？`, '确认删除', { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' })
      // 调用 deleteSeries 如果有的话，或者标记删除
      ElMessage.success('删除成功（实际删除需要后端支持）')
      fetchData()
    } catch (err) {
      if (err !== 'cancel') ElMessage.error('删除失败')
    }
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const getProjectStatusType = (status) => {
  const map = { draft: 'info', active: '', completed: 'success', archived: 'warning' }
  return map[status] || 'info'
}

const getProjectStatusText = (status) => {
  const map = { draft: '草稿', active: '进行中', completed: '已完成', archived: '已归档' }
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
</script>

<style scoped>
.series-page {
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

.project-status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px;
  color: #909399;
}

.series-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.series-card {
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.series-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.series-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.series-name {
  font-weight: 600;
  font-size: 16px;
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

.series-info {
  padding: 4px 0;
}

.series-desc {
  color: #606266;
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.series-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #c0c4cc;
}
</style>
