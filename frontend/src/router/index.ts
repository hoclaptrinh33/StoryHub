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
        component: () => import('../views/manager.vue'),
    },
    {
        path: '/ban-hang',
        name: 'QuickSale',
        component: () => import('../views/checkout.vue'),
    },
    {
        path: '/khuyen-mai',
        name: 'Promotion',
        component: () => import('../views/Promotion.vue'),
    },
    {
        path: '/hoan-tra',
        name: 'RentalReturnInspection',
        component: () => import('../views/rental-return-inspection.vue'),
    },
    {
        path: '/kho',
        name: 'Inventory',
        component: () => import('../views/inventory.vue'),
    },
    {
        path: '/khach-hang',
        name: 'Customers',
        component: () => import('../views/customer.vue'),
    },
    {
        path: '/bao-cao',
        name: 'Report',
        component: () => import('../views/report.vue'),
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
