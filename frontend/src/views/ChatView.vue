<template>
  <div class="chat-view">
    <!-- 对话历史 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="welcome-message">
        <h2>👋 你好！我是智能 OnCall 助手</h2>
        <p>我可以帮助你解答运维相关问题，查询系统状态，分析故障原因。</p>
      </div>
      
      <div 
        v-for="(msg, index) in messages" 
        :key="index" 
        :class="['message', msg.role]"
      >
        <div class="message-avatar">
          {{ msg.role === 'user' ? '👤' : '🤖' }}
        </div>
        <div class="message-content">
          <div class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
          <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
            <span class="sources-label">📚 参考来源:</span>
            <span v-for="(source, i) in msg.sources" :key="i" class="source-tag">
              {{ source }}
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="isLoading" class="message assistant loading">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <textarea 
          v-model="inputText" 
          placeholder="输入你的问题..." 
          class="input"
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          :disabled="isLoading"
        ></textarea>
        <div class="input-actions">
          <select v-model="chatMode" class="mode-select">
            <option value="quick">快速模式</option>
            <option value="stream">流式模式</option>
          </select>
          <button 
            class="btn btn-primary" 
            @click="sendMessage" 
            :disabled="!inputText.trim() || isLoading"
          >
            <span v-if="isLoading" class="loading-spinner small"></span>
            <span v-else>发送</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

// 配置 marked
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  }
})

const messages = ref([])
const inputText = ref('')
const chatMode = ref('stream')
const isLoading = ref(false)
const messagesContainer = ref(null)

const sessionId = 'session-' + Date.now()

const renderMarkdown = (text) => {
  return marked.parse(text || '')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    if (chatMode.value === 'stream') {
      // 流式模式
      const response = await fetch('/api/chat_stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Id: sessionId, Question: text })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantMessage = { role: 'assistant', content: '' }
      messages.value.push(assistantMessage)

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'content') {
                assistantMessage.content += data.data
                scrollToBottom()
              }
            } catch (e) {}
          }
        }
      }
    } else {
      // 快速模式
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ Id: sessionId, Question: text })
      })

      const data = await response.json()
      messages.value.push({
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      })
    }
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `❌ 请求失败: ${error.message}`
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.welcome-message h2 {
  color: var(--text-primary);
  margin-bottom: 12px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  background-color: var(--bg-tertiary);
  flex-shrink: 0;
}

.message.user .message-avatar {
  background-color: var(--primary-color);
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.message.user .message-content {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

.message-sources {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  font-size: 0.85rem;
}

.sources-label {
  color: var(--text-muted);
  margin-right: 8px;
}

.source-tag {
  display: inline-block;
  background-color: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 4px;
  font-size: 0.8rem;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background-color: var(--text-muted);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-wrapper .input {
  resize: none;
  min-height: 44px;
  max-height: 120px;
}

.input-actions {
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
  font-size: 0.9rem;
}

.loading-spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
}
</style>