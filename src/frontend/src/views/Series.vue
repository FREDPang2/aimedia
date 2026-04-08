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
              <span class="series-name">{{ s.name }}</span>
              <el-tag size="small" type="info">共 {{ s.episode_count || 0 }} 集</el-tag>
            </div>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, s)">
              <el-icon class="more-icon"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        <div class="series-info">
          <p class="series-desc">{{ s.description || '暂无描述' }}</p>
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
        <el-form-item label="系列名称">
          <el-input v-model="newSeries.name" placeholder="请输入系列名称" />
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, Loading, ArrowLeft } from '@element-plus/icons-vue'
import * as api from '@/api'

const router = useRouter()
const route = useRoute()
const projectId = route.params.id

const loading = ref(false)
const error = ref('')
const projectName = ref('')
const seriesList = ref([])
const showCreateDialog = ref(false)
const submitting = ref(false)
const newSeries = ref({ name: '', description: '' })

const fetchData = async () => {
  loading.value = true
  error.value = ''
  try {
    const project = await api.getProject(projectId)
    projectName.value = project.name || `项目 ${projectId}`

    const data = await api.getSeries(projectId)
    seriesList.value = data.series || data || []
  } catch (err) {
    error.value = '加载失败: ' + (err.message || '未知错误')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!newSeries.value.name.trim()) {
    ElMessage.warning('请输入系列名称')
    return
  }
  submitting.value = true
  try {
    await api.createSeries(projectId, newSeries.value)
    ElMessage.success('系列创建成功')
    showCreateDialog.value = false
    newSeries.value = { name: '', description: '' }
    fetchData()
  } catch (err) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

const goToSeries = (s) => {
  router.push(`/episode/${s.id}`)
}

const goBack = () => router.push('/')

const handleCommand = async (cmd, s) => {
  if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(`确定删除系列「${s.name}」吗？`, '确认删除', { type: 'warning' })
      await api.updateSeries(s.id, { ...s, status: 'deleted' }).catch(() => {})
      ElMessage.success('删除成功')
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
  gap: 12px;
}

.series-name {
  font-weight: 600;
  font-size: 16px;
}

.more-icon {
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
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
}

.series-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #c0c4cc;
}
</style>
