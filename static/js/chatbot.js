// =========================================================
// KISANVISION360+ AI CHATBOT
// Smart Multilingual Farming Assistant
// =========================================================

"use strict";


// =========================================================
// GLOBAL CONFIGURATION
// =========================================================

const KISAN_CHATBOT = {

    maxMessageLength: 2000,

    apiUrl: "/ask_chatbot",

    storageKey: "kisanvision360_chat_history",

    requestTimeout: 30000,

    isSending: false,

    language: "en",

    role: "farmer",

    userName: "Farmer"

};


// =========================================================
// INITIALIZE
// =========================================================

document.addEventListener("DOMContentLoaded", function () {

    initializeChatbot();

});


// =========================================================
// INITIALIZE CHATBOT
// =========================================================

function initializeChatbot() {

    loadChatConfig();

    setupMessageInput();

    setupChatButtons();

    loadChatHistory();

    updateConnectionStatus("ready");

}


// =========================================================
// LOAD CONFIGURATION
// =========================================================

function loadChatConfig() {

    try {

        if (window.KISAN_CHATBOT_CONFIG) {

            KISAN_CHATBOT.apiUrl =
                window.KISAN_CHATBOT_CONFIG.chatbotUrl ||
                "/ask_chatbot";

            KISAN_CHATBOT.language =
                window.KISAN_CHATBOT_CONFIG.language ||
                getStoredLanguage() ||
                "en";

            KISAN_CHATBOT.role =
                window.KISAN_CHATBOT_CONFIG.role ||
                "farmer";

            KISAN_CHATBOT.userName =
                window.KISAN_CHATBOT_CONFIG.userName ||
                "Farmer";

        } else {

            KISAN_CHATBOT.language =
                getStoredLanguage() || "en";

        }

    }

    catch (error) {

        console.warn(
            "Chatbot configuration error:",
            error
        );

    }

}


// =========================================================
// GET STORED LANGUAGE
// =========================================================

function getStoredLanguage() {

    try {

        return (
            localStorage.getItem("kisanvision360_language") ||
            localStorage.getItem("language") ||
            document.documentElement.lang ||
            "en"
        );

    }

    catch (error) {

        return "en";

    }

}


// =========================================================
// TOGGLE CHAT
// =========================================================

function toggleChat() {

    const chatBox =
        document.getElementById("chatBox");

    if (!chatBox) {
        return;
    }

    chatBox.classList.toggle("active");

    const isOpen =
        chatBox.classList.contains("active");

    chatBox.setAttribute(
        "aria-hidden",
        isOpen ? "false" : "true"
    );


    if (isOpen) {

        const input =
            document.getElementById("message");

        if (input) {

            setTimeout(function () {

                input.focus();

            }, 150);

        }

        scrollChatToBottom();

    }

}


// =========================================================
// CLOSE CHAT
// =========================================================

function closeChat() {

    const chatBox =
        document.getElementById("chatBox");

    if (!chatBox) {
        return;
    }

    chatBox.classList.remove("active");

    chatBox.setAttribute(
        "aria-hidden",
        "true"
    );

}


// =========================================================
// QUICK QUESTION
// =========================================================

function quickQuestion(question) {

    const input =
        document.getElementById("message");

    if (!input || !question) {
        return;
    }

    input.value =
        String(question).substring(
            0,
            KISAN_CHATBOT.maxMessageLength
        );

    input.focus();

    sendMessage();

}


// =========================================================
// ADD USER MESSAGE
// =========================================================

function addUserMessage(message, save = true) {

    const chatBody =
        document.getElementById("chat-box");

    if (!chatBody || !message) {
        return;
    }


    const div =
        document.createElement("div");

    div.className = "user-message";


    const timestamp =
        getCurrentTime();


    div.innerHTML = `

        <div class="message-content">

            <div class="user-text">
                ${escapeHTML(message)}
            </div>

            <div class="message-time">
                ${timestamp}
            </div>

        </div>

    `;


    chatBody.appendChild(div);

    scrollChatToBottom();


    if (save) {

        saveChatMessage(
            "user",
            message
        );

    }

}


// =========================================================
// ADD BOT MESSAGE
// =========================================================

function addBotMessage(message, save = true) {

    const chatBody =
        document.getElementById("chat-box");

    if (!chatBody || !message) {
        return;
    }


    const div =
        document.createElement("div");

    div.className = "bot-reply";


    const timestamp =
        getCurrentTime();


    div.innerHTML = `

        <div class="message-avatar">
            🤖
        </div>

        <div class="message-content">

            <div class="bot">

                ${formatBotMessage(message)}

            </div>

            <div class="message-time">

                ${timestamp}

            </div>

        </div>

    `;


    chatBody.appendChild(div);

    scrollChatToBottom();


    if (save) {

        saveChatMessage(
            "bot",
            message
        );

    }

}


// =========================================================
// SEND MESSAGE
// =========================================================

async function sendMessage() {

    if (KISAN_CHATBOT.isSending) {
        return;
    }


    const input =
        document.getElementById("message");

    const chatBody =
        document.getElementById("chat-box");

    if (!input || !chatBody) {

        console.error(
            "❌ Chatbot HTML elements not found."
        );

        return;

    }


    let message =
        input.value.trim();


    if (!message) {
        return;
    }


    // -----------------------------------------
    // CHARACTER LIMIT
    // -----------------------------------------

    if (
        message.length >
        KISAN_CHATBOT.maxMessageLength
    ) {

        addBotMessage(
            `⚠️ Please keep your message within ${KISAN_CHATBOT.maxMessageLength} characters.`
        );

        return;

    }


    // -----------------------------------------
    // LOCK REQUEST
    // -----------------------------------------

    KISAN_CHATBOT.isSending = true;

    setSendButtonState(true);


    // -----------------------------------------
    // SHOW USER MESSAGE
    // -----------------------------------------

    addUserMessage(message);

    input.value = "";

    updateCharacterCount(0);


    // -----------------------------------------
    // SHOW TYPING
    // -----------------------------------------

    showTypingIndicator();

    updateConnectionStatus("connecting");


    try {

        // -------------------------------------
        // CREATE REQUEST
        // -------------------------------------

        const controller =
            new AbortController();

        const timeout =
            setTimeout(function () {

                controller.abort();

            }, KISAN_CHATBOT.requestTimeout);


        // -------------------------------------
        // SEND TO FLASK
        // -------------------------------------

        const response =
            await fetch(
                KISAN_CHATBOT.apiUrl,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json",

                        "X-Requested-With":
                            "XMLHttpRequest"

                    },

                    credentials: "same-origin",

                    body: JSON.stringify({

                        message: message,

                        language:
                            KISAN_CHATBOT.language,

                        role:
                            KISAN_CHATBOT.role

                    }),

                    signal:
                        controller.signal

                }
            );


        clearTimeout(timeout);


        // -------------------------------------
        // CHECK HTTP STATUS
        // -------------------------------------

        if (!response.ok) {

            let serverMessage = "";

            try {

                const errorData =
                    await response.json();

                serverMessage =
                    errorData.message ||
                    errorData.error ||
                    "";

            }

            catch (jsonError) {

                serverMessage = "";

            }


            throw new Error(

                serverMessage ||
                "Server returned HTTP " +
                response.status

            );

        }


        // -------------------------------------
        // READ RESPONSE
        // -------------------------------------

        const data =
            await response.json();


        // -------------------------------------
        // HIDE TYPING
        // -------------------------------------

        hideTypingIndicator();


        // -------------------------------------
        // SUCCESS
        // -------------------------------------

        if (
            data &&
            (
                data.reply ||
                data.response ||
                data.message
            )
        ) {

            const reply =
                data.reply ||
                data.response ||
                data.message;


            addBotMessage(reply);

            updateConnectionStatus("online");


            // Update language if backend
            // sends current language.

            if (data.language) {

                KISAN_CHATBOT.language =
                    data.language;

            }

        }

        else {

            addBotMessage(
                "🤖 Sorry, I could not generate an answer. Please try again."
            );

            updateConnectionStatus("online");

        }

    }


    catch (error) {

        console.error(
            "❌ KISANVISION360 CHATBOT ERROR:",
            error
        );


        hideTypingIndicator();


        updateConnectionStatus("offline");


        let errorMessage =
            "⚠️ Unable to connect to KisanVision360 AI. Please try again.";


        if (
            error &&
            error.name === "AbortError"
        ) {

            errorMessage =
                "⏱️ The AI response took too long. Please try again.";

        }


        addBotMessage(errorMessage);

    }


    finally {

        KISAN_CHATBOT.isSending = false;

        setSendButtonState(false);


        if (input) {

            input.focus();

        }

    }

}


// =========================================================
// SET SEND BUTTON STATE
// =========================================================

function setSendButtonState(disabled) {

    const buttons =
        document.querySelectorAll(
            "#sendButton, .send-btn, button[type='submit']"
        );


    buttons.forEach(function (button) {

        if (
            button.closest("#chatBox") ||
            button.id === "sendButton"
        ) {

            button.disabled =
                disabled;

            button.setAttribute(
                "aria-disabled",
                disabled ? "true" : "false"
            );

        }

    });

}


// =========================================================
// TYPING INDICATOR
// =========================================================

function showTypingIndicator() {

    const indicator =
        document.getElementById(
            "typingIndicator"
        );

    if (!indicator) {
        return;
    }

    indicator.style.display = "block";

    indicator.setAttribute(
        "aria-hidden",
        "false"
    );

    scrollChatToBottom();

}


// =========================================================
// HIDE TYPING INDICATOR
// =========================================================

function hideTypingIndicator() {

    const indicator =
        document.getElementById(
            "typingIndicator"
        );

    if (!indicator) {
        return;
    }

    indicator.style.display = "none";

    indicator.setAttribute(
        "aria-hidden",
        "true"
    );

}


// =========================================================
// CONNECTION STATUS
// =========================================================

function updateConnectionStatus(status) {

    const element =
        document.getElementById(
            "chatConnectionStatus"
        );

    if (!element) {
        return;
    }


    element.classList.remove(
        "online",
        "offline",
        "connecting",
        "ready"
    );


    element.classList.add(status);


    const labels = {

        online:
            "● AI Online",

        offline:
            "● Offline",

        connecting:
            "● Connecting...",

        ready:
            "● Ready"

    };


    element.textContent =
        labels[status] ||
        "● Ready";

}


// =========================================================
// ENTER KEY
// =========================================================

function setupMessageInput() {

    const input =
        document.getElementById("message");


    if (!input) {

        console.warn(
            "⚠️ Chat input #message not found."
        );

        return;

    }


    input.addEventListener(
        "keydown",
        function (event) {

            // Enter = Send
            // Shift + Enter = New Line

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();

            }

        }
    );


    input.addEventListener(
        "input",
        function () {

            updateCharacterCount(
                input.value.length
            );

            autoResizeInput(input);

        }
    );


    updateCharacterCount(
        input.value.length
    );

}


// =========================================================
// AUTO RESIZE TEXTAREA
// =========================================================

function autoResizeInput(input) {

    if (!input) {
        return;
    }


    if (
        input.tagName.toLowerCase() !==
        "textarea"
    ) {

        return;

    }


    input.style.height = "auto";


    const maxHeight = 140;


    input.style.height =
        Math.min(
            input.scrollHeight,
            maxHeight
        ) + "px";

}


// =========================================================
// CHARACTER COUNT
// =========================================================

function updateCharacterCount(length) {

    const counter =
        document.getElementById(
            "messageCounter"
        );


    if (!counter) {
        return;
    }


    counter.textContent =
        `${length}/${KISAN_CHATBOT.maxMessageLength}`;


    counter.classList.remove(
        "warning",
        "danger"
    );


    if (
        length >
        KISAN_CHATBOT.maxMessageLength * 0.85
    ) {

        counter.classList.add(
            "warning"
        );

    }


    if (
        length >=
        KISAN_CHATBOT.maxMessageLength
    ) {

        counter.classList.add(
            "danger"
        );

    }

}


// =========================================================
// CHAT BUTTONS
// =========================================================

function setupChatButtons() {

    // Clear chat

    const clearButton =
        document.getElementById(
            "clearChat"
        );


    if (clearButton) {

        clearButton.addEventListener(
            "click",
            function () {

                clearChat();

            }
        );

    }


    // Close button

    const closeButton =
        document.getElementById(
            "closeChat"
        );


    if (closeButton) {

        closeButton.addEventListener(
            "click",
            function () {

                closeChat();

            }
        );

    }

}


// =========================================================
// CLEAR CHAT
// =========================================================

function clearChat() {

    const chatBody =
        document.getElementById("chat-box");


    if (!chatBody) {
        return;
    }


    const confirmed =
        window.confirm(
            "Clear your KisanVision360 AI chat history?"
        );


    if (!confirmed) {
        return;
    }


    chatBody.innerHTML = "";


    try {

        sessionStorage.removeItem(
            KISAN_CHATBOT.storageKey
        );

    }

    catch (error) {

        console.warn(
            "Unable to clear local chat history.",
            error
        );

    }


    // Optional welcome message

    addBotMessage(
        getWelcomeMessage(),
        false
    );

}


// =========================================================
// WELCOME MESSAGE
// =========================================================

function getWelcomeMessage() {

    const name =
        escapeHTML(
            KISAN_CHATBOT.userName ||
            "Farmer"
        );


    const messages = {

        en:
            `Hello ${name}! 👋 I am your KisanVision360+ AI farming assistant. Ask me about weather, crops, disease, irrigation, mandi prices, schemes, finance or farming guidance.`,

        hi:
            `नमस्ते ${name}! 👋 मैं आपका KisanVision360+ AI कृषि सहायक हूँ। आप मौसम, फसल, रोग, सिंचाई, मंडी भाव, योजनाओं और खेती के बारे में पूछ सकते हैं।`,

        mr:
            `नमस्कार ${name}! 👋 मी तुमचा KisanVision360+ AI कृषी सहाय्यक आहे. तुम्ही हवामान, पिके, रोग, सिंचन, बाजारभाव, योजना आणि शेतीबद्दल विचारू शकता.`

    };


    return (
        messages[
            KISAN_CHATBOT.language
        ] ||
        messages.en
    );

}


// =========================================================
// SAVE CHAT HISTORY
// =========================================================

function saveChatMessage(type, message) {

    try {

        const history =
            JSON.parse(
                sessionStorage.getItem(
                    KISAN_CHATBOT.storageKey
                ) || "[]"
            );


        history.push({

            type: type,

            message: String(message),

            timestamp:
                new Date().toISOString()

        });


        // Keep only latest 50 messages

        if (history.length > 50) {

            history.splice(
                0,
                history.length - 50
            );

        }


        sessionStorage.setItem(

            KISAN_CHATBOT.storageKey,

            JSON.stringify(history)

        );

    }

    catch (error) {

        console.warn(
            "Unable to save chat history.",
            error
        );

    }

}


// =========================================================
// LOAD CHAT HISTORY
// =========================================================

function loadChatHistory() {

    const chatBody =
        document.getElementById("chat-box");


    if (!chatBody) {
        return;
    }


    try {

        const history =
            JSON.parse(
                sessionStorage.getItem(
                    KISAN_CHATBOT.storageKey
                ) || "[]"
            );


        if (!Array.isArray(history)) {
            return;
        }


        history.forEach(function (item) {

            if (
                !item ||
                !item.message
            ) {

                return;

            }


            if (item.type === "user") {

                addUserMessage(
                    item.message,
                    false
                );

            }

            else {

                addBotMessage(
                    item.message,
                    false
                );

            }

        });

    }

    catch (error) {

        console.warn(
            "Unable to load chat history.",
            error
        );

    }


    scrollChatToBottom();

}


// =========================================================
// SCROLL CHAT TO BOTTOM
// =========================================================

function scrollChatToBottom() {

    const chatBody =
        document.getElementById(
            "chat-box"
        );


    if (!chatBody) {
        return;
    }


    requestAnimationFrame(function () {

        chatBody.scrollTop =
            chatBody.scrollHeight;

    });

}


// =========================================================
// CURRENT TIME
// =========================================================

function getCurrentTime() {

    try {

        return new Date().toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );

    }

    catch (error) {

        return "";

    }

}


// =========================================================
// FORMAT BOT MESSAGE
// =========================================================

function formatBotMessage(message) {

    if (!message) {
        return "";
    }


    let text =
        String(message);


    // -----------------------------------------
    // FIRST ESCAPE HTML
    // -----------------------------------------

    text =
        escapeHTML(text);


    // -----------------------------------------
    // BOLD
    // **text**
    // -----------------------------------------

    text =
        text.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    // -----------------------------------------
    // BULLET POINTS
    // -----------------------------------------

    text =
        text.replace(
            /^[•*-]\s+(.*)$/gm,
            "<div class=\"bot-bullet\">• $1</div>"
        );


    // -----------------------------------------
    // NUMBERED LIST
    // -----------------------------------------

    text =
        text.replace(
            /^(\d+)\.\s+(.*)$/gm,
            "<div class=\"bot-number\">$1. $2</div>"
        );


    // -----------------------------------------
    // LINE BREAKS
    // -----------------------------------------

    text =
        text.replace(
            /\r?\n/g,
            "<br>"
        );


    return text;

}


// =========================================================
// SECURITY
// =========================================================

function escapeHTML(text) {

    const div =
        document.createElement("div");


    div.textContent =
        String(text);


    return div.innerHTML;

}


// =========================================================
// PUBLIC CHATBOT API
// =========================================================

window.KisanVisionChatbot = {

    sendMessage: sendMessage,

    toggleChat: toggleChat,

    closeChat: closeChat,

    quickQuestion: quickQuestion,

    clearChat: clearChat,

    addUserMessage: addUserMessage,

    addBotMessage: addBotMessage

};


// =========================================================
// DEBUG INFORMATION
// =========================================================

console.log(
    "🌱 KisanVision360+ AI Chatbot loaded successfully."
);