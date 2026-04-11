import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4000/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error('[API Error]', msg)
    return Promise.reject(new Error(msg))
  }
)

// ============ 项目 API ============

export const getProjects = () => apiClient.get('/projects')

export const getProject = (id) => apiClient.get(`/projects/${id}`)

export const createProject = (data) => apiClient.post('/projects', data)

export const updateProject = (id, data) => apiClient.put(`/projects/${id}`, data)

export const deleteProject = (id) => apiClient.delete(`/projects/${id}`)

// ============ 系列 API ============

export const getSeries = (projectId) => apiClient.get('/series', { params: { project_id: projectId } })

export const getSeriesDetail = (id) => apiClient.get(`/series/${id}`)

export const createSeries = (projectId, data) =>
  apiClient.post('/series', { project_id: projectId, title: data.title, description: data.description })

export const updateSeries = (id, data) => apiClient.put(`/series/${id}`, data)

export const generateOutline = (id) => apiClient.post(`/series/${id}/generate-outline`)

// ============ 分集 API ============

export const getEpisodes = (seriesId) => apiClient.get('/episodes', { params: { series_id: seriesId } })

export const getEpisodeDetail = (id) => apiClient.get(`/episodes/${id}`)

export const createEpisode = (seriesId, data) =>
  apiClient.post('/episodes', {
    series_id: parseInt(seriesId),
    episode_number: data.episode_number || 1,
    title: data.title,
    description: data.description || ''
  })

export const updateEpisode = (id, data) => apiClient.put(`/episodes/${id}`, data)

export const generateScript = (id) => apiClient.post(`/episodes/${id}/generate-script`)

export const generateVideo = (id) => apiClient.post(`/episodes/${id}/generate-video`)

export const updateScript = (id, script) => apiClient.patch(`/episodes/${id}/script`, { script })

// ============ 任务 API ============

export const getTasks = (params) => apiClient.get('/tasks', { params })

export const getTaskStatus = (id) => apiClient.get(`/tasks/${id}`)

export const createTask = (data) => apiClient.post('/tasks', data)

export const retryTask = (id) => apiClient.post(`/tasks/${id}/retry`)

export const pauseTask = (id) => apiClient.post(`/tasks/${id}/pause`)

export const resumeTask = (id) => apiClient.post(`/tasks/${id}/resume`)

// ============ 队列状态 API ============

export const getQueueStatus = () => apiClient.get('/openclaw/queue')

export default apiClient
