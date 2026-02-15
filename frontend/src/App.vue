<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="logo">🤖 智能OnCall助手</h1>
      </div>
      
      <nav class="sidebar-nav">
        <button 
          v-for="item in navItems" 
          :key="item.id"
          :class="['nav-item', { active: currentView === item.id }]"
          @click="currentView = item.id"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-text">{{ item.name }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <div class="status-indicator" :class="connectionStatus">
          <span class="status-dot"></span>
          <span>{{ connectionStatus === 'connected' ? '已连接' : '未连接' }}</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 对话视图 -->
      <div v-if="currentView === 'chat'" class="view-container">
        <ChatView />
      </div>

      <!-- AIOps 视图 -->
      <div v-if="currentView === 'aiops'" class="view-container">
        <AIOpsView />
      </div>

      <!-- 文件上传视图 -->
      <div v-if="currentView === 'upload'" class="view-container">
        <UploadView />
      </div>

      <!-- 系统状态视图 -->
      <div v-if="currentView === 'status'" class="view-container">
        <StatusView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ChatView from './views/ChatView.vue'
import AIOpsView from './views/AIOpsView.vue'
import UploadView from './views/UploadView.vue'
import StatusView from './views/StatusView.vue'

const currentView = ref('chat')
const connectionStatus = ref('disconnected')

const navItems = [
  { id: 'chat', name: '智能对话', icon: '💬' },
  { id: 'aiops', name: '故障分析', icon: '🔧' },
  { id: 'upload', name: '知识库管理', icon: '📁' },
  { id: 'status', name: '系统状态', icon: '📊' }
]

onMounted(async () => {
  try {
    const res = await fetch('/health')
    if (res.ok) {
      connectionStatus.value = 'connected'
    }
  } catch (e) {
    connectionStatus.value = 'disconnected'
  }
})
</script>