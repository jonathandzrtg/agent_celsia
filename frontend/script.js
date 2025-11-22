// ========================================
// Configuration
// ========================================
const API_URL = 'http://localhost:8000/chat';
const SESSION_ID = 'celsia-chat-session'; // Single session for all users
const STORAGE_KEY = 'celsia-chat-history';

// ========================================
// DOM Elements
// ========================================
const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const messagesContainer = document.getElementById('messagesContainer');
const typingIndicator = document.getElementById('typingIndicator');
const clearChatBtn = document.getElementById('clearChatBtn');
const charCounter = document.getElementById('charCounter');
const celsiaLogo = document.getElementById('celsia-logo');

// ========================================
// Initialize
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    setupEventListeners();
    autoResizeTextarea();
    
    // Hide logo with fallback if image doesn't exist
    celsiaLogo.addEventListener('error', () => {
        celsiaLogo.style.display = 'none';
    });
});

// ========================================
// Event Listeners
// ========================================
function setupEventListeners() {
    // Form submission
    chatForm.addEventListener('submit', handleSubmit);
    
    // Clear chat button
    clearChatBtn.addEventListener('click', handleClearChat);
    
    // Textarea auto-resize and character counter
    userInput.addEventListener('input', () => {
        autoResizeTextarea();
        updateCharCounter();
    });
    
    // Submit on Enter (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
}

// ========================================
// Message Handling
// ========================================
async function handleSubmit(e) {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;
    
    // Disable input while processing
    setInputState(false);
    
    // Add user message to UI
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    autoResizeTextarea();
    updateCharCounter();
    
    // Show typing indicator
    showTypingIndicator(true);
    
    try {
        // Send message to API
        const response = await sendMessageToAPI(message);
        
        // Hide typing indicator
        showTypingIndicator(false);
        
        // Add bot response to UI
        addMessage(response, 'bot');
        
    } catch (error) {
        showTypingIndicator(false);
        handleError(error);
    } finally {
        // Re-enable input
        setInputState(true);
        userInput.focus();
    }
}

async function sendMessageToAPI(message) {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_message: message,
                session_id: SESSION_ID
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.response || 'Lo siento, no pude generar una respuesta.';
        
    } catch (error) {
        console.error('Error calling API:', error);
        throw error;
    }
}

function addMessage(content, sender) {
    // Remove welcome message if it exists
    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatar = createAvatar(sender);
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    // Save to localStorage
    saveChatHistory();
}

function createAvatar(sender) {
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '24');
    svg.setAttribute('height', '24');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'currentColor');
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    
    if (sender === 'bot') {
        path.setAttribute('d', 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z');
    } else {
        path.setAttribute('d', 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z');
    }
    
    svg.appendChild(path);
    avatar.appendChild(svg);
    
    return avatar;
}

// ========================================
// UI State Management
// ========================================
function setInputState(enabled) {
    userInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
}

function showTypingIndicator(show) {
    if (show) {
        typingIndicator.classList.add('active');
        scrollToBottom();
    } else {
        typingIndicator.classList.remove('active');
    }
}

function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

function autoResizeTextarea() {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
}

function updateCharCounter() {
    const currentLength = userInput.value.length;
    const maxLength = userInput.getAttribute('maxlength');
    charCounter.textContent = `${currentLength}/${maxLength}`;
    
    if (currentLength > maxLength * 0.9) {
        charCounter.style.color = '#ff7705';
    } else {
        charCounter.style.color = '#8a8a8c';
    }
}

// ========================================
// Chat History (LocalStorage)
// ========================================
function saveChatHistory() {
    const messages = [];
    const messageElements = messagesContainer.querySelectorAll('.message');
    
    messageElements.forEach(msgEl => {
        const sender = msgEl.classList.contains('user') ? 'user' : 'bot';
        const content = msgEl.querySelector('.message-content').textContent;
        messages.push({ sender, content });
    });
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
}

function loadChatHistory() {
    const savedHistory = localStorage.getItem(STORAGE_KEY);
    
    if (savedHistory) {
        try {
            const messages = JSON.parse(savedHistory);
            
            if (messages.length > 0) {
                // Remove welcome message
                const welcomeMessage = messagesContainer.querySelector('.welcome-message');
                if (welcomeMessage) {
                    welcomeMessage.remove();
                }
                
                // Restore messages
                messages.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${msg.sender}`;
                    
                    const avatar = createAvatar(msg.sender);
                    const messageContent = document.createElement('div');
                    messageContent.className = 'message-content';
                    messageContent.textContent = msg.content;
                    
                    messageDiv.appendChild(avatar);
                    messageDiv.appendChild(messageContent);
                    
                    messagesContainer.appendChild(messageDiv);
                });
                
                scrollToBottom();
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            localStorage.removeItem(STORAGE_KEY);
        }
    }
}

function handleClearChat() {
    // Show confirmation dialog
    const confirmed = confirm('¿Estás seguro de que deseas limpiar toda la conversación?');
    
    if (confirmed) {
        // Clear messages from UI
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="bot-avatar">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                    </svg>
                </div>
                <div class="welcome-text">
                    <h2>¡Bienvenido a Celsia!</h2>
                    <p>Soy tu asistente virtual. Estoy aquí para ayudarte con información sobre nuestros servicios, facturación, puntos de pago y más.</p>
                    <p class="welcome-suggestions">Puedes preguntarme sobre:</p>
                    <ul class="suggestions-list">
                        <li>📞 Información de contacto</li>
                        <li>💡 Servicios de energía</li>
                        <li>💳 Facturación y pagos</li>
                        <li>🏢 Ubicaciones y sedes</li>
                        <li>♻️ Programas de sostenibilidad</li>
                    </ul>
                </div>
            </div>
        `;
        
        // Clear localStorage
        localStorage.removeItem(STORAGE_KEY);
        
        // Reset input
        userInput.value = '';
        autoResizeTextarea();
        updateCharCounter();
        
        // Focus input
        userInput.focus();
    }
}

// ========================================
// Error Handling
// ========================================
function handleError(error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `Error: No se pudo conectar con el servidor. Por favor, verifica que el API esté ejecutándose en ${API_URL}`;
    
    messagesContainer.appendChild(errorDiv);
    scrollToBottom();
    
    // Remove error message after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}
