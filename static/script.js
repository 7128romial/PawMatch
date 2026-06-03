document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const langToggleBtn = document.getElementById('lang-toggle-btn');
    
    let currentLang = localStorage.getItem('pawmatch_lang') || 'he'; // Persisted language preference
    let isWaitingForResults = false;

    // Translation Dictionaries
    const uiStrings = {
        he: {
            disclaimerTitle: '<i class="fa-solid fa-triangle-exclamation"></i> הצהרה אתית',
            disclaimerP1: '⚠️ שים לב: המלצות האג\'נט מהוות הצעה ראשונית בלבד המבוססת על נתונים יבשים ומודלים סטטיסטיים.',
            disclaimerP2: 'כלב הוא נפש חיה, וביקור פיזי במקלט הוא תנאי הכרחי ומחייב לפני אימוץ.',
            associationsTitle: '<i class="fa-solid fa-hand-holding-heart"></i> עמותות שותפות',
            agentName: 'הסוכן החכם של PawMatch',
            statusText: 'מחובר',
            placeholder: 'הקלד/י הודעה...',
            langBtnText: '<i class="fa-solid fa-globe"></i> <span class="btn-text">English</span>',
            welcome: 'שלום! אני הסוכן החכם של PawMatch. אני אעזור לכם למצוא את הכלב המושלם. בואו נתחיל: איזה גודל כלב אתם מחפשים?',
            
            // Results Hebrew
            perfectMatch: 'התאמה מושלמת!',
            scoreLabel: 'ציון',
            ageLabel: 'גיל',
            weightLabel: 'משקל',
            sizeLabel: 'גודל',
            colorLabel: 'צבע',
            kg: 'ק"ג',
            years: 'שנים',
            startOver: 'התחל מחדש',
            partialWarning: 'המלצה מבוססת על מידע חלקי',
            alternative: 'חלופה',
            communicationError: 'שגיאת תקשורת מול השרת.',
            skipUserMessage: 'הציגי לי תוצאות חלקיות עכשיו',
            enterTextPrompt: 'אנא הכנס טקסט.',
            otherTextPrompt: 'ספרו לי בפירוט בתיבת הטקסט מטה:'
        },
        en: {
            disclaimerTitle: '<i class="fa-solid fa-triangle-exclamation"></i> Ethical Disclaimer',
            disclaimerP1: '⚠️ Please note: The agent\'s recommendations are only a preliminary suggestion based on raw data and statistical models.',
            disclaimerP2: 'A dog is a living soul, and a physical visit to the shelter is an essential and mandatory condition before adoption.',
            associationsTitle: '<i class="fa-solid fa-hand-holding-heart"></i> Partner Associations',
            agentName: 'PawMatch Smart Agent',
            statusText: 'Connected',
            placeholder: 'Type a message...',
            langBtnText: '<i class="fa-solid fa-globe"></i> <span class="btn-text">עברית</span>',
            welcome: 'Hello! I am the PawMatch Smart Agent. I will help you find the perfect dog. Let\'s start: What size dog are you looking for?',
            
            // Results English
            perfectMatch: 'Perfect Match!',
            scoreLabel: 'Score',
            ageLabel: 'Age',
            weightLabel: 'Weight',
            sizeLabel: 'Size',
            colorLabel: 'Color',
            kg: 'kg',
            years: 'years',
            startOver: 'Start Over',
            partialWarning: 'Recommendation based on partial information',
            alternative: 'Alternative',
            communicationError: 'Communication error with the server.',
            skipUserMessage: 'Show me partial results now',
            enterTextPrompt: 'Please enter text.',
            otherTextPrompt: 'Please describe in detail in the text box below:'
        }
    };

    const sizeTranslations = {
        he: { 'Small': 'קטן', 'Medium': 'בינוני', 'Large': 'גדול' },
        en: { 'Small': 'Small', 'Medium': 'Medium', 'Large': 'Large' }
    };

    const colorTranslations = {
        he: {
            'White': 'לבן', 'Black': 'שחור', 'Tan': 'חום בהיר', 'Gray': 'אפור', 
            'Bicolor': 'דו-צבעי', 'Spotted': 'מנוקד', 'Cream': 'קרם', 'Red': 'ג\'ינג\'י', 
            'Brown': 'חום', 'Black and Tan': 'שחור וחום', 'Brindle': 'מנומר', 'Mixed': 'מעורב'
        },
        en: {
            'White': 'White', 'Black': 'Black', 'Tan': 'Tan', 'Gray': 'Gray', 
            'Bicolor': 'Bicolor', 'Spotted': 'Spotted', 'Cream': 'Cream', 'Red': 'Red', 
            'Brown': 'Brown', 'Black and Tan': 'Black & Tan', 'Brindle': 'Brindle', 'Mixed': 'Mixed'
        }
    };

    function translateSize(val) {
        return sizeTranslations[currentLang][val] || val;
    }

    function translateColor(val) {
        return colorTranslations[currentLang][val] || val;
    }

    function updateUIStrings() {
        const trans = uiStrings[currentLang];
        
        // Update document attributes
        document.documentElement.lang = currentLang;
        document.documentElement.dir = currentLang === 'he' ? 'rtl' : 'ltr';
        
        // Update static UI Elements
        document.getElementById('disclaimer-card').innerHTML = `
            <h3>${trans.disclaimerTitle}</h3>
            <p>${trans.disclaimerP1}</p>
            <p>${trans.disclaimerP2}</p>
        `;
        const banner = document.getElementById('chat-disclaimer-banner');
        if (banner) {
            const isHeb = currentLang === 'he';
            banner.querySelector('.banner-content').innerHTML = `
                <i class="fa-solid fa-triangle-exclamation"></i>
                <p><strong>${isHeb ? 'הצהרה אתית:' : 'Ethical Disclaimer:'}</strong> ${isHeb ? 'המלצות האג\'נט הן הצעה ראשונית בלבד. כלב הוא נפש חיה, וביקור פיזי במקלט הוא תנאי הכרחי ומחייב לפני אימוץ.' : 'The agent\'s recommendations are only a preliminary suggestion. A dog is a living soul, and a physical visit to the shelter is essential.'}</p>
            `;
        }
        document.querySelector('.associations h4').innerHTML = trans.associationsTitle;
        document.querySelector('.agent-info h2').textContent = trans.agentName;
        document.querySelector('.status-text').textContent = trans.statusText;
        
        // Reset and Lang Toggle Buttons
        langToggleBtn.innerHTML = trans.langBtnText;
        const resetBtn = document.getElementById('reset-btn');
        if (resetBtn) {
            resetBtn.innerHTML = `<i class="fa-solid fa-rotate-right"></i> <span class="btn-text">${trans.startOver}</span>`;
        }
        
        // Input Area
        userInput.placeholder = trans.placeholder;
        
        // Update first welcome message if chat has only the welcome message
        const messages = chatMessages.querySelectorAll('.message');
        if (messages.length === 1 && messages[0].classList.contains('agent')) {
            const opts = currentLang === 'he' ? ["קטן", "בינוני", "גדול", "אין לי העדפה"] : ["Small", "Medium", "Large", "No Preference"];
            let html = trans.welcome;
            html += '<div class="chat-buttons">';
            opts.forEach(opt => {
                html += `<button class="chat-btn" onclick="window.handleChatBtn('${opt}')">${opt}</button>`;
            });
            html += '</div>';
            messages[0].querySelector('.message-content').innerHTML = html;
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function saveChatHistory() {
        const messages = [];
        chatMessages.querySelectorAll('.message').forEach(msgDiv => {
            const sender = msgDiv.classList.contains('user') ? 'user' : 'agent';
            const contentDiv = msgDiv.querySelector('.message-content');
            messages.push({
                sender: sender,
                content: contentDiv.innerHTML
            });
        });
        sessionStorage.setItem('pawmatch_chat_history', JSON.stringify(messages));
    }

    function loadChatHistory() {
        const saved = sessionStorage.getItem('pawmatch_chat_history');
        if (saved) {
            try {
                const messages = JSON.parse(saved);
                if (messages && messages.length > 0) {
                    chatMessages.innerHTML = '';
                    messages.forEach(msg => {
                        addMessage(msg.content, msg.sender, true, false);
                    });
                    return;
                }
            } catch (e) {
                console.error("Error loading chat history:", e);
            }
        }
        
        // If there's no saved history (e.g. new tab or window), reset the backend session to ensure a completely clean start
        fetch('/api/reset', { method: 'POST' }).catch(e => console.error("Error resetting session:", e));
        
        updateUIStrings();
    }

    function addMessage(content, sender, isHtml = false, saveToStorage = true) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        if (isHtml) contentDiv.innerHTML = content;
        else contentDiv.textContent = content;
        msgDiv.appendChild(contentDiv);
        
        // Add feedback buttons for agent messages
        if (sender === 'agent') {
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'message-feedback';
            feedbackDiv.innerHTML = `
                <button class="feedback-btn thumbs-up" title="${currentLang === 'he' ? 'מועיל' : 'Helpful'}"><i class="fa-regular fa-thumbs-up"></i></button>
                <button class="feedback-btn thumbs-down" title="${currentLang === 'he' ? 'לא מועיל' : 'Not Helpful'}"><i class="fa-regular fa-thumbs-down"></i></button>
            `;
            
            const upBtn = feedbackDiv.querySelector('.thumbs-up');
            const downBtn = feedbackDiv.querySelector('.thumbs-down');
            upBtn.addEventListener('click', () => window.handleFeedback(upBtn, 1));
            downBtn.addEventListener('click', () => window.handleFeedback(downBtn, 0));
            
            msgDiv.appendChild(feedbackDiv);
        }
        
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
        if (saveToStorage) {
            saveChatHistory();
        }
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
        const trans = uiStrings[currentLang];
        
        const warningText = data.message || trans.partialWarning;
        // Show disclaimer/warning if we don't have a high confidence score
        const lowConfidence = data.score ? '' : `<div style="color:var(--danger); margin-bottom:1rem;">${warningText}</div>`;
        
        let cards = data.dogs.map(dog => {
            const matchReasonHtml = dog.match_reason 
                ? `<div class="match-reason"><strong>💡 ${currentLang === 'he' ? 'למה זה מתאים לכם:' : 'Why you match:'}</strong> ${dog.match_reason}</div>` 
                : '';
            const breedInfoHtml = dog.breed_info 
                ? `<div class="breed-info"><strong>ℹ️ ${currentLang === 'he' ? 'מידע על הגזע:' : 'About the Breed:'}</strong> ${dog.breed_info}</div>` 
                : '';
                
            return `
                <div class="dog-card premium-card">
                    <div class="dog-card-header">
                        <h4>${dog.name || 'Dog'} (${dog.breed})</h4>
                        <div class="score-badge-card">${dog.match_score ? dog.match_score + '%' : trans.alternative}</div>
                    </div>
                    <div class="dog-specs">
                        <span><i class="fa-solid fa-cake-candles"></i> ${trans.ageLabel}: ${dog.age_years} ${trans.years}</span>
                        <span><i class="fa-solid fa-weight-scale"></i> ${trans.weightLabel}: ${dog.weight_kg} ${trans.kg}</span>
                        <span><i class="fa-solid fa-paw"></i> ${trans.sizeLabel}: ${translateSize(dog.size)}</span>
                        <span><i class="fa-solid fa-palette"></i> ${trans.colorLabel}: ${translateColor(dog.color)}</span>
                    </div>
                    ${matchReasonHtml}
                    ${breedInfoHtml}
                </div>
            `;
        }).join('');
        
        html = `
            ${lowConfidence}
            <div class="results-container vertical-match-list">
                ${cards}
            </div>
            <div class="action-btns">
                <button onclick="window.handleStartOver()"><i class="fa-solid fa-rotate-right"></i> ${trans.startOver}</button>
            </div>
        `;
        
        return html;
    }

    async function sendMessage(text, skip = false, isButton = false) {
        const trans = uiStrings[currentLang];
        if (!text && !skip) return;
        
        if (!skip && !isButton) {
            addMessage(text, 'user');
            userInput.value = '';
        }

        addTypingIndicator();

        try {
            const savedSessionData = sessionStorage.getItem('pawmatch_session_data');
            const sessionData = savedSessionData ? JSON.parse(savedSessionData) : null;

            const endpoint = isButton ? '/api/button_click' : '/api/chat';
            const payload = isButton 
                ? { selection: text, lang: currentLang, session_data: sessionData } 
                : { message: text, selects: {}, skip: skip, lang: currentLang, session_data: sessionData };
            
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            removeTypingIndicator();

            if (data.session_data && Object.keys(data.session_data).length > 0) {
                sessionStorage.setItem('pawmatch_session_data', JSON.stringify(data.session_data));
            } else {
                sessionStorage.removeItem('pawmatch_session_data');
            }

            if (data.type === 'result') {
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
            addMessage(trans.communicationError, 'agent');
        }
    }

    // Expose for inline onclick
    window.handleChatBtn = function(optionText) {
        if (optionText === 'אחר' || optionText === 'Other') {
            const trans = uiStrings[currentLang];
            addMessage(optionText, 'user');
            addMessage(trans.otherTextPrompt, 'agent');
            userInput.focus();
            return;
        }
        addMessage(optionText, 'user');
        sendMessage(optionText, false, true);
    };

    // Lang toggle click event
    langToggleBtn.addEventListener('click', () => {
        currentLang = currentLang === 'he' ? 'en' : 'he';
        localStorage.setItem('pawmatch_lang', currentLang);
        updateUIStrings();
    });

    const resetBtnElement = document.getElementById('reset-btn');
    if (resetBtnElement) {
        resetBtnElement.addEventListener('click', () => window.handleStartOver());
    }

    sendBtn.addEventListener('click', () => sendMessage(userInput.value.trim()));
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage(userInput.value.trim());
    });

    // Feedback submission handler
    window.handleFeedback = async function(btn, rating) {
        const feedbackDiv = btn.parentElement;
        const msgDiv = feedbackDiv.parentElement;
        
        // Find all messages up to this one to construct the chat log context
        const allMessageDivs = Array.from(chatMessages.querySelectorAll('.message'));
        const index = allMessageDivs.indexOf(msgDiv);
        const contextMessages = [];
        
        for (let i = 0; i <= index; i++) {
            const currentDiv = allMessageDivs[i];
            const sender = currentDiv.classList.contains('user') ? 'user' : 'agent';
            const contentDiv = currentDiv.querySelector('.message-content');
            if (contentDiv) {
                const contentText = contentDiv.innerText || contentDiv.textContent;
                contextMessages.push({ sender, content: contentText.trim() });
            }
        }
        
        // Disable buttons in this container to prevent duplicate submissions
        const buttons = feedbackDiv.querySelectorAll('.feedback-btn');
        buttons.forEach(b => b.disabled = true);
        
        if (rating === 1) {
            btn.classList.add('active-up');
        } else {
            btn.classList.add('active-down');
        }
        
        try {
            const savedSessionData = sessionStorage.getItem('pawmatch_session_data');
            const sessionData = savedSessionData ? JSON.parse(savedSessionData) : null;
            
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    rating: rating,
                    chat_history: contextMessages,
                    session_data: sessionData,
                    lang: currentLang
                })
            });
            const result = await response.json();
            console.log("Feedback submitted successfully:", result);
        } catch (error) {
            console.error("Error submitting feedback:", error);
        }
    };

    // Start over global handler
    window.handleStartOver = async function() {
        sessionStorage.removeItem('pawmatch_chat_history');
        sessionStorage.removeItem('pawmatch_session_data');
        try {
            await fetch('/api/reset', { method: 'POST' });
        } catch (e) {
            console.error("Error resetting session:", e);
        }
        window.location.reload();
    };

    // Initial setup
    loadChatHistory();
});
