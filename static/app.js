// SuperBizAgent 前端应用
class SuperBizAgentApp {
    constructor() {
        this.apiBaseUrl = (window.API_BASE_URL || localStorage.getItem('API_BASE_URL') || '/api').replace(/\/$/, '');
        this.currentMode = 'quick'; // 'quick' 或 'stream'
        this.sessionId = this.generateSessionId();
        this.isStreaming = false;
        this.currentChatHistory = []; // 当前对话的消息历史
        this.chatHistories = this.loadChatHistories(); // 所有历史对话
        this.isCurrentChatFromHistory = false; // 标记当前对话是否是从历史记录加载的
        
        this.initializeElements();
        this.bindEvents();
        this.updateUI();
        this.initMarkdown();
        this.checkAndSetCentered();
        this.renderChatHistory(); // 更新历史对话列表显示

        this.bindGlobalErrorRecovery();
    }

    bindGlobalErrorRecovery() {
        const recover = (err) => {
            try {
                console.error('[GlobalRecover] 捕获异常，自动解除锁定:', err);
                this.isStreaming = false;
                this.showLoadingOverlay(false);
                this.updateUI();
            } catch (e) {
            }
        };

        window.addEventListener('unhandledrejection', (event) => {
            recover(event && event.reason);
        });

        window.addEventListener('error', (event) => {
            recover(event && event.error);
        });
    }

    fetchWithTimeout(url, options = {}, timeoutMs = 60000) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(new Error('请求超时')), timeoutMs);
        const mergedOptions = { ...options, signal: controller.signal };
        return fetch(url, mergedOptions).finally(() => clearTimeout(timer));
    }

    generateSessionId() {
        return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }

    initMarkdown() {
        const checkMarked = () => {
            if (typeof marked !== 'undefined') {
                try {
                    marked.setOptions({
                        breaks: true,
                        gfm: true,
                        headerIds: false,
                        mangle: false
                    });
                } catch (e) {
                    console.error('Markdown 配置失败:', e);
                }
            } else {
                setTimeout(checkMarked, 100);
            }
        };
        checkMarked();
    }

    renderMarkdown(content) {
        if (!content) return '';
        if (typeof marked === 'undefined') {
            return this.escapeHtml(content);
        }
        try {
            return marked.parse(content);
        } catch (e) {
            console.error('Markdown 渲染失败:', e);
            return this.escapeHtml(content);
        }
    }

    highlightCodeBlocks(container) {
        if (typeof hljs === 'undefined' || !container) return;
        try {
            container.querySelectorAll('pre code').forEach((block) => {
                if (!block.classList.contains('hljs')) {
                    hljs.highlightElement(block);
                }
            });
        } catch (e) {
            console.error('代码高亮失败:', e);
        }
    }

    initializeElements() {
        this.sidebar = document.querySelector('.sidebar');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.aiOpsSidebarBtn = document.getElementById('aiOpsSidebarBtn');

        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.toolsBtn = document.getElementById('toolsBtn');
        this.toolsMenu = document.getElementById('toolsMenu');
        this.uploadFileItem = document.getElementById('uploadFileItem');
        this.modeSelectorBtn = document.getElementById('modeSelectorBtn');
        this.modeDropdown = document.getElementById('modeDropdown');
        this.currentModeText = document.getElementById('currentModeText');
        this.fileInput = document.getElementById('fileInput');

        this.chatMessages = document.getElementById('chatMessages');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.chatContainer = document.querySelector('.chat-container');
        this.welcomeGreeting = document.getElementById('welcomeGreeting');
        this.chatHistoryList = document.getElementById('chatHistoryList');
    }

    bindEvents() {
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => this.newChat());
        }

        if (this.aiOpsSidebarBtn) {
            this.aiOpsSidebarBtn.addEventListener('click', () => this.triggerAIOps());
        }

        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }

        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        if (this.uploadFileItem) {
            this.uploadFileItem.addEventListener('click', () => {
                if (this.fileInput) {
                    this.fileInput.click();
                }
                this.closeToolsMenu();
            });
        }

        if (this.toolsBtn) {
            this.toolsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleToolsMenu();
            });
        }

        document.addEventListener('click', (e) => {
            if (!this.toolsBtn) return;
            const wrapper = this.toolsBtn.closest('.tools-btn-wrapper');
            if (!wrapper) return;
            if (!wrapper.contains(e.target)) {
                wrapper.classList.remove('active');
            }
        });

        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        const dropdownItems = document.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', () => {
                const mode = item.getAttribute('data-mode');
                this.selectMode(mode);
            });
        });
    }

    toggleToolsMenu() {
        if (!this.toolsBtn) return;
        const wrapper = this.toolsBtn.closest('.tools-btn-wrapper');
        if (!wrapper) return;
        wrapper.classList.toggle('active');
    }

    closeToolsMenu() {
        if (!this.toolsBtn) return;
        const wrapper = this.toolsBtn.closest('.tools-btn-wrapper');
        if (!wrapper) return;
        wrapper.classList.remove('active');
    }

    updateUI() {
        const disabled = !!this.isStreaming;
        if (this.sendButton) this.sendButton.disabled = disabled;
        if (this.messageInput) this.messageInput.disabled = disabled;
    }

    checkAndSetCentered() {
        return;
    }

    renderChatHistory() {
        return;
    }

    loadChatHistories() {
        try {
            const stored = localStorage.getItem('chatHistories');
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('加载历史对话失败:', e);
            return [];
        }
    }

    sendMessage() {
        if (this.isStreaming) return;
        const message = (this.messageInput?.value || '').trim();
        if (!message) return;

        if (this.messageInput) this.messageInput.value = '';
        this.addMessage('user', message);
        this.isStreaming = true;
        this.updateUI();

        const run = async () => {
            try {
                if (this.currentMode === 'stream') {
                    await this.sendStreamMessage(message);
                } else {
                    await this.sendQuickMessage(message);
                }
            } catch (e) {
                this.addMessage('assistant', '抱歉，发送消息时出现错误：' + (e?.message || String(e)));
            } finally {
                this.isStreaming = false;
                this.updateUI();
            }
        };
        run();
    }

    selectMode(mode) {
        this.currentMode = mode === 'stream' ? 'stream' : 'quick';
        if (this.currentModeText) {
            this.currentModeText.textContent = this.currentMode === 'stream' ? '流式' : '快速';
        }
    }

    addMessage(type, content, isStreaming = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const wrapper = document.createElement('div');
        wrapper.className = 'message-content-wrapper';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = type === 'assistant' ? this.renderMarkdown(content) : this.escapeHtml(content);
        wrapper.appendChild(messageContent);
        messageDiv.appendChild(wrapper);

        if (this.chatMessages) {
            this.chatMessages.appendChild(messageDiv);
            this.highlightCodeBlocks(messageContent);
            this.scrollToBottom();
        }

        if (isStreaming) {
            messageDiv.dataset.streaming = '1';
        }

        return messageDiv;
    }

    addUploadResultMessage(result) {
        const status = result && result.status ? String(result.status) : 'unknown';
        const isSuccess = status === 'success';
        const filename = (result && result.filename ? String(result.filename) : '').trim() || '（未知文件）';
        const chunks = (result && typeof result.chunks === 'number') ? result.chunks : null;
        const detail = (result && result.detail ? String(result.detail) : '').trim();

        const messageDiv = document.createElement('div');
        messageDiv.className = `message assistant upload-result-message ${isSuccess ? 'success' : 'error'}`;

        const wrapper = document.createElement('div');
        wrapper.className = 'message-content-wrapper';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const safeName = this.escapeHtml(filename);
        const statusText = isSuccess ? '上传成功' : '上传失败';
        const chunksText = (chunks === null) ? '' : `<span class="upload-result-meta-item">chunks: <strong>${this.escapeHtml(String(chunks))}</strong></span>`;
        const detailHtml = detail ? `<div class="upload-result-detail">${this.escapeHtml(detail)}</div>` : '';

        messageContent.innerHTML = `
            <div class="upload-result-card">
                <div class="upload-result-header">
                    <span class="upload-result-badge ${isSuccess ? 'success' : 'error'}">${statusText}</span>
                    <span class="upload-result-filename" title="${safeName}">${safeName}</span>
                </div>
                <div class="upload-result-meta">
                    ${chunksText}
                    <span class="upload-result-meta-item">状态: <strong>${this.escapeHtml(status)}</strong></span>
                </div>
                ${detailHtml}
            </div>
        `.trim();

        wrapper.appendChild(messageContent);
        messageDiv.appendChild(wrapper);

        if (this.chatMessages) {
            this.chatMessages.appendChild(messageDiv);
            this.scrollToBottom();
        }

        return messageDiv;
    }

    addLoadingMessage(text) {
        return this.addMessage('assistant', text || '加载中...');
    }

    updateStreamMessage(messageElement, content) {
        if (!messageElement) return;
        const messageContent = messageElement.querySelector('.message-content');
        if (!messageContent) return;
        messageContent.innerHTML = this.renderMarkdown(content);
        this.highlightCodeBlocks(messageContent);
        this.scrollToBottom();
    }

    scrollToBottom() {
        if (!this.chatMessages) return;
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showNotification(message) {
        console.warn(message);
    }

    newChat() {
        if (this.isStreaming) return;
        if (this.chatMessages) this.chatMessages.innerHTML = '';
        this.sessionId = this.generateSessionId();
        this.currentChatHistory = [];
        if (this.welcomeGreeting) this.welcomeGreeting.style.display = '';
    }

    handleFileSelect(event) {
        const file = event.target.files && event.target.files[0];
        if (!file) return;
        if (!this.validateFileType(file)) {
            this.showNotification('只支持上传 TXT 或 Markdown (.md) 格式的文件');
            if (this.fileInput) this.fileInput.value = '';
            return;
        }
        this.uploadFile(file);
    }

    validateFileType(file) {
        const fileName = (file?.name || '').toLowerCase();
        const allowedExtensions = ['.txt', '.md', '.markdown'];
        return allowedExtensions.some(ext => fileName.endsWith(ext));
    }

    // 发送快速消息（普通对话）
    async sendQuickMessage(message) {
        // 添加等待提示消息
        const loadingMessage = this.addLoadingMessage('正在思考...');
        
        try {
            const response = await this.fetchWithTimeout(`${this.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    Id: this.sessionId,
                    Question: message
                })
            }, 60000);

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            const data = await response.json();
            console.log('[sendQuickMessage] 响应数据:', JSON.stringify(data));
            
            // 移除等待提示消息
            if (loadingMessage && loadingMessage.parentNode) {
                loadingMessage.parentNode.removeChild(loadingMessage);
            }

            // FastAPI 后端返回的是 ChatResponse：{ answer, sources }
            if (data && typeof data.answer === 'string') {
                const answer = data.answer || '（无回复内容）';
                this.addMessage('assistant', answer);
                return;
            }

            // 兼容：如果后端返回的是 HTTPException 格式 {detail: "..."}
            if (data && typeof data.detail === 'string') {
                throw new Error(data.detail);
            }

            throw new Error('服务返回格式不符合预期');
        } catch (error) {
            // 出错时也要移除等待提示消息
            if (loadingMessage && loadingMessage.parentNode) {
                loadingMessage.parentNode.removeChild(loadingMessage);
            }
            throw error;
        }
    }

    // 发送流式消息
    async sendStreamMessage(message) {
        try {
            const response = await this.fetchWithTimeout(`${this.apiBaseUrl}/chat_stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    Id: this.sessionId,
                    Question: message
                })
            }, 180000);

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            const assistantMessageElement = this.addMessage('assistant', '', true);
            let fullResponse = '';

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        this.updateStreamMessage(assistantMessageElement, fullResponse);
                        break;
                    }

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (!line.startsWith('data:')) continue;
                        const rawData = line.substring(5).trim();
                        if (!rawData) continue;
                        const msg = JSON.parse(rawData);
                        if (msg.type === 'content') {
                            fullResponse += msg.data || '';
                            this.updateStreamMessage(assistantMessageElement, fullResponse);
                        } else if (msg.type === 'done') {
                            this.updateStreamMessage(assistantMessageElement, fullResponse);
                            return;
                        } else if (msg.type === 'error') {
                            throw new Error(msg.data || '流式对话失败');
                        }
                    }
                }
            } finally {
                reader.releaseLock();
            }
        } catch (error) {
            throw error;
        }
    }

    updateAIOpsStreamContent(messageElement, content) {
        if (!messageElement) return;
        const messageContent = messageElement.querySelector('.message-content');
        if (!messageContent) return;
        messageContent.textContent = content;
        this.scrollToBottom();
    }

    updateAIOpsMessage(messageElement, response, details) {
        if (!messageElement) return;
        const messageContent = messageElement.querySelector('.message-content');
        if (!messageContent) return;
        messageContent.innerHTML = this.renderMarkdown(response);
        this.highlightCodeBlocks(messageContent);
        this.scrollToBottom();
    }

    // 上传文件到知识库
    async uploadFile(file) {
        // 再次验证文件类型（双重保险）
        if (!this.validateFileType(file)) {
            this.showNotification('只支持上传 TXT 或 Markdown (.md) 格式的文件', 'error');
            return;
        }

        // 验证文件大小（限制为50MB）
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showNotification('文件大小不能超过50MB', 'error');
            return;
        }

        // 锁定前端并显示上传遮罩层
        this.isStreaming = true;
        this.updateUI();
        this.showUploadOverlay(true, file.name);

        try {
            // 创建 FormData
            const formData = new FormData();
            formData.append('file', file);

            // 发送上传请求
            const response = await this.fetchWithTimeout(`${this.apiBaseUrl}/upload`, {
                method: 'POST',
                body: formData
            }, 90000);

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            const data = await response.json();

            // FastAPI 后端返回 UploadResponse：{ filename, chunks, status }
            if (data && data.status === 'success') {
                const filename = data.filename || file.name;
                const chunks = typeof data.chunks === 'number' ? data.chunks : undefined;
                this.addUploadResultMessage({ status: 'success', filename, chunks });
            } else if (data && typeof data.detail === 'string') {
                this.addUploadResultMessage({ status: 'error', filename: file.name, detail: data.detail });
                throw new Error(data.detail);
            } else {
                this.addUploadResultMessage({ status: 'error', filename: file.name, detail: '上传失败' });
                throw new Error('上传失败');
            }
        } catch (error) {
            console.error('文件上传失败:', error);
            this.showNotification('文件上传失败: ' + error.message, 'error');
        } finally {
            // 清空文件输入
            if (this.fileInput) {
                this.fileInput.value = '';
            }
            // 解锁前端
            this.isStreaming = false;
            this.showUploadOverlay(false);
            this.updateUI();
        }
    }

    async sendAIOpsRequest(loadingMessageElement, problem) {
        try {
            const response = await this.fetchWithTimeout(`${this.apiBaseUrl}/ai_ops_stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    problem: problem || '请分析当前系统告警'
                })
            }, 240000);

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }

            let fullResponse = '';

            // 处理 SSE 流式响应
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let currentEvent = '';

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) {
                        // 流结束，更新最终内容
                        if (fullResponse) {
                            console.log('AI Ops 流结束，更新最终内容，长度:', fullResponse.length);
                            this.updateAIOpsMessage(loadingMessageElement, fullResponse, []);
                        }
                        break;
                    }

                    // 解码数据并添加到缓冲区
                    buffer += decoder.decode(value, { stream: true });
                    
                    // 按行分割处理
                    const lines = buffer.split('\n');
                    // 保留最后一行（可能不完整）
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.trim() === '') continue;
                        
                        console.log('[AI Ops SSE] 收到行:', line);
                        
                        // 解析 SSE 格式
                        if (line.startsWith('id:')) {
                            continue;
                        } else if (line.startsWith('event:')) {
                            currentEvent = line.substring(6).trim();
                            console.log('[AI Ops SSE] 事件类型:', currentEvent);
                            continue;
                        } else if (line.startsWith('data:')) {
                            const rawData = line.substring(5).trim();
                            console.log('[AI Ops SSE] 数据:', rawData, ', currentEvent:', currentEvent);
                            
                            // 解析可能包含多个JSON对象的数据
                            const processJsonMessages = (data) => {
                                const jsonPattern = /\{"type"\s*:\s*"[^"]+"\s*,\s*"data"\s*:\s*(?:"[^"]*"|null)\}/g;
                                const matches = data.match(jsonPattern);
                                
                                if (matches && matches.length > 0) {
                                    console.log('[AI Ops SSE] 匹配到', matches.length, '个JSON对象');
                                    for (const jsonStr of matches) {
                                        try {
                                            const sseMessage = JSON.parse(jsonStr);
                                            if (sseMessage.type === 'content') {
                                                fullResponse += sseMessage.data || '';
                                            } else if (sseMessage.type === 'done') {
                                                console.log('AI Ops 流完成，最终内容长度:', fullResponse.length);
                                                this.updateAIOpsMessage(loadingMessageElement, fullResponse, []);
                                                return true;
                                            } else if (sseMessage.type === 'error') {
                                                throw new Error(sseMessage.data || '智能运维分析失败');
                                            }
                                        } catch (e) {
                                            if (e.message.includes('智能运维')) throw e;
                                            console.log('[AI Ops SSE] 单个JSON解析失败:', jsonStr);
                                        }
                                    }
                                    if (loadingMessageElement) {
                                        this.updateAIOpsStreamContent(loadingMessageElement, fullResponse);
                                    }
                                    return false;
                                }
                                return null;
                            };
                            
                            const result = processJsonMessages(rawData);
                            if (result === true) {
                                return; // 流结束
                            } else if (result === null) {
                                // 没有匹配到多个JSON，尝试单个JSON解析
                                try {
                                    const sseMessage = JSON.parse(rawData);
                                    if (sseMessage && sseMessage.type) {
                                        if (sseMessage.type === 'content') {
                                            fullResponse += sseMessage.data || '';
                                            if (loadingMessageElement) {
                                                this.updateAIOpsStreamContent(loadingMessageElement, fullResponse);
                                            }
                                        } else if (sseMessage.type === 'done') {
                                            console.log('AI Ops 流完成，最终内容长度:', fullResponse.length);
                                            this.updateAIOpsMessage(loadingMessageElement, fullResponse, []);
                                            return;
                                        } else if (sseMessage.type === 'error') {
                                            throw new Error(sseMessage.data || '智能运维分析失败');
                                        }
                                    } else {
                                        fullResponse += rawData;
                                        if (loadingMessageElement) {
                                            this.updateAIOpsStreamContent(loadingMessageElement, fullResponse);
                                        }
                                    }
                                } catch (e) {
                                    if (e.message.includes('智能运维')) throw e;
                                    // 非 JSON 格式，直接追加原始数据
                                    fullResponse += rawData;
                                    if (loadingMessageElement) {
                                        this.updateAIOpsStreamContent(loadingMessageElement, fullResponse);
                                    }
                                }
                            }
                        }
                    }
                }
            } finally {
                reader.releaseLock();
            }
        } catch (error) {
            throw error;
        }
    }

    updateAIOpsStreamContent(messageElement, content) {
        if (!messageElement) return;
        const messageContent = messageElement.querySelector('.message-content');
        if (!messageContent) return;
        messageContent.textContent = content;
        this.scrollToBottom();
    }

    updateAIOpsMessage(messageElement, response) {
        if (!messageElement) return;
        const messageContent = messageElement.querySelector('.message-content');
        if (!messageContent) return;
        messageContent.innerHTML = this.renderMarkdown(response);
        this.highlightCodeBlocks(messageContent);
        this.scrollToBottom();
    }

    async triggerAIOps() {
        if (this.isStreaming) {
            this.showNotification('请等待当前操作完成', 'warning');
            return;
        }

        const defaultProblem = '请分析当前系统告警';
        const inputProblem = window.prompt('请输入需要分析的问题/告警描述：', defaultProblem);
        const problem = (inputProblem || '').trim() || defaultProblem;

        // 新建对话
        this.newChat();
        
        // 添加"分析中..."的消息（带旋转动画）
        const loadingMessage = this.addLoadingMessage('分析中...');
        this.currentAIOpsMessage = loadingMessage; // 保存消息引用用于后续更新
        
        // 设置发送状态
        this.isStreaming = true;
        this.updateUI();

        try {
            await this.sendAIOpsRequest(loadingMessage, problem);
        } catch (error) {
            console.error('智能运维分析失败:', error);
            // 更新消息为错误信息
            if (loadingMessage) {
                const messageContent = loadingMessage.querySelector('.message-content');
                if (messageContent) {
                    messageContent.textContent = '抱歉，智能运维分析时出现错误：' + error.message;
                }
            }
        } finally {
            this.isStreaming = false;
            this.currentAIOpsMessage = null;
            this.updateUI();
        }
    }

    // 显示/隐藏加载遮罩层
    showLoadingOverlay(show) {
        if (this.loadingOverlay) {
            if (show) {
                this.loadingOverlay.style.display = 'flex';
                // 更新文字为智能运维
                const loadingText = this.loadingOverlay.querySelector('.loading-text');
                const loadingSubtext = this.loadingOverlay.querySelector('.loading-subtext');
                if (loadingText) loadingText.textContent = '智能运维分析中，请稍候...';
                if (loadingSubtext) loadingSubtext.textContent = '后端正在处理，请耐心等待';
                // 防止页面滚动
                document.body.style.overflow = 'hidden';
            } else {
                this.loadingOverlay.style.display = 'none';
                // 恢复页面滚动
                document.body.style.overflow = '';
            }
        }
    }

    // 显示/隐藏上传遮罩层
    showUploadOverlay(show, fileName = '') {
        if (this.loadingOverlay) {
            if (show) {
                this.loadingOverlay.style.display = 'flex';
                // 更新文字为上传中
                const loadingText = this.loadingOverlay.querySelector('.loading-text');
                const loadingSubtext = this.loadingOverlay.querySelector('.loading-subtext');
                if (loadingText) loadingText.textContent = '正在上传文件...';
                if (loadingSubtext) loadingSubtext.textContent = fileName ? `上传: ${fileName}` : '请稍候';
                // 防止页面滚动
                document.body.style.overflow = 'hidden';
            } else {
                this.loadingOverlay.style.display = 'none';
                // 恢复页面滚动
                document.body.style.overflow = '';
            }
        }
    }
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new SuperBizAgentApp();
});
