<template>
  <div class="projects-page">
    <div class="page-header">
      <h2>📁 项目列表</h2>
      <el-button type="primary" @click="openCreateDialog()">
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
            <span class="project-name">{{ project.title }}</span>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, project)">
              <el-icon class="more-icon" @click.stop><MoreFilled /></el-icon>
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
          <div class="project-tags">
            <el-tag size="small" type="info">目标受众: {{ project.target_audience || '未设置' }}</el-tag>
            <el-tag size="small" type="info">风格: {{ project.style || '未设置' }}</el-tag>
          </div>
          <div class="project-meta">
            <el-tag size="small" :type="getStatusType(project.status)">
              {{ getStatusText(project.status) }}
            </el-tag>
            <span class="project-date">{{ formatDate(project.created_at) }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 新建/编辑项目对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingProject ? '编辑项目' : '新建项目'"
      width="520px"
    >
      <el-form :model="form" label-width="100px" ref="formRef" :rules="rules">
        <el-form-item label="项目名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入项目描述（可选）" />
        </el-form-item>
        <el-form-item label="目标受众">
          <el-input v-model="form.target_audience" placeholder="如：职场新人、健身爱好者" />
        </el-form-item>
        <el-form-item label="内容风格">
          <el-input v-model="form.style" placeholder="如：幽默风趣、严肃认真" />
        </el-form-item>
        <el-form-item label="计划集数">
          <el-input-number v-model="form.episode_count" :min="1" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, Loading } from '@element-plus/icons-vue'
import * as api from '@/api'

const router = useRouter()
const loading = ref(false)
const projects = ref([])
const dialogVisible = ref(false)
const editingProject = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const defaultForm = () => ({
  title: '',
  description: '',
  target_audience: '',
  style: '',
  episode_count: 5
})

const form = reactive(defaultForm())

const rules = {
  title: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const fetchProjects = async () => {
  loading.value = true
  try {
    const data = await api.getProjects()
    projects.value = data || []
  } catch (err) {
    ElMessage.error('获取项目列表失败: ' + err.message)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingProject.value = null
  Object.assign(form, defaultForm())
  dialogVisible.value = true
}

const openEditDialog = (project) => {
  editingProject.value = project
  Object.assign(form, {
    title: project.title,
    description: project.description || '',
    target_audience: project.target_audience || '',
    style: project.style || '',
    episode_count: project.episode_count || 5
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (editingProject.value) {
      await api.updateProject(editingProject.value.id, form)
      ElMessage.success('项目更新成功')
    } else {
      await api.createProject(form)
      ElMessage.success('项目创建成功')
    }
    dialogVisible.value = false
    fetchProjects()
  } catch (err) {
    ElMessage.error((editingProject.value ? '更新' : '创建') + '失败: ' + err.message)
  } finally {
    submitting.value = false
  }
}

const goToProject = (project) => {
  router.push(`/series/${project.id}`)
}

const handleCommand = async (cmd, project) => {
  if (cmd === 'edit') {
    openEditDialog(project)
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm(`确定删除项目「${project.title}」吗？相关系列和分集也将被删除。`, '确认删除', {
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

const getStatusType = (status) => {
  const map = {
    draft: 'info',
    active: '',
    completed: 'success',
    archived: 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = {
    draft: '草稿',
    active: '进行中',
    completed: '已完成',
    archived: '已归档'
  }
  return map[status] || status
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
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
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
  font-size: 16px;
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
  margin-bottom: 10px;
  line-height: 1.5;
  min-height: 42px;
}

.project-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 10px;
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
