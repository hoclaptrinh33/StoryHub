import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/login.vue'),
        meta: { public: true }
    },
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
    // {
    //     path: '/inventory',
    //     name: 'Settings',
    //     component: () => import('../views/inventory.vue'),
    // },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

router.beforeEach((to, _from, next) => {
    const authStore = useAuthStore()

    if (to.meta.public) {
        // If logged in and trying to go to login, redirect to dashboard
        if (to.name === 'Login' && authStore.isAuthenticated) {
            next({ name: 'Dashboard' })
        } else {
            next()
        }
    } else {
        if (!authStore.isAuthenticated) {
            next({ name: 'Login' })
        } else {
            next()
        }
    }
})

export default router
