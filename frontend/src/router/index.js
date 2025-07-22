// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import ServicePage  from '../components/ServicePage.vue'
import TaskStatus   from '../views/TaskStatus.vue'

const routes = [
  { path: '/',             name: 'ServicePage', component: ServicePage },
  { path: '/tasks/:id',    name: 'TaskStatus',  component: TaskStatus },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
