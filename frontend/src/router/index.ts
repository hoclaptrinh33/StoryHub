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
        component: () => import('../views/sale.vue'),
    },
    {
        path: '/phieu-thue',
        name: 'QuickRental',
        component: () => import('../views/sale.vue'),
    },
    {
        path: '/order-sale',
        name: 'OrderSale',
        component: () => import('../views/order-sale.vue'),
    },
    {
        path: '/rentalorder',
        name: 'RentalOrder',
        component: () => import('../views/rentalorder.vue'),
    },
    {
        path: '/khuyen-mai',
        name: 'Promotion',
        component: () => import('../views/Promotion.vue'),
    },
    {
        path: '/kho',
        name: 'Inventory',
        component: () => import('../views/manager_title.vue'),
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
