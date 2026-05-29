document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const skipBtn = document.getElementById('skip-btn');
    const langToggleBtn = document.getElementById('lang-toggle-btn');
    
    let currentLang = 'he'; // Default to Hebrew
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
            skipBtn: '<i class="fa-solid fa-forward"></i> הצג תוצאות עכשיו',
            placeholder: 'לדוגמה: אני גרה בדירה, רוב היום בעבודה...',
            langBtnText: '<i class="fa-solid fa-globe"></i> English',
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
            enterTextPrompt: 'אנא הכנס טקסט.'
        },
        en: {
            disclaimerTitle: '<i class="fa-solid fa-triangle-exclamation"></i> Ethical Disclaimer',
            disclaimerP1: '⚠️ Please note: The agent\'s recommendations are only a preliminary suggestion based on raw data and statistical models.',
            disclaimerP2: 'A dog is a living soul, and a physical visit to the shelter is an essential and mandatory condition before adoption.',
            associationsTitle: '<i class="fa-solid fa-hand-holding-heart"></i> Partner Associations',
            agentName: 'PawMatch Smart Agent',
            statusText: 'Connected',
            skipBtn: '<i class="fa-solid fa-forward"></i> Show Results Now',
            placeholder: 'For example: I live in an apartment, most of the day at work...',
            langBtnText: '<i class="fa-solid fa-globe"></i> עברית',
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
            enterTextPrompt: 'Please enter text.'
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
        document.querySelector('.associations h4').innerHTML = trans.associationsTitle;
        document.querySelector('.agent-info h2').textContent = trans.agentName;
        document.querySelector('.status-text').textContent = trans.statusText;
        
        // Skip and Lang Toggle Buttons
        skipBtn.innerHTML = trans.skipBtn;
        langToggleBtn.innerHTML = trans.langBtnText;
        
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
        const trans = uiStrings[currentLang];
        
        if (data.match_type === 'perfect') {
            const dog = data.dogs[0];
            html = `
                <div class="results-container perfect-match">
                    <div class="hero-card">
                        <h3>${trans.perfectMatch}</h3>
                        <div class="score-badge">${trans.scoreLabel}: ${data.score}%</div>
                        <h2>${dog.name || 'Dog'} (${dog.breed})</h2>
                        <div class="details">
                            <p><i class="fa-solid fa-cake-candles"></i> ${trans.ageLabel}: ${dog.age_years} ${trans.years}</p>
                            <p><i class="fa-solid fa-weight-scale"></i> ${trans.weightLabel}: ${dog.weight_kg} ${trans.kg}</p>
                            <p><i class="fa-solid fa-paw"></i> ${trans.sizeLabel}: ${translateSize(dog.size)}</p>
                            <p><i class="fa-solid fa-palette"></i> ${trans.colorLabel}: ${translateColor(dog.color)}</p>
                        </div>
                    </div>
                    <div class="action-btns">
                        <button onclick="window.location.reload()"><i class="fa-solid fa-rotate-right"></i> ${trans.startOver}</button>
                    </div>
                </div>
            `;
        } else {
            const warningText = data.message || trans.partialWarning;
            const lowConfidence = data.score ? '' : `<div style="color:var(--danger); margin-bottom:1rem;">${warningText}</div>`;
            let cards = data.dogs.map(dog => `
                <div class="dog-card">
                    <div class="score">${dog.match_score ? dog.match_score + '%' : trans.alternative}</div>
                    <h4>${dog.name || 'Dog'} (${dog.breed})</h4>
                    <p>${trans.ageLabel}: ${dog.age_years} | ${trans.weightLabel}: ${dog.weight_kg}</p>
                    <p>${trans.sizeLabel}: ${translateSize(dog.size)} | ${trans.colorLabel}: ${translateColor(dog.color)}</p>
                </div>
            `).join('');
            
            html = `
                ${lowConfidence}
                <div class="results-container partial-match">
                    ${cards}
                </div>
                <div class="action-btns">
                    <button onclick="window.location.reload()"><i class="fa-solid fa-rotate-right"></i> ${trans.startOver}</button>
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
        const trans = uiStrings[currentLang];
        if (!text && !skip) return;
        
        if (!skip && !isButton) {
            addMessage(text, 'user');
            userInput.value = '';
        }

        addTypingIndicator();
        skipBtn.style.display = 'block'; // Show skip button after first interaction

        try {
            const endpoint = isButton ? '/api/button_click' : '/api/chat';
            // Include lang property in the payload
            const payload = isButton 
                ? { selection: text, lang: currentLang } 
                : { message: text, selects: {}, skip: skip, lang: currentLang };
            
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
            addMessage(trans.communicationError, 'agent');
        }
    }

    // Expose for inline onclick
    window.handleChatBtn = function(optionText) {
        addMessage(optionText, 'user');
        sendMessage(optionText, false, true);
    };

    // Lang toggle click event
    langToggleBtn.addEventListener('click', () => {
        currentLang = currentLang === 'he' ? 'en' : 'he';
        updateUIStrings();
    });

    sendBtn.addEventListener('click', () => sendMessage(userInput.value.trim()));
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage(userInput.value.trim());
    });
    skipBtn.addEventListener('click', () => {
        const trans = uiStrings[currentLang];
        addMessage(trans.skipUserMessage, 'user');
        sendMessage("", true);
    });

    // Initial setup
    updateUIStrings();
});
