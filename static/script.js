document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const skipBtn = document.getElementById('skip-btn');
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
            skipBtn: '<i class="fa-solid fa-forward"></i> <span class="btn-text">הצג תוצאות עכשיו</span>',
            placeholder: 'לדוגמה: אני גרה בדירה, רוב היום בעבודה...',
            langBtnText: '<i class="fa-solid fa-globe"></i> <span class="btn-text">English</span>',
            welcome: 'שלום! אני הסוכן החכם של PawMatch. ספרו לי בטקסט חופשי על אורח החיים שלכם (סביבת מגורים, שעות לבד בבית, ילדים וכו\' וכו\') ואיזה כלב אתם מחפשים.',
            
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
            skipBtn: '<i class="fa-solid fa-forward"></i> <span class="btn-text">Show Results Now</span>',
            placeholder: 'For example: I live in an apartment, most of the day at work...',
            langBtnText: '<i class="fa-solid fa-globe"></i> <span class="btn-text">עברית</span>',
            welcome: 'Hello! I am the PawMatch Smart Agent. Tell me in free text about your lifestyle (living environment, hours alone at home, kids, etc.) and what kind of dog you are looking for.',
            
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
        
        // Skip, Reset and Lang Toggle Buttons
        skipBtn.innerHTML = trans.skipBtn;
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
            messages[0].querySelector('.message-content').textContent = trans.welcome;
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
        localStorage.setItem('pawmatch_chat_history', JSON.stringify(messages));
    }

    function loadChatHistory() {
        const saved = localStorage.getItem('pawmatch_chat_history');
        if (saved) {
            try {
                const messages = JSON.parse(saved);
                if (messages && messages.length > 0) {
                    chatMessages.innerHTML = '';
                    messages.forEach(msg => {
                        addMessage(msg.content, msg.sender, true, false);
                    });
                    const hasResult = messages.some(msg => msg.content.includes('results-container') || msg.content.includes('dog-card'));
                    if (hasResult) {
                        skipBtn.style.display = 'none';
                    } else {
                        skipBtn.style.display = 'block';
                    }
                    return;
                }
            } catch (e) {
                console.error("Error loading chat history:", e);
            }
        }
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
        
        // Highlight disclaimer if partial match with low info
        if (!data.score) {
            document.getElementById('disclaimer-card').classList.add('low-confidence');
        }
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
        skipBtn.style.display = 'block'; // Show skip button after first interaction

        try {
            const savedSessionData = localStorage.getItem('pawmatch_session_data');
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
                localStorage.setItem('pawmatch_session_data', JSON.stringify(data.session_data));
            } else {
                localStorage.removeItem('pawmatch_session_data');
            }

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
    skipBtn.addEventListener('click', () => {
        const trans = uiStrings[currentLang];
        addMessage(trans.skipUserMessage, 'user');
        sendMessage("", true);
    });

    // Start over global handler
    window.handleStartOver = async function() {
        localStorage.removeItem('pawmatch_chat_history');
        localStorage.removeItem('pawmatch_session_data');
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
