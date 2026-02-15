<template>
  <div class="aiops-view">
    <!-- 输入区域 -->
    <div class="aiops-input card">
      <h3 class="card-title">🔧 故障分析</h3>
      <p class="card-desc">描述你遇到的故障或告警，AI 将自动进行根因分析并提供解决建议。</p>
      
      <div class="input-group">
        <textarea 
          v-model="problemText" 
          placeholder="例如：CPU使用率过高、服务响应缓慢、内存溢出..."
          class="input"
          rows="3"
          :disabled="isAnalyzing"
        ></textarea>
        
        <div class="quick-problems">
          <span class="quick-label">快速选择：</span>
          <button 
            v-for="problem in quickProblems" 
            :key="problem"
            class="quick-btn"
            @click="problemText = problem"
          >
            {{ problem }}
          </button>
        </div>
        
        <div class="action-bar">
          <select v-model="analysisMode" class="mode-select">
            <option value="stream">流式分析（推荐）</option>
            <option value="normal">普通分析</option>
          </select>
          <button 
            class="btn btn-primary" 
            @click="startAnalysis"
            :disabled="!problemText.trim() || isAnalyzing"
          >
            {{ isAnalyzing ? '分析中...' : '开始分析' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 分析过程 -->
    <div v-if="analysisSteps.length > 0" class="analysis-process card">
      <h3 class="card-title">📊 分析过程</h3>
      
      <div class="steps-container">
        <div 
          v-for="(step, index) in analysisSteps" 
          :key="index"
          :class="['step-item', step.type]"
        >
          <div class="step-icon">
            <span v-if="step.type === 'start'">🚀</span>
            <span v-else-if="step.type === 'plan'">📋</span>
            <span v-else-if="step.type === 'step'">⚙️</span>
            <span v-else-if="step.type === 'tool_result'">🔧</span>
            <span v-else-if="step.type === 'report'">📄</span>
            <span v-else>📌</span>
          </div>
          <div class="step-content">
            <div class="markdown-content" v-html="renderMarkdown(step.data)"></div>
          </div>
        </div>
        
        <div v-if="isAnalyzing" class="step-item loading">
          <div class="step-icon">
            <div class="loading-spinner small"></div>
          </div>
          <div class="step-content">
            <span class="typing-text">正在分析中...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 分析报告 -->
    <div v-if="finalReport" class="analysis-report card">
      <h3 class="card-title">📄 分析报告</h3>
      <div class="report-content markdown-content" v-html="renderMarkdown(finalReport)"></div>
      
      <div class="report-actions">
        <button class="btn btn-secondary" @click="copyReport">
          📋 复制报告
        </button>
        <button class="btn btn-secondary" @click="resetAnalysis">
          🔄 重新分析
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  }
})

const problemText = ref('')
const analysisMode = ref('stream')
const isAnalyzing = ref(false)
const analysisSteps = ref([])
const finalReport = ref('')

const quickProblems = [
  'CPU使用率过高',
  '内存使用率过高',
  '服务响应缓慢',
  '服务不可用'
]

const renderMarkdown = (text) => {
  return marked.parse(text || '')
}

const startAnalysis = async () => {
  const problem = problemText.value.trim()
  if (!problem || isAnalyzing.value) return

  isAnalyzing.value = true
  analysisSteps.value = []
  finalReport.value = ''

  try {
    if (analysisMode.value === 'stream') {
      // 流式分析
      const response = await fetch('/api/ai_ops_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'done') {
                // 分析完成
              } else if (data.type === 'report') {
                finalReport.value = data.data
              } else if (data.data) {
                analysisSteps.value.push({
                  type: data.type,
                  data: data.data
                })
              }
            } catch (e) {}
          }
        }
      }
    } else {
      // 普通分析
      const response = await fetch('/api/ai_ops', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem })
      })

      const data = await response.json()
      finalReport.value = data.report
    }
  } catch (error) {
    analysisSteps.value.push({
      type: 'error',
      data: `❌ 分析失败: ${error.message}`
    })
  } finally {
    isAnalyzing.value = false
  }
}

const copyReport = () => {
  navigator.clipboard.writeText(finalReport.value)
  alert('报告已复制到剪贴板')
}

const resetAnalysis = () => {
  problemText.value = ''
  analysisSteps.value = []
  finalReport.value = ''
}
</script>

<style scoped>
.aiops-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.card-desc {
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-problems {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.quick-label {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.quick-btn {
  padding: 6px 12px;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

.mode-select {
  padding: 8px 12px;
  background-color: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background-color: var(--bg-tertiary);
  border-radius: 8px;
  animation: fadeIn 0.3s ease;
}

.step-item.start {
  background-color: rgba(79, 70, 229, 0.1);
  border-left: 3px solid var(--primary-color);
}

.step-item.report {
  background-color: rgba(16, 185, 129, 0.1);
  border-left: 3px solid var(--success-color);
}

.step-item.error {
  background-color: rgba(239, 68, 68, 0.1);
  border-left: 3px solid var(--error-color);
}

.step-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  overflow-x: auto;
}

.typing-text {
  color: var(--text-muted);
}

.report-content {
  padding: 16px;
  background-color: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 16px;
}

.report-actions {
  display: flex;
  gap: 12px;
}
</style>