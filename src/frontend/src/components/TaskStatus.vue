<template>
  <div class="task-status" :class="`status-${task.status}`">
    <div class="task-info">
      <el-icon class="task-icon">
        <Loading v-if="task.status === 'running'" class="is-loading" />
        <Check v-else-if="task.status === 'completed'" />
        <Close v-else-if="task.status === 'failed'" />
        <Clock v-else />
      </el-icon>
      <span class="task-type">{{ getTaskTypeText(task.type) }}</span>
      <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
    </div>
    <div class="task-actions" v-if="task.status === 'failed'">
      <el-button size="small" type="danger" @click="$emit('retry', task)">
        重试
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

defineEmits(['retry'])

const statusType = computed(() => {
  const map = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[props.task.status] || 'info'
})

const statusText = computed(() => {
  const map = {
    pending: '等待中',
    running: '进行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[props.task.status] || props.task.status
})

const getTaskTypeText = (type) => {
  const map = {
    script: '脚本生成',
    voiceover: '配音',
    video: '视频生成',
    subtitles: '字幕生成',
    background_music: '背景音乐',
    synthesis: '合成'
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
}

.task-status.status-failed {
  background: #fef0f0;
}

.task-status.status-completed {
  background: #f0f9eb;
}

.task-status.status-running {
  background: #fdf6ec;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-icon {
  font-size: 14px;
}

.task-type {
  color: #303133;
}

.task-actions {
  flex-shrink: 0;
}
</style>
