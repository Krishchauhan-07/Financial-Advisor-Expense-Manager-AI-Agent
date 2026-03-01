document.addEventListener('DOMContentLoaded', () => {
    const attachBtn = document.getElementById('attachBtn');
    const attachmentMenu = document.getElementById('attachmentMenu');
    const apiKeyBtn = document.getElementById('apiKeyBtn');
    const apiModal = document.getElementById('apiModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const saveApiBtn = document.getElementById('saveApiBtn');
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');
    const chatArea = document.getElementById('chatArea');
    const chatIntro = document.querySelector('.chat-intro');

    let currentContext = ""; // Store extracted text from docs/links
    let userApiKey = ""; // Store API key if user provides it in UI

    // Backend URL (Assuming FastAPI runs on port 8000 locally)
    const API_BASE = "http://localhost:8000/api";

    // Toggle attachment menu
    attachBtn.addEventListener('click', () => {
        attachmentMenu.classList.toggle('hidden');
    });

    // Close attachment menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!attachBtn.contains(e.target) && !attachmentMenu.contains(e.target)) {
            attachmentMenu.classList.add('hidden');
        }
    });

    // Modal logic
    const apiKeyInput = document.getElementById('apiKeyInput'); // Assuming this exists or we add it

    apiKeyBtn.addEventListener('click', () => {
        apiModal.classList.remove('hidden');
    });

    closeModalBtn.addEventListener('click', () => {
        apiModal.classList.add('hidden');
    });

    saveApiBtn.addEventListener('click', () => {
        const inputField = apiModal.querySelector('input[type="password"]');
        if (inputField && inputField.value) {
            userApiKey = inputField.value;
        }

        saveApiBtn.textContent = 'Saved!';
        saveApiBtn.style.background = '#10b981';
        setTimeout(() => {
            apiModal.classList.add('hidden');
            saveApiBtn.textContent = 'Save Configurations';
            saveApiBtn.style.background = '';
        }, 1000);
    });

    // Auto-resize textarea
    userInput.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    function addMessage(text, sender, isHtml = false) {
        if (chatIntro) {
            chatIntro.style.display = 'none';
        }

        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        if (sender === 'bot') {
            avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';
        }

        const content = document.createElement('div');
        content.className = 'msg-content';

        if (isHtml) {
            content.innerHTML = text;

            // Apply markdown-like formatting for bot responses if not pure HTML
            if (sender === 'bot' && !text.includes('<div')) {
                // Simple markdown parser for basic bold and newlines
                let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                formatted = formatted.replace(/\n/g, '<br>');
                content.innerHTML = formatted;
            }
        } else {
            content.textContent = text;
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(content);

        chatArea.appendChild(msgDiv);
        chatArea.parentNode.scrollTop = chatArea.parentNode.scrollHeight;

        return msgDiv;
    }

    async function handleSend() {
        const text = userInput.value.trim();
        if (!text) return;

        // Add user message
        addMessage(text, 'user', false);

        // Reset input
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add typing indicator
        const typingMsg = addMessage("Thinking...", 'bot', false);

        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    context: currentContext,
                    api_key: userApiKey || null
                })
            });

            const data = await response.json();

            // Remove typing indicator
            chatArea.removeChild(typingMsg);

            if (!response.ok) {
                throw new Error(data.detail || 'API Error');
            }

            // Add real bot response
            addMessage(data.response, 'bot', true);

            // Clear context after using it once to avoid appending to every future message
            currentContext = "";

        } catch (error) {
            chatArea.removeChild(typingMsg);
            addMessage(`<span style="color: #ef4444;">Error: ${error.message}. Is the backend running?</span>`, 'bot', true);
        }
    }

    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // File Input Handlers
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.style.display = 'none';
    document.body.appendChild(fileInput);

    let currentUploadType = "";

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        attachmentMenu.classList.add('hidden');
        addMessage(`<div style="display: flex; align-items: center; gap: 10px;"><i class="fa-solid fa-file-circle-check" style="font-size: 1.5rem;"></i> <strong>Uploading:</strong> ${file.name}</div>`, 'user', true);

        const typingMsg = addMessage("Processing document...", 'bot', false);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const endpoint = currentUploadType === 'pdf' ? '/upload/pdf' : '/upload/image';

            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            chatArea.removeChild(typingMsg);

            if (!response.ok) {
                throw new Error(data.detail || 'Upload Error');
            }

            currentContext = data.extracted_text;
            addMessage("Document processed successfully! I've extracted the data. What would you like to know about it?", 'bot', false);

        } catch (error) {
            chatArea.removeChild(typingMsg);
            addMessage(`<span style="color: #ef4444;">Error processing file: ${error.message}</span>`, 'bot', true);
        }

        // Reset file input
        fileInput.value = '';
    });

    const attachOptions = document.querySelectorAll('.attach-option');
    attachOptions.forEach(opt => {
        opt.addEventListener('click', async (e) => {
            const typeText = opt.querySelector('span').textContent;

            if (typeText.includes('PDF')) {
                currentUploadType = 'pdf';
                fileInput.accept = '.pdf';
                fileInput.click();
            } else if (typeText.includes('Screenshot')) {
                currentUploadType = 'image';
                fileInput.accept = 'image/jpeg, image/png';
                fileInput.click();
            } else if (typeText.includes('Link')) {
                attachmentMenu.classList.add('hidden');
                const url = prompt("Enter the URL to analyze:");
                if (url) {
                    addMessage(`<div style="display: flex; align-items: center; gap: 10px;"><i class="fa-solid fa-link" style="font-size: 1.5rem;"></i> <strong>Link provided:</strong> ${url}</div>`, 'user', true);
                    const typingMsg = addMessage("Scraping webpage...", 'bot', false);

                    try {
                        const response = await fetch(`${API_BASE}/upload/link`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ url: url })
                        });

                        const data = await response.json();
                        chatArea.removeChild(typingMsg);

                        if (!response.ok) {
                            throw new Error(data.detail || 'Scraping Error');
                        }

                        currentContext = data.extracted_text;
                        addMessage("Webpage analyzed successfully! What would you like to know about it?", 'bot', false);

                    } catch (error) {
                        chatArea.removeChild(typingMsg);
                        addMessage(`<span style="color: #ef4444;">Error analyzing link: ${error.message}</span>`, 'bot', true);
                    }
                }
            }
        });
    });
});
