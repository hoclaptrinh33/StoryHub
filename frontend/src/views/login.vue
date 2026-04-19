<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { login as apiLogin } from '../services/storyhubApi'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    errorMessage.value = 'Vui lòng nhập đầy đủ tài khoản và mật khẩu.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    const data = await apiLogin({
      username: username.value,
      password: password.value,
      remember_me: rememberMe.value
    })

    authStore.setAuth(data.access_token, data.user)
    
    // Redirect to dashboard or previous page
    router.push('/')
  } catch (err: any) {
    errorMessage.value = err.message || 'Đăng nhập thất bại. Vui lòng thử lại.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <!-- Background animation elements -->
    <div class="bg-blur blur-1"></div>
    <div class="bg-blur blur-2"></div>
    
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <span class="logo-icon">📚</span>
          <h1>Story<span>Hub</span></h1>
        </div>
        <p>Hệ thống quản lý kho và cho thuê truyện chuyên nghiệp</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Tài khoản</label>
          <div class="input-wrapper">
            <span class="input-icon">👤</span>
            <input 
              id="username"
              v-model="username" 
              type="text" 
              placeholder="Nhập tên đăng nhập"
              :disabled="isLoading"
              autofocus
            />
          </div>
        </div>

        <div class="form-group">
          <label for="password">Mật khẩu</label>
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <input 
              id="password"
              v-model="password" 
              type="password" 
              placeholder="Nhập mật khẩu"
              :disabled="isLoading"
            />
          </div>
        </div>

        <div class="form-options">
          <label class="remember-me">
            <input type="checkbox" v-model="rememberMe" :disabled="isLoading" />
            <span class="checkmark"></span>
            Ghi nhớ đăng nhập
          </label>
        </div>

        <div v-if="errorMessage" class="error-alert">
          <span class="error-icon">⚠️</span>
          {{ errorMessage }}
        </div>

        <button type="submit" class="login-button" :disabled="isLoading">
          <span v-if="isLoading" class="loader"></span>
          <span v-else>Đăng Nhập</span>
        </button>
      </form>

      <div class="login-footer">
        <p>&copy; 2026 StoryHub POS. v0.2.0-beta</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #0c0f16;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
  color: #fff;
}

/* Background effects */
.bg-blur {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  filter: blur(120px);
  z-index: 0;
  opacity: 0.15;
}

.blur-1 {
  background: #3b82f6;
  top: -100px;
  left: -100px;
}

.blur-2 {
  background: #8b5cf6;
  bottom: -100px;
  right: -100px;
}

/* Glassmorphism Card */
.login-card {
  width: 100%;
  max-width: 440px;
  padding: 48px;
  background: rgba(23, 28, 41, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  z-index: 10;
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.logo-icon {
  font-size: 32px;
}

.logo h1 {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.logo span {
  color: #6366f1;
  -webkit-text-fill-color: #6366f1;
}

.login-header p {
  color: #94a3b8;
  font-size: 14px;
  line-height: 1.5;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #cbd5e1;
  margin-left: 4px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  font-size: 18px;
  opacity: 0.5;
}

input {
  width: 100%;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 14px 14px 14px 48px;
  color: #fff;
  font-size: 15px;
  transition: all 0.2s ease;
  outline: none;
}

input:focus {
  border-color: #6366f1;
  background: rgba(15, 23, 42, 0.8);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
}

input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: -8px;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: #94a3b8;
  user-select: none;
  position: relative;
  padding-left: 28px;
}

.remember-me input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
  height: 0;
  width: 0;
}

.checkmark {
  position: absolute;
  top: 0;
  left: 0;
  height: 20px;
  width: 20px;
  background-color: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.remember-me:hover input ~ .checkmark {
  border-color: #6366f1;
}

.remember-me input:checked ~ .checkmark {
  background-color: #6366f1;
  border-color: #6366f1;
}

.checkmark:after {
  content: "";
  position: absolute;
  display: none;
}

.remember-me input:checked ~ .checkmark:after {
  display: block;
}

.remember-me .checkmark:after {
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.error-alert {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #f87171;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.login-button {
  margin-top: 8px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3);
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 20px 25px -5px rgba(79, 70, 229, 0.4);
  filter: brightness(1.1);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-footer {
  margin-top: 40px;
  text-align: center;
}

.login-footer p {
  font-size: 12px;
  color: #64748b;
}
</style>
