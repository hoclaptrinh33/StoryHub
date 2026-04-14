import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSystemStore = defineStore('system', () => {
    const backendHealthy = ref(false)
    const backendMessage = ref('')
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

    async function checkHealth() {
        try {
            const response = await fetch(`${apiBaseUrl}/api/v1/health`)
            if (response.ok) {
                const data = await response.json()
                backendHealthy.value = true
                backendMessage.value = `Online: ${data.service} v${data.version}`
            } else {
                backendHealthy.value = false
                backendMessage.value = `Offline: HTTP ${response.status}`
            }
        } catch {
            backendHealthy.value = false
            backendMessage.value = 'Offline: Không thể kết nối'
        }
    }

    return {
        backendHealthy,
        backendMessage,
        apiBaseUrl,
        checkHealth,
    }
})
