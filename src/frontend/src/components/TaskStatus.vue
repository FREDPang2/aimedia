<template>
  <div class="task-status" :class="`status-${task.status}`">
    <div class="task-info">
      <el-icon class="task-icon">
        <Loading v-if="task.status === 'in_progress'" class="is-loading" />
        <Check v-else-if="task.status === 'completed'" style="color: #67c23a" />
        <Close v-else-if="task.status === 'failed'" style="color: #f56c6c" />
        <Clock v-else />
      </el-icon>
      <span class="task-type">{{ getTaskTypeText(task.task_type) }}</span>
      <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
      <!-- 进度条（仅进行中显示） -->
      <el-progress
        v-if="task.status === 'in_progress' && task.progress > 0"
        :percentage="task.progress"
        :stroke-width="6"
        :show-text="false"
        style="width: 80px"
      />
    </div>
    <div class="task-actions">
      <el-button
        v-if="task.status === 'failed'"
        size="small"
        type="danger"
        @click.stop="$emit('retry', task)"
      >
        重试
      </el-button>
      <el-button
        v-if="task.status === 'in_progress'"
        size="small"
        @click.stop="$emit('pause', task)"
      >
        暂停
      </el-button>
      <el-button
        v-if="task.status === 'paused'"
        size="small"
        type="success"
        @click.stop="$emit('resume', task)"
      >
        恢复
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Loading, Check, Close, Clock } from '@element-plus/icons-vue'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

defineEmits(['retry', 'pause', 'resume'])

const statusType = computed(() => {
  const map = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    failed: 'danger',
    paused: 'warning'
  }
  return map[props.task.status] || 'info'
})

const statusText = computed(() => {
  const map = {
    pending: '等待中',
    in_progress: '进行中',
    completed: '已完成',
    failed: '失败',
    paused: '已暂停'
  }
  return map[props.task.status] || props.task.status
})

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
</script>

<style scoped>
.task-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: #f5f7fa;
  font-size: 13px;
  gap: 8px;
}

.task-status.status-failed {
  background: #fef0f0;
}

.task-status.status-completed {
  background: #f0f9eb;
}

.task-status.status-in_progress {
  background: #fdf6ec;
}

.task-status.status-paused {
  background: #fdf6ec;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.task-icon {
  font-size: 14px;
}

.task-type {
  color: #303133;
  font-weight: 500;
}

.task-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}
</style>
