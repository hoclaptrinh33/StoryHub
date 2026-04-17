<template>
  <div class="placeholder">
    <h1>Tính năng đang phát triển</h1>
    <p>Chào mừng bạn đến với module: {{ $route.name }}</p>
    <div class="card">
      <p>Module này sẽ sớm được hoàn thiện theo yêu cầu của dự án StoryHub.</p>
    </div>
  </div>
</template>

<style scoped>
.placeholder {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  padding: 30px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

h1 {
  color: #1a2a4a;
}
</style>
