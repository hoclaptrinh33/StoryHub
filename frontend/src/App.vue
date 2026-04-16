<template>
  <div id="app">
    <Notice ref="noticeRef" />
    <ConfirmModal ref="confirmRef" />
    <router-view />
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import Notice from './components/layout/notice.vue'
import ConfirmModal from './components/layout/ConfirmModal.vue'

const noticeRef = ref(null)
const confirmRef = ref(null)

const addNotification = (type, message) => {
  if (noticeRef.value) {
    noticeRef.value.addNotification(type, message)
  }
}

const showConfirm = (message, title) => {
  if (confirmRef.value) {
    return confirmRef.value.show(message, title)
  }
  return Promise.resolve(false)
}

provide('addNotification', addNotification)
provide('showConfirm', showConfirm)
</script>

<style>
#app {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
</style>
