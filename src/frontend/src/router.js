import { createRouter, createWebHistory } from 'vue-router'
import Projects from './views/Projects.vue'
import Series from './views/Series.vue'
import Episode from './views/Episode.vue'
import Tasks from './views/Tasks.vue'

const routes = [
  {
    path: '/',
    name: 'Projects',
    component: Projects
  },
  {
    path: '/series/:id',
    name: 'Series',
    component: Series
  },
  {
    path: '/episode/:id',
    name: 'Episode',
    component: Episode
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
