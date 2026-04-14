import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

const routes = [
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
    },
    {
        path: '/manager',
        name: 'Manager',
        component: () => import('../views/Placeholder.vue'), // Lazy load placeholders
    },
    {
        path: '/rental',
        name: 'Rental',
        component: () => import('../views/Placeholder.vue'),
    },
    {
        path: '/inventory',
        name: 'Inventory',
        component: () => import('../views/Placeholder.vue'),
    },
    {
        path: '/customers',
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
