import axios from 'axios'

const API_BASE = 'http://localhost:4000/api'

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
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
    console.error('[API Error]', error.message)
    return Promise.reject(error)
  }
)

// ============ 项目 API ============

export const getProjects = () => apiClient.get('/projects')

export const getProject = (id) => apiClient.get(`/projects/${id}`)

export const createProject = (data) => apiClient.post('/projects', data)

export const updateProject = (id, data) => apiClient.put(`/projects/${id}`, data)

export const deleteProject = (id) => apiClient.delete(`/projects/${id}`)

// ============ 系列 API ============

export const getSeries = (projectId) => apiClient.get(`/projects/${projectId}/series`)

export const getSeriesDetail = (id) => apiClient.get(`/series/${id}`)

export const createSeries = (projectId, data) => apiClient.post(`/projects/${projectId}/series`, data)

export const updateSeries = (id, data) => apiClient.put(`/series/${id}`, data)

// ============ 分集 API ============

export const getEpisodes = (seriesId) => apiClient.get(`/series/${seriesId}/episodes`)

export const getEpisodeDetail = (id) => apiClient.get(`/episodes/${id}`)

export const createEpisode = (seriesId, data) => apiClient.post(`/series/${seriesId}/episodes`, data)

export const updateEpisode = (id, data) => apiClient.put(`/episodes/${id}`, data)

// ============ 任务 API ============

export const getTasks = (params) => apiClient.get('/tasks', { params })

export const getTaskStatus = (id) => apiClient.get(`/tasks/${id}`)

export const createTask = (data) => apiClient.post('/tasks', data)

export const retryTask = (id) => apiClient.post(`/tasks/${id}/retry`)

export default apiClient
