import { defineStore } from 'pinia'
import { ref } from 'vue'
import { logger } from '../utils/logger'

export const useSystemStore = defineStore('system', () => {
    const backendHealthy = ref(false)
    const backendMessage = ref('')
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

    async function checkHealth() {
        logger.debug('Bat dau kiem tra ket noi backend', { apiBaseUrl })
        try {
            const response = await fetch(`${apiBaseUrl}/api/v1/health`)
            if (response.ok) {
                const data = await response.json()
                backendHealthy.value = true
                backendMessage.value = `Online: ${data.data.service} v${data.data.version}`
                logger.info('Backend ket noi thanh cong', data.data)
            } else {
                backendHealthy.value = false
                backendMessage.value = `Offline: HTTP ${response.status}`
                logger.warn('Backend tra ve trang thai loi', { status: response.status })
            }
        } catch (error) {
            backendHealthy.value = false
            backendMessage.value = 'Offline: Không thể kết nối'
            logger.error('Khong the ket noi backend', error)
        }
    }

    return {
        backendHealthy,
        backendMessage,
        apiBaseUrl,
        checkHealth,
    }
})
