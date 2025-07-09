class MultiAgentAssistant {
    constructor() {
        this.sessionId = null;
        this.isLoading = false;
        this.initializeElements();
        this.bindEvents();
        this.checkHealth();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.questionForm = document.getElementById('questionForm');
        this.questionInput = document.getElementById('questionInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.statusBadge = document.getElementById('statusBadge');
        this.sessionInfo = document.getElementById('sessionInfo');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.healthCheckBtn = document.getElementById('healthCheckBtn');
        this.loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    }

    bindEvents() {
        this.questionForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.newChatBtn.addEventListener('click', () => this.startNewChat());
        this.healthCheckBtn.addEventListener('click', () => this.checkHealth());
        
        // Auto-resize input
        this.questionInput.addEventListener('input', this.autoResizeInput);
        
        // Focus on input when page loads
        this.questionInput.focus();
    }

    autoResizeInput() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const question = this.questionInput.value.trim();
        if (!question || this.isLoading) return;

        this.isLoading = true;
        this.updateUI();
        
        // Add user message to chat
        this.addMessage(question, 'user');
        this.questionInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await this.sendQuestion(question);
            this.removeTypingIndicator();
            
            if (response.error) {
                this.addErrorMessage(response.error);
            } else {
                this.addMessage(response.response, 'assistant');
                this.sessionId = response.session_id;
                this.updateSessionInfo();
            }
        } catch (error) {
            this.removeTypingIndicator();
            this.addErrorMessage('Failed to get response. Please try again.');
            console.error('Error:', error);
        } finally {
            this.isLoading = false;
            this.updateUI();
        }
    }

    async sendQuestion(question) {
        const requestData = {
            question: question,
            session_id: this.sessionId
        };

        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(timestamp);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addErrorMessage(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Error:</strong> ${error}
        `;
        
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-content" style="background-color: var(--bs-secondary);">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    updateUI() {
        this.sendBtn.disabled = this.isLoading;
        this.questionInput.disabled = this.isLoading;
        
        if (this.isLoading) {
            this.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        } else {
            this.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }

    startNewChat() {
        this.sessionId = null;
        this.chatMessages.innerHTML = `
            <div class="welcome-message text-center text-muted py-5">
                <i class="fas fa-comments fa-3x mb-3"></i>
                <h5>Welcome to the Multi-Agent AI Assistant</h5>
                <p>Ask me anything! I can search the web, access knowledge bases, and provide intelligent responses.</p>
                <div class="row mt-4">
                    <div class="col-md-4">
                        <div class="card bg-dark border-secondary">
                            <div class="card-body text-center">
                                <i class="fas fa-globe text-info mb-2"></i>
                                <h6>Web Search</h6>
                                <small class="text-muted">Real-time information and current events</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-dark border-secondary">
                            <div class="card-body text-center">
                                <i class="fas fa-database text-warning mb-2"></i>
                                <h6>Knowledge Base</h6>
                                <small class="text-muted">Company docs and FAQs</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card bg-dark border-secondary">
                            <div class="card-body text-center">
                                <i class="fas fa-brain text-success mb-2"></i>
                                <h6>Smart Routing</h6>
                                <small class="text-muted">Intelligent question routing</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        this.updateSessionInfo();
        this.questionInput.focus();
    }

    updateSessionInfo() {
        if (this.sessionId) {
            this.sessionInfo.textContent = `Session: ${this.sessionId.substring(0, 8)}...`;
        } else {
            this.sessionInfo.textContent = 'No active session';
        }
    }

    async checkHealth() {
        try {
            this.healthCheckBtn.disabled = true;
            this.healthCheckBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Checking...';
            
            const response = await fetch('/health');
            const data = await response.json();
            
            if (response.ok) {
                this.statusBadge.className = 'badge bg-success';
                this.statusBadge.textContent = 'Connected';
                
                // Show success message temporarily
                this.showTemporaryMessage(`System healthy - ${data.active_sessions} active sessions`, 'success');
            } else {
                throw new Error('Health check failed');
            }
        } catch (error) {
            this.statusBadge.className = 'badge bg-danger';
            this.statusBadge.textContent = 'Disconnected';
            this.showTemporaryMessage('Health check failed', 'error');
            console.error('Health check error:', error);
        } finally {
            this.healthCheckBtn.disabled = false;
            this.healthCheckBtn.innerHTML = '<i class="fas fa-heartbeat me-1"></i>Health Check';
        }
    }

    showTemporaryMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = type === 'success' ? 'success-message' : 'error-message';
        messageDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
            ${message}
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 3000);
    }

    // Utility method to format responses with markdown-like syntax
    formatResponse(text) {
        // Simple formatting for better readability
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.assistant = new MultiAgentAssistant();
});

// Handle keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        window.assistant.handleSubmit(new Event('submit'));
    }
    
    // Escape to clear input
    if (e.key === 'Escape') {
        window.assistant.questionInput.value = '';
        window.assistant.questionInput.focus();
    }
});
