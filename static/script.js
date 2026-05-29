document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const skipBtn = document.getElementById('skip-btn');
    
    let isWaitingForResults = false;

    function getSelects() {
        return {};
    }


    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function addMessage(content, sender, isHtml = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        if (isHtml) contentDiv.innerHTML = content;
        else contentDiv.textContent = content;
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
        chatMessages.appendChild(indicator);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }
    
    function renderResults(data) {
        let html = '';
        if (data.match_type === 'perfect') {
            const dog = data.dogs[0];
            html = `
                <div class="results-container perfect-match">
                    <div class="hero-card">
                        <h3>התאמה מושלמת!</h3>
                        <div class="score-badge">ציון: ${data.score}%</div>
                        <h2>${dog.name || 'כלב'} (${dog.breed})</h2>
                        <div class="details">
                            <p><i class="fa-solid fa-cake-candles"></i> גיל: ${dog.age_years}</p>
                            <p><i class="fa-solid fa-weight-scale"></i> משקל: ${dog.weight_kg} ק"ג</p>
                            <p><i class="fa-solid fa-paw"></i> גודל: ${dog.size}</p>
                            <p><i class="fa-solid fa-palette"></i> צבע: ${dog.color}</p>
                        </div>
                    </div>
                    <div class="action-btns">
                        <button onclick="window.location.reload()"><i class="fa-solid fa-rotate-right"></i> התחל מחדש</button>
                    </div>
                </div>
            `;
        } else {
            const lowConfidence = data.score ? '' : '<div style="color:var(--danger); margin-bottom:1rem;">המלצה מבוססת על מידע חלקי</div>';
            let cards = data.dogs.map(dog => `
                <div class="dog-card">
                    <div class="score">${dog.match_score ? dog.match_score + '%' : 'חלופה'}</div>
                    <h4>${dog.name || 'כלב'} (${dog.breed})</h4>
                    <p>גיל: ${dog.age_years} | משקל: ${dog.weight_kg}</p>
                    <p>גודל: ${dog.size} | צבע: ${dog.color}</p>
                </div>
            `).join('');
            
            html = `
                ${lowConfidence}
                <div class="results-container partial-match">
                    ${cards}
                </div>
                <div class="action-btns">
                    <button onclick="window.location.reload()"><i class="fa-solid fa-rotate-right"></i> התחל מחדש</button>
                </div>
            `;
            
            // Highlight disclaimer if partial match with low info
            if (!data.score) {
                document.getElementById('disclaimer-card').classList.add('low-confidence');
            }
        }
        return html;
    }

    async function sendMessage(text, skip = false, isButton = false) {
        if (!text && !skip) return;
        
        if (!skip && !isButton) {
            addMessage(text, 'user');
            userInput.value = '';
        }

        addTypingIndicator();
        skipBtn.style.display = 'block'; // Show skip button after first interaction

        try {
            const endpoint = isButton ? '/api/button_click' : '/api/chat';
            const payload = isButton ? { selection: text } : { message: text, selects: getSelects(), skip: skip };
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            removeTypingIndicator();

            if (data.type === 'result') {
                skipBtn.style.display = 'none';
                addMessage(renderResults(data), 'agent', true);
            } else {
                let responseHtml = data.response;
                if (data.options) {
                    responseHtml += '<div class="chat-buttons">';
                    data.options.forEach(opt => {
                        responseHtml += `<button class="chat-btn" onclick="window.handleChatBtn('${opt}')">${opt}</button>`;
                    });
                    responseHtml += '</div>';
                }
                addMessage(responseHtml, 'agent', true);
            }
        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage('שגיאת תקשורת מול השרת.', 'agent');
        }
    }

    // Expose for inline onclick
    window.handleChatBtn = function(optionText) {
        addMessage(optionText, 'user');
        sendMessage(optionText, false, true);
    };

    sendBtn.addEventListener('click', () => sendMessage(userInput.value.trim()));
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage(userInput.value.trim());
    });
    skipBtn.addEventListener('click', () => {
        addMessage("הציגי לי תוצאות חלקיות עכשיו", 'user');
        sendMessage("", true);
    });
});
