<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>📁 项目列表</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="projects.length === 0" description="暂无项目，点击上方按钮创建第一个项目" />

    <!-- 项目列表 -->
    <div v-else class="projects-grid">
      <el-card
        v-for="project in projects"
        :key="project.id"
        class="project-card"
        shadow="hover"
        @click="goToProject(project)"
      >
        <template #header>
          <div class="card-header">
            <span class="project-name">{{ project.name }}</span>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, project)">
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
        <div class="project-info">
          <p class="project-desc">{{ project.description || '暂无描述' }}</p>
          <div class="project-meta">
            <el-tag size="small" type="info">ID: {{ project.id }}</el-tag>
            <span class="project-date">{{ formatDate(project.created_at) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 新建项目对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建项目" width="500px">
      <el-form :model="newProject" label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="newProject.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="newProject.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述（可选）"
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, Loading } from '@element-plus/icons-vue'
import * as api from '@/api'

const router = useRouter()
const loading = ref(false)
const projects = ref([])
const showCreateDialog = ref(false)
const submitting = ref(false)
const newProject = ref({ name: '', description: '' })

const fetchProjects = async () => {
  loading.value = true
  try {
    const data = await api.getProjects()
    projects.value = data.projects || data || []
  } catch (err) {
    ElMessage.error('获取项目列表失败')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  if (!newProject.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  submitting.value = true
  try {
    await api.createProject(newProject.value)
    ElMessage.success('项目创建成功')
    showCreateDialog.value = false
    newProject.value = { name: '', description: '' }
    fetchProjects()
  } catch (err) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

const goToProject = (project) => {
  router.push(`/series/${project.id}`)
}

const handleCommand = async (cmd, project) => {
  if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(`确定删除项目「${project.name}」吗？`, '确认删除', {
        type: 'warning'
      })
      await api.deleteProject(project.id)
      ElMessage.success('删除成功')
      fetchProjects()
    } catch (err) {
      if (err !== 'cancel') ElMessage.error('删除失败')
    }
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN')
}

onMounted(fetchProjects)
</script>

<style scoped>
.projects-page {
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
  justify-content: center;
  padding: 60px;
  color: #909399;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.project-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-name {
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

.project-info {
  padding: 4px 0;
}

.project-desc {
  color: #606266;
  font-size: 14px;
  margin-bottom: 12px;
  line-height: 1.5;
}

.project-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-date {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
