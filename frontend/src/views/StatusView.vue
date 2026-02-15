<template>
  <div class="status-view">
    <!-- 系统状态概览 -->
    <div class="status-overview">
      <div class="status-card" :class="systemStatus.overall">
        <div class="status-icon">
          {{ systemStatus.overall === 'healthy' ? '✅' : '⚠️' }}
        </div>
        <div class="status-info">
          <h3>系统状态</h3>
          <p>{{ systemStatus.overall === 'healthy' ? '所有服务正常运行' : '部分服务异常' }}</p>
        </div>
      </div>
    </div>

    <!-- 服务状态列表 -->
    <div class="services-section card">
      <h3 class="card-title">🔍 服务状态</h3>
      
      <div class="services-grid">
        <!-- API 服务 -->
        <div class="service-item" :class="services.api.status">
          <div class="service-header">
            <span class="service-icon">🌐</span>
            <span class="service-name">API 服务</span>
          </div>
          <div class="service-status">
            <span class="status-dot"></span>
            <span>{{ services.api.message }}</span>
          </div>
          <button class="btn btn-secondary small" @click="checkApiHealth">
            检查
          </button>
        </div>

        <!-- Milvus 服务 -->
        <div class="service-item" :class="services.milvus.status">
          <div class="service-header">
            <span class="service-icon">🗄️</span>
            <span class="service-name">Milvus 向量数据库</span>
          </div>
          <div class="service-status">
            <span class="status-dot"></span>
            <span>{{ services.milvus.message }}</span>
          </div>
          <button class="btn btn-secondary small" @click="checkMilvusHealth">
            检查
          </button>
        </div>

        <!-- Redis 服务 -->
        <div class="service-item" :class="services.redis.status">
          <div class="service-header">
            <span class="service-icon">⚡</span>
            <span class="service-name">Redis 缓存</span>
          </div>
          <div class="service-status">
            <span class="status-dot"></span>
            <span>{{ services.redis.message }}</span>
          </div>
          <button class="btn btn-secondary small" @click="checkRedisHealth">
            检查
          </button>
        </div>
      </div>
    </div>

    <!-- 会话统计 -->
    <div class="session-section card">
      <div class="card-header">
        <h3 class="card-title">📊 会话统计</h3>
        <button class="btn btn-secondary" @click="refreshSessions">刷新</button>
      </div>
      
      <div v-if="loadingSessions" class="loading-state">
        <div class="loading-spinner"></div>
      </div>
      
      <div v-else class="session-stats">
        <div class="stat-item">
          <span class="stat-value">{{ sessionStats.count }}</span>
          <span class="stat-label">活跃会话</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ sessionStats.recentSessions.length }}</span>
          <span class="stat-label">近期会话</span>
        </div>
      </div>
      
      <div v-if="sessionStats.recentSessions.length > 0" class="session-list">
        <h4>近期会话 ID</h4>
        <div class="session-ids">
          <span 
            v-for="id in sessionStats.recentSessions" 
            :key="id" 
            class="session-id-tag"
          >
            {{ id.substring(0, 20) }}...
          </span>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-section card">
      <h3 class="card-title">🛠️ 系统操作</h3>
      <div class="actions-grid">
        <button class="btn btn-secondary" @click="checkAllHealth">
          🔄 刷新所有状态
        </button>
        <button class="btn btn-danger" @click="clearAllSessions">
          🗑️ 清空所有会话
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const systemStatus = reactive({
  overall: 'unknown'
})

const services = reactive({
  api: { status: 'unknown', message: '未检查' },
  milvus: { status: 'unknown', message: '未检查' },
  redis: { status: 'unknown', message: '未检查' }
})

const sessionStats = reactive({
  count: 0,
  recentSessions: []
})

const loadingSessions = ref(false)

const checkApiHealth = async () => {
  services.api.status = 'checking'
  services.api.message = '检查中...'
  
  try {
    const res = await fetch('/health')
    if (res.ok) {
      services.api.status = 'healthy'
      services.api.message = '运行正常'
    } else {
      services.api.status = 'unhealthy'
      services.api.message = '响应异常'
    }
  } catch (e) {
    services.api.status = 'unhealthy'
    services.api.message = '连接失败'
  }
  updateOverallStatus()
}

const checkMilvusHealth = async () => {
  services.milvus.status = 'checking'
  services.milvus.message = '检查中...'
  
  try {
    const res = await fetch('/milvus/health')
    const data = await res.json()
    if (data.status === 'healthy') {
      services.milvus.status = 'healthy'
      services.milvus.message = '连接正常'
    } else {
      services.milvus.status = 'unhealthy'
      services.milvus.message = data.message || '连接失败'
    }
  } catch (e) {
    services.milvus.status = 'unhealthy'
    services.milvus.message = '连接失败'
  }
  updateOverallStatus()
}

const checkRedisHealth = async () => {
  // Redis 健康检查暂时通过会话接口间接判断
  services.redis.status = 'checking'
  services.redis.message = '检查中...'
  
  try {
    const res = await fetch('/api/chat/sessions')
    if (res.ok) {
      services.redis.status = 'healthy'
      services.redis.message = '连接正常'
    } else {
      services.redis.status = 'unhealthy'
      services.redis.message = '响应异常'
    }
  } catch (e) {
    services.redis.status = 'unhealthy'
    services.redis.message = '连接失败'
  }
  updateOverallStatus()
}

const updateOverallStatus = () => {
  const allHealthy = 
    services.api.status === 'healthy' &&
    services.milvus.status === 'healthy' &&
    services.redis.status === 'healthy'
  
  systemStatus.overall = allHealthy ? 'healthy' : 'unhealthy'
}

const checkAllHealth = async () => {
  await Promise.all([
    checkApiHealth(),
    checkMilvusHealth(),
    checkRedisHealth()
  ])
}

const refreshSessions = async () => {
  loadingSessions.value = true
  
  try {
    const res = await fetch('/api/chat/sessions')
    const data = await res.json()
    
    sessionStats.count = data.count || 0
    sessionStats.recentSessions = data.sessions || []
  } catch (e) {
    console.error('获取会话统计失败:', e)
  } finally {
    loadingSessions.value = false
  }
}

const clearAllSessions = async () => {
  if (!confirm('确定要清空所有会话吗？此操作不可恢复。')) {
    return
  }
  
  try {
    // 清空每个会话
    for (const sessionId of sessionStats.recentSessions) {
      await fetch(`/api/chat/clear/${sessionId}`, { method: 'DELETE' })
    }
    
    sessionStats.count = 0
    sessionStats.recentSessions = []
    alert('所有会话已清空')
  } catch (e) {
    alert('清空会话失败: ' + e.message)
  }
}

onMounted(() => {
  checkAllHealth()
  refreshSessions()
})
</script>

<style scoped>
.status-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.status-overview {
  margin-bottom: 8px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border-radius: 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.status-card.healthy {
  background-color: rgba(16, 185, 129, 0.1);
  border-color: var(--success-color);
}

.status-card.unhealthy {
  background-color: rgba(239, 68, 68, 0.1);
  border-color: var(--error-color);
}

.status-icon {
  font-size: 2.5rem;
}

.status-info h3 {
  margin-bottom: 4px;
}

.status-info p {
  color: var(--text-secondary);
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.service-item {
  padding: 16px;
  background-color: var(--bg-tertiary);
  border-radius: 8px;
  border-left: 3px solid var(--border-color);
}

.service-item.healthy {
  border-left-color: var(--success-color);
}

.service-item.unhealthy {
  border-left-color: var(--error-color);
}

.service-item.checking {
  border-left-color: var(--warning-color);
}

.service-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.service-icon {
  font-size: 1.2rem;
}

.service-name {
  font-weight: 500;
}

.service-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-muted);
}

.service-item.healthy .status-dot {
  background-color: var(--success-color);
}

.service-item.unhealthy .status-dot {
  background-color: var(--error-color);
}

.service-item.checking .status-dot {
  background-color: var(--warning-color);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.btn.small {
  padding: 6px 12px;
  font-size: 0.85rem;
}

.session-stats {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 600;
  color: var(--primary-color);
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.session-list h4 {
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.session-ids {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.session-id-tag {
  padding: 4px 10px;
  background-color: var(--bg-tertiary);
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: monospace;
  color: var(--text-muted);
}

.loading-state {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.actions-grid {
  display: flex;
  gap: 12px;
}
</style>