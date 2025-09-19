/**
 * Demo Interface Controls
 * Manages demo scenario execution, performance monitoring, and user interactions
 */

class DemoController {
    constructor() {
        this.currentScenario = null;
        this.currentPersona = null;
        this.conversationTurn = 0;
        this.startTime = Date.now();
        this.sessionTimer = null;
        this.performanceMetrics = {
            responseTimes: [],
            accuracyScores: [],
            userSatisfaction: 0
        };
        this.autoPlayMode = false;
        this.autoPlayDelay = 3000; // 3 seconds between auto messages

        this.initializeEventListeners();
        this.startSessionTimer();
        this.loadAvailableScenarios();
    }

    initializeEventListeners() {
        // Message input handling
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // Quick action buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-action-btn')) {
                const message = e.target.getAttribute('data-message');
                this.sendMessage(message);
            }
        });

        // Demo controls
        document.getElementById('reset-demo-btn').addEventListener('click', () => {
            this.resetDemo();
        });

        document.getElementById('auto-play-btn').addEventListener('click', () => {
            this.toggleAutoPlay();
        });

        document.getElementById('skip-step-btn').addEventListener('click', () => {
            this.skipCurrentStep();
        });

        document.getElementById('restart-scenario-btn').addEventListener('click', () => {
            this.restartScenario();
        });

        document.getElementById('export-transcript-btn').addEventListener('click', () => {
            this.exportTranscript();
        });

        // Scenario and persona selectors
        document.getElementById('scenario-selector').addEventListener('change', (e) => {
            this.selectScenario(e.target.value);
        });

        document.getElementById('persona-selector').addEventListener('change', (e) => {
            this.selectPersona(e.target.value);
        });

        // Modal controls
        document.getElementById('modal-cancel').addEventListener('click', () => {
            this.hideModal();
        });

        document.getElementById('modal-confirm').addEventListener('click', () => {
            this.handleModalConfirm();
        });
    }

    async sendMessage(messageText = null) {
        const messageInput = document.getElementById('message-input');
        const message = messageText || messageInput.value.trim();

        if (!message) return;

        // Clear input
        messageInput.value = '';

        // Add user message to chat
        this.addMessageToChat(message, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        // Record start time for response time measurement
        const requestStartTime = Date.now();

        try {
            // Send message to AI backend
            const response = await this.sendMessageToAI(message);

            // Calculate response time
            const responseTime = Date.now() - requestStartTime;
            this.recordResponseTime(responseTime);

            // Remove typing indicator
            this.hideTypingIndicator();

            // Add AI response to chat
            this.addMessageToChat(response.message, 'ai');

            // Update conversation metrics
            this.updateConversationMetrics(response);

            // Check if this completes a scenario step
            this.checkScenarioProgress(message, response);

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('I apologize, but I\'m experiencing technical difficulties. Please try again.', 'ai', 'error');
        }
    }

    async sendMessageToAI(message) {
        // Simulate AI response for demo purposes
        // In production, this would call the actual AI API

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                scenario: this.currentScenario,
                persona: this.currentPersona,
                demo_mode: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    addMessageToChat(message, sender, type = 'normal') {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3';

        if (sender === 'user') {
            messageDiv.className = 'flex items-start space-x-3 justify-end';
            messageDiv.innerHTML = `
                <div class="user-message message-enter-user">
                    <p>${this.escapeHtml(message)}</p>
                    <div class="message-timestamp">${this.formatTime(new Date())}</div>
                </div>
            `;
        } else {
            const iconClass = type === 'error' ? 'fas fa-exclamation-triangle text-red-500' : 'fas fa-robot text-white';
            const bgClass = type === 'error' ? 'bg-red-500' : 'bg-blue-500';

            messageDiv.innerHTML = `
                <div class="flex-shrink-0 w-8 h-8 ${bgClass} rounded-full flex items-center justify-center">
                    <i class="${iconClass} text-sm"></i>
                </div>
                <div class="ai-message message-enter-ai">
                    <div>${this.formatAIMessage(message)}</div>
                    <div class="message-timestamp">${this.formatTime(new Date())}</div>
                </div>
            `;
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Update conversation turn counter
        this.conversationTurn++;
        document.getElementById('conversation-turn').textContent = this.conversationTurn;
    }

    formatAIMessage(message) {
        // Format AI messages with better styling for demo
        // Handle property information, tax amounts, etc.

        // Replace property addresses with styled elements
        message = message.replace(
            /(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Drive|Dr|Lane|Ln|Road|Rd|Boulevard|Blvd|Circle|Cir|Court|Ct|Way),\s*[A-Za-z\s]+)/g,
            '<span class="property-address">$1</span>'
        );

        // Style tax amounts
        message = message.replace(
            /\$([0-9,]+(?:\.[0-9]{2})?)/g,
            '<span class="property-tax-amount">$$$1</span>'
        );

        // Style percentages
        message = message.replace(
            /(\d+(?:\.\d+)?%)/g,
            '<span class="font-medium text-blue-600">$1</span>'
        );

        return message;
    }

    showTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start space-x-3';
        typingDiv.innerHTML = `
            <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <i class="fas fa-robot text-white text-sm"></i>
            </div>
            <div class="bg-white rounded-lg p-4 shadow-sm">
                <div class="typing-indicator">
                    <span class="text-gray-500 text-sm">AI is typing</span>
                    <div class="flex space-x-1 ml-2">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;

        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    recordResponseTime(responseTime) {
        this.performanceMetrics.responseTimes.push(responseTime);

        // Update display
        document.getElementById('response-time').textContent = responseTime;

        // Calculate and display average
        const avgResponseTime = this.performanceMetrics.responseTimes.reduce((a, b) => a + b, 0) / this.performanceMetrics.responseTimes.length;
        document.getElementById('avg-response-time').textContent = Math.round(avgResponseTime);

        // Apply performance coloring
        const responseTimeElement = document.getElementById('response-time');
        responseTimeElement.className = this.getPerformanceClass(responseTime, [200, 500, 1000]);
    }

    updateConversationMetrics(response) {
        // Update accuracy score (simulated for demo)
        const accuracyScore = response.accuracy_score || this.simulateAccuracyScore();
        this.performanceMetrics.accuracyScores.push(accuracyScore);

        document.getElementById('accuracy-score').textContent = accuracyScore;

        // Calculate average accuracy
        const avgAccuracy = this.performanceMetrics.accuracyScores.reduce((a, b) => a + b, 0) / this.performanceMetrics.accuracyScores.length;
        document.getElementById('avg-accuracy').textContent = Math.round(avgAccuracy);

        // Update resolution rate (simulated)
        const resolutionRate = this.calculateResolutionRate();
        document.getElementById('resolution-rate').textContent = resolutionRate;

        // Update satisfaction score (simulated)
        const satisfactionScore = this.calculateSatisfactionScore();
        document.getElementById('satisfaction-score').textContent = satisfactionScore.toFixed(1);
    }

    simulateAccuracyScore() {
        // Simulate accuracy score between 90-98% for demo
        return Math.floor(Math.random() * 8) + 90;
    }

    calculateResolutionRate() {
        // Simulate resolution rate based on conversation turns
        const baseRate = 85;
        const turnPenalty = Math.max(0, (this.conversationTurn - 3) * 2);
        return Math.max(70, baseRate - turnPenalty);
    }

    calculateSatisfactionScore() {
        // Simulate satisfaction score between 4.2-4.8 for demo
        return 4.2 + (Math.random() * 0.6);
    }

    getPerformanceClass(value, thresholds) {
        if (value <= thresholds[0]) return 'performance-excellent';
        if (value <= thresholds[1]) return 'performance-good';
        if (value <= thresholds[2]) return 'performance-fair';
        return 'performance-poor';
    }

    selectScenario(scenarioId) {
        if (!scenarioId) {
            this.currentScenario = null;
            this.updateScenarioInfo(null);
            return;
        }

        this.currentScenario = scenarioId;
        this.loadScenarioInfo(scenarioId);
        this.updateScenarioProgress();
    }

    selectPersona(personaId) {
        this.currentPersona = personaId;
        this.loadPersonaInfo(personaId);
    }

    async loadScenarioInfo(scenarioId) {
        try {
            const response = await fetch(`/api/demo/scenarios/${scenarioId}`);
            const scenarioData = await response.json();

            this.updateScenarioInfo(scenarioData);
            this.resetScenarioProgress(scenarioData);

        } catch (error) {
            console.error('Error loading scenario:', error);
        }
    }

    updateScenarioInfo(scenarioData) {
        const scenarioInfoElement = document.getElementById('scenario-info');

        if (!scenarioData) {
            scenarioInfoElement.innerHTML = '<p class="text-sm text-gray-600">No scenario selected. Choose from the dropdown above to start a guided demo.</p>';
            return;
        }

        scenarioInfoElement.innerHTML = `
            <div class="space-y-2">
                <h4 class="font-medium text-blue-700">${scenarioData.title}</h4>
                <p class="text-sm text-gray-600">${scenarioData.description}</p>
                <div class="flex items-center space-x-2">
                    <span class="scenario-difficulty ${scenarioData.difficulty}">${scenarioData.difficulty}</span>
                    <span class="text-xs text-gray-500">${scenarioData.estimated_duration} min</span>
                </div>
            </div>
        `;
    }

    resetScenarioProgress(scenarioData) {
        this.currentStep = 0;
        this.totalSteps = scenarioData.conversation_flow ? scenarioData.conversation_flow.length : 0;
        this.updateProgressDisplay();
    }

    updateProgressDisplay() {
        document.getElementById('progress-steps').textContent = `${this.currentStep}/${this.totalSteps}`;

        const progressPercentage = this.totalSteps > 0 ? (this.currentStep / this.totalSteps) * 100 : 0;
        document.getElementById('progress-bar').style.width = `${progressPercentage}%`;

        document.getElementById('progress-description').textContent =
            this.currentStep === this.totalSteps ? 'Scenario completed!' :
            this.currentStep === 0 ? 'Scenario ready to start' :
            `Step ${this.currentStep} of ${this.totalSteps}`;
    }

    toggleAutoPlay() {
        this.autoPlayMode = !this.autoPlayMode;
        const autoPlayBtn = document.getElementById('auto-play-btn');

        if (this.autoPlayMode) {
            autoPlayBtn.innerHTML = '<i class="fas fa-pause mr-2"></i>Pause Auto-Play';
            autoPlayBtn.className = autoPlayBtn.className.replace('bg-green-600 hover:bg-green-700', 'bg-red-600 hover:bg-red-700');
            this.startAutoPlay();
        } else {
            autoPlayBtn.innerHTML = '<i class="fas fa-play mr-2"></i>Auto-Play Scenario';
            autoPlayBtn.className = autoPlayBtn.className.replace('bg-red-600 hover:bg-red-700', 'bg-green-600 hover:bg-green-700');
            this.stopAutoPlay();
        }
    }

    async startAutoPlay() {
        if (!this.currentScenario || !this.autoPlayMode) return;

        // Load scenario conversation flow
        try {
            const response = await fetch(`/api/demo/scenarios/${this.currentScenario}/conversation`);
            const conversationFlow = await response.json();

            for (let i = 0; i < conversationFlow.length && this.autoPlayMode; i++) {
                await this.delay(this.autoPlayDelay);
                if (this.autoPlayMode) {
                    this.sendMessage(conversationFlow[i].user_message);
                    this.currentStep = i + 1;
                    this.updateProgressDisplay();
                }
            }
        } catch (error) {
            console.error('Error in auto-play:', error);
        }
    }

    stopAutoPlay() {
        this.autoPlayMode = false;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    skipCurrentStep() {
        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.updateProgressDisplay();
        }
    }

    restartScenario() {
        this.showModal(
            'Restart Scenario',
            'Are you sure you want to restart the current scenario? This will clear the chat and reset progress.',
            () => {
                this.clearChat();
                this.resetScenarioProgress({ conversation_flow: [] });
                this.conversationTurn = 0;
                document.getElementById('conversation-turn').textContent = '0';
                this.hideModal();
            }
        );
    }

    resetDemo() {
        this.showModal(
            'Reset Demo Environment',
            'This will completely reset the demo environment, clearing all data and conversation history. Continue?',
            async () => {
                try {
                    const response = await fetch('/api/demo/reset', { method: 'POST' });
                    if (response.ok) {
                        location.reload();
                    } else {
                        throw new Error('Reset failed');
                    }
                } catch (error) {
                    console.error('Error resetting demo:', error);
                    this.hideModal();
                }
            }
        );
    }

    exportTranscript() {
        const chatMessages = document.getElementById('chat-messages');
        const messages = [];

        chatMessages.querySelectorAll('.user-message, .ai-message').forEach(messageElement => {
            const isUser = messageElement.classList.contains('user-message');
            const text = messageElement.querySelector('p')?.textContent || messageElement.textContent;
            const timestamp = messageElement.querySelector('.message-timestamp')?.textContent || '';

            messages.push({
                sender: isUser ? 'User' : 'AI Assistant',
                message: text.trim(),
                timestamp: timestamp
            });
        });

        const transcript = {
            session_info: {
                scenario: this.currentScenario,
                persona: this.currentPersona,
                start_time: new Date(this.startTime).toISOString(),
                duration_minutes: Math.round((Date.now() - this.startTime) / 60000),
                total_turns: this.conversationTurn
            },
            performance_metrics: {
                average_response_time: this.performanceMetrics.responseTimes.length > 0 ?
                    Math.round(this.performanceMetrics.responseTimes.reduce((a, b) => a + b, 0) / this.performanceMetrics.responseTimes.length) : 0,
                average_accuracy: this.performanceMetrics.accuracyScores.length > 0 ?
                    Math.round(this.performanceMetrics.accuracyScores.reduce((a, b) => a + b, 0) / this.performanceMetrics.accuracyScores.length) : 0,
                resolution_rate: this.calculateResolutionRate(),
                satisfaction_score: this.calculateSatisfactionScore()
            },
            conversation: messages
        };

        const blob = new Blob([JSON.stringify(transcript, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `demo_transcript_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        // Keep only the welcome message
        const welcomeMessage = chatMessages.firstElementChild;
        chatMessages.innerHTML = '';
        if (welcomeMessage) {
            chatMessages.appendChild(welcomeMessage);
        }
    }

    startSessionTimer() {
        const sessionTimerElement = document.getElementById('session-timer');

        this.sessionTimer = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            sessionTimerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    showModal(title, message, onConfirm) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-message').textContent = message;
        document.getElementById('demo-modal').classList.remove('hidden');
        document.getElementById('demo-modal').classList.add('flex');

        this.modalConfirmCallback = onConfirm;
    }

    hideModal() {
        document.getElementById('demo-modal').classList.add('hidden');
        document.getElementById('demo-modal').classList.remove('flex');
        this.modalConfirmCallback = null;
    }

    handleModalConfirm() {
        if (this.modalConfirmCallback) {
            this.modalConfirmCallback();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    async loadAvailableScenarios() {
        try {
            const response = await fetch('/api/demo/scenarios');
            const scenarios = await response.json();

            const scenarioSelector = document.getElementById('scenario-selector');
            scenarios.forEach(scenario => {
                const option = document.createElement('option');
                option.value = scenario.id;
                option.textContent = scenario.title;
                scenarioSelector.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading scenarios:', error);
        }
    }

    checkScenarioProgress(userMessage, aiResponse) {
        // Check if the current interaction matches expected scenario flow
        // This would be more sophisticated in a real implementation
        if (this.currentScenario && aiResponse.scenario_step_completed) {
            this.currentStep++;
            this.updateProgressDisplay();
        }
    }

    updateScenarioProgress() {
        // Update progress based on current scenario
        this.updateProgressDisplay();
    }
}

// Initialize demo controller when DOM is loaded
function initializeDemoInterface() {
    window.demoController = new DemoController();
}