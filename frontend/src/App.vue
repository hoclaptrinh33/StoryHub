<template>
  <div id="app">
    <Notice ref="noticeRef" />
    <ConfirmModal ref="confirmRef" />
    <router-view />
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onBeforeUnmount } from 'vue'
import Notice from './components/layout/notice.vue'
import ConfirmModal from './components/layout/ConfirmModal.vue'

const noticeRef = ref(null)
const confirmRef = ref(null)

const SCAN_BUFFER_TIMEOUT_MS = 50
const SCAN_MAX_KEY_INTERVAL_MS = 30
const SCAN_MIN_LENGTH = 8

let scanBuffer = ''
let scanTimestamps = []
let scanResetTimer = null
let scannerSessionActive = false

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

const hasBlockingModal = () =>
  Boolean(document.querySelector('.confirm-overlay, .modal-overlay'))

const isEditableTarget = (target) => {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  const tagName = target.tagName.toLowerCase()
  return (
    target.isContentEditable ||
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'select'
  )
}

const emitScannerEvent = (code) => {
  window.dispatchEvent(
    new CustomEvent('storyhub:scan', {
      detail: { code, at: Date.now() },
    }),
  )
}

const emitHotkeyEvent = (name) => {
  window.dispatchEvent(
    new CustomEvent('storyhub:hotkey', {
      detail: { name, at: Date.now() },
    }),
  )
}

const clearScannerBuffer = () => {
  scanBuffer = ''
  scanTimestamps = []
  scannerSessionActive = false
  if (scanResetTimer !== null) {
    clearTimeout(scanResetTimer)
    scanResetTimer = null
  }
}

const isScannerPattern = () => {
  if (scanBuffer.length < SCAN_MIN_LENGTH) {
    return false
  }

  if (scanTimestamps.length < 2) {
    return false
  }

  for (let index = 1; index < scanTimestamps.length; index += 1) {
    const gap = scanTimestamps[index] - scanTimestamps[index - 1]
    if (gap > SCAN_MAX_KEY_INTERVAL_MS) {
      return false
    }
  }

  return true
}

const flushScannerBuffer = () => {
  if (!scanBuffer) {
    clearScannerBuffer()
    return false
  }

  const code = scanBuffer.trim()
  const validScannerInput = isScannerPattern()
  clearScannerBuffer()

  if (!validScannerInput || code.length < SCAN_MIN_LENGTH) {
    return false
  }

  emitScannerEvent(code)
  return true
}

const scheduleScannerReset = () => {
  if (scanResetTimer !== null) {
    clearTimeout(scanResetTimer)
  }

  scanResetTimer = setTimeout(() => {
    clearScannerBuffer()
  }, SCAN_BUFFER_TIMEOUT_MS)
}

const handleGlobalKeydown = (event) => {
  if (event.defaultPrevented || event.isComposing) {
    return
  }

  if (event.ctrlKey || event.metaKey || event.altKey) {
    return
  }

  const key = event.key
  if (key === 'F1' || key === 'Escape') {
    if (scannerSessionActive || hasBlockingModal()) {
      return
    }

    event.preventDefault()
    emitHotkeyEvent(key === 'F1' ? 'f1' : 'escape')
    return
  }

  if (key === '1' || key === '2' || key === '3' || key === '4') {
    if (scannerSessionActive) {
      return
    }

    if (!isEditableTarget(event.target) && !hasBlockingModal()) {
      event.preventDefault()
      emitHotkeyEvent(`digit-${key}`)
    }
    return
  }

  if (key === 'Enter') {
    if (scannerSessionActive || scanBuffer.length > 0) {
      const didHandleScanner = flushScannerBuffer()
      if (didHandleScanner) {
        event.preventDefault()
        event.stopPropagation()
      }
      return
    }

    if (!isEditableTarget(event.target) && !hasBlockingModal()) {
      event.preventDefault()
      emitHotkeyEvent('enter')
    }
    return
  }

  if (key.length !== 1) {
    return
  }

  scanBuffer += key
  scanTimestamps.push(performance.now())
  scannerSessionActive = true
  scheduleScannerReset()
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown, true)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown, true)
  clearScannerBuffer()
})

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
