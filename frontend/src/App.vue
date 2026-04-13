<script setup lang="ts">
import { ref } from 'vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
const healthMessage = ref('Chưa kiểm tra kết nối backend')
const checking = ref(false)

async function checkBackendHealth() {
  checking.value = true

  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/health`)
    if (!response.ok) {
      healthMessage.value = `Backend phản hồi lỗi HTTP ${response.status}`
      return
    }

    const payload = (await response.json()) as {
      status: string
      service: string
      version: string
      environment: string
    }
    healthMessage.value = `Kết nối thành công: ${payload.service} v${payload.version} (${payload.environment})`
  } catch {
    healthMessage.value = 'Không thể kết nối backend. Kiểm tra server FastAPI đã chạy chưa.'
  } finally {
    checking.value = false
  }
}
</script>

<template>
  <main class="shell">
    <section class="hero card">
      <p class="badge">StoryHub Development</p>
      <h1>Môi trường code đã sẵn sàng để phát triển ứng dụng kiosk</h1>
      <p class="muted">Frontend đang dùng Vue 3 + TypeScript. Backend mặc định: {{ apiBaseUrl }}</p>
      <button class="button" :disabled="checking" @click="checkBackendHealth">
        {{ checking ? 'Đang kiểm tra...' : 'Kiểm tra kết nối backend' }}
      </button>
      <p class="status">{{ healthMessage }}</p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Các bước tiếp theo</h2>
        <ul>
          <li>Triển khai API theo blueprint trong thư mục docs/api-reference/v1.</li>
          <li>Xây màn hình POS và Rental Return theo UI contract.</li>
          <li>Bổ sung realtime item status qua WebSocket.</li>
        </ul>
      </article>

      <article class="card">
        <h2>Checklist môi trường</h2>
        <ul>
          <li>Python env đã cấu hình trong workspace.</li>
          <li>Node.js đã sẵn sàng cho frontend Vite.</li>
          <li>Rust chưa có, cần cài để bật Tauri desktop shell.</li>
        </ul>
      </article>
    </section>
  </main>
</template>
