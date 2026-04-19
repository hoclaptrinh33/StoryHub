<template>
  <div id="app">
    <Notice ref="noticeRef" />
    <ConfirmModal ref="confirmRef" />
    <router-view />
  </div>
</template>

<script setup>
import { ref, provide, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import Notice from './components/layout/notice.vue'
import ConfirmModal from './components/layout/ConfirmModal.vue'
import { useScannerStore } from './stores/scanner'

const router = useRouter()
const scannerStore = useScannerStore()

const noticeRef = ref(null)
const confirmRef = ref(null)

const SCAN_BUFFER_TIMEOUT_MS = 200
const SCAN_MAX_KEY_INTERVAL_MS = 60
const SCAN_MIN_LENGTH = 4
const SCAN_RELAXED_MAX_KEY_INTERVAL_MS = 180
const SCAN_RELAXED_MIN_LENGTH = 8

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

const isCheckoutLocalInputTarget = (target) => {
  if (!(target instanceof HTMLElement)) {
    return false
  }

  if (router.currentRoute.value.path !== '/ban-hang') {
    return false
  }

  // These inputs have their own local Enter handling in checkout view.
  return target.id === 'manual-code-input' || target.id === 'customer-smart-input'
}

const emitScannerEvent = (code) => {
  // Global smart processing
  scannerStore.processGlobalScan(code)
  
  // Also keep the event for backward compatibility or local page use
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

const hasScannerGapUnder = (maxGapMs) => {
  for (let index = 1; index < scanTimestamps.length; index += 1) {
    const gap = scanTimestamps[index] - scanTimestamps[index - 1]
    if (gap > maxGapMs) {
      return false
    }
  }

  return true
}

const isScannerPattern = () => {
  if (scanBuffer.length < SCAN_MIN_LENGTH) {
    return false
  }

  if (scanTimestamps.length < 2) {
    return false
  }

  return hasScannerGapUnder(SCAN_MAX_KEY_INTERVAL_MS)
}

const isRelaxedScannerPattern = () => {
  if (scanBuffer.length < SCAN_RELAXED_MIN_LENGTH) {
    return false
  }

  if (scanTimestamps.length < 2) {
    return false
  }

  return hasScannerGapUnder(SCAN_RELAXED_MAX_KEY_INTERVAL_MS)
}

const flushScannerBuffer = ({ allowRelaxed = false } = {}) => {
  if (!scanBuffer) {
    clearScannerBuffer()
    return false
  }

  const code = scanBuffer.trim()
  const validScannerInput =
    isScannerPattern() || (allowRelaxed && isRelaxedScannerPattern())
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

const appendScannerKey = (key) => {
  scanBuffer += key
  scanTimestamps.push(performance.now())
  scannerSessionActive = true
  scheduleScannerReset()
}

const handleGlobalKeydown = (event) => {
  if (event.defaultPrevented || event.isComposing) {
    return
  }

  // Disable global hotkeys and scanner logic on login page
  if (router.currentRoute.value.path === '/login') {
    return
  }

  if (event.ctrlKey || event.metaKey || event.altKey) {
    return
  }

  if (isCheckoutLocalInputTarget(event.target)) {
    // Avoid double-processing the same code by both local input handlers and global scanner.
    return
  }

  const key = event.key
  const functionHotkeyMap = {
    F1: 'f1',
    F2: 'f2',
    F3: 'f3',
    F4: 'f4',
    F5: 'f5',
  }

  if (key in functionHotkeyMap || key === 'Escape') {
    if (scannerSessionActive || hasBlockingModal()) {
      return
    }

    event.preventDefault()
    if (key === 'Escape') {
      if (router.currentRoute.value.path !== '/') {
        void router.push('/')
      }
      emitHotkeyEvent('escape')
      return
    }

    emitHotkeyEvent(functionHotkeyMap[key])
    return
  }

  if (key === 'Delete' || key === 'ArrowUp' || key === 'ArrowDown') {
    if (scannerSessionActive || isEditableTarget(event.target) || hasBlockingModal()) {
      return
    }

    event.preventDefault()
    if (key === 'Delete') emitHotkeyEvent('delete')
    if (key === 'ArrowUp') emitHotkeyEvent('arrow-up')
    if (key === 'ArrowDown') emitHotkeyEvent('arrow-down')
    return
  }

  if (key === '1' || key === '2' || key === '3' || key === '4') {
    if (scannerSessionActive || scanBuffer.length > 0) {
      appendScannerKey(key)
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
      const didHandleScanner = flushScannerBuffer({
        allowRelaxed: !isEditableTarget(event.target),
      })
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

  appendScannerKey(key)
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
