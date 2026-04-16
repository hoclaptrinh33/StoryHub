import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
    },
    {
        path: '/quan-ly',
        name: 'Manager_title',
        component: () => import('../views/manager_title.vue'), // Lazy load placeholders
    },
    {
        path: '/ban-hang',
        name: 'Rental',
        component: () => import('../views/Placeholder.vue'),
    },
    {
        path: '/kho',
        name: 'Inventory',
        component: () => import('../views/Placeholder.vue'),
    },
    {
        path: '/khach-hang',
        name: 'Customers',
        component: () => import('../views/Placeholder.vue'),
    },
    {
        path: '/settings',
        name: 'Settings',
        component: () => import('../views/Placeholder.vue'),
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
