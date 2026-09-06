/* =========================================================
   KISANVISION360+ AI CHATBOT
   c_chatbot.js
   OPEN + CLOSE + SEND + RECEIVE ANSWERS
========================================================= */

(function () {

    "use strict";

    console.log("KisanVision360+ Chatbot JS Loaded");


    /* =====================================================
       CONFIGURATION
    ===================================================== */

    const config = window.KISAN_CHATBOT_CONFIG || {};

    const chatbotUrl =
        config.chatbotUrl || "/ask-chatbot";


    /* =====================================================
       ELEMENTS
    ===================================================== */

    function get(id) {
        return document.getElementById(id);
    }


    /* =====================================================
       OPEN CHAT
    ===================================================== */

    function openChat() {

        const box = get("chatBox");

        if (!box) {
            console.error("chatBox not found");
            return;
        }

        box.classList.add("open");
        box.classList.add("active");

        box.setAttribute("aria-hidden", "false");

        const button = get("chatbotButton");

        if (button) {
            button.setAttribute("aria-expanded", "true");
        }

        setTimeout(function () {

            const input =
                get("chatMessageInput");

            if (input) {
                input.focus();
            }

        }, 200);

    }


    /* =====================================================
       CLOSE CHAT
    ===================================================== */

    function closeChat() {

        const box = get("chatBox");

        if (!box) {
            return;
        }

        box.classList.remove("open");
        box.classList.remove("active");

        box.setAttribute("aria-hidden", "true");

        const button = get("chatbotButton");

        if (button) {
            button.setAttribute("aria-expanded", "false");
        }

    }


    /* =====================================================
       TOGGLE CHAT
    ===================================================== */

    function toggleChat() {

        const box = get("chatBox");

        if (!box) {
            return;
        }

        if (
            box.classList.contains("open") ||
            box.classList.contains("active")
        ) {

            closeChat();

        } else {

            openChat();

        }

    }


    /* =====================================================
       SHOW TYPING
    ===================================================== */

    function showTyping() {

        const typing =
            get("typingIndicator");

        if (typing) {

            typing.style.display = "flex";

        }

        scrollChat();

    }


    /* =====================================================
       HIDE TYPING
    ===================================================== */

    function hideTyping() {

        const typing =
            get("typingIndicator");

        if (typing) {

            typing.style.display = "none";

        }

    }


    /* =====================================================
       SCROLL CHAT
    ===================================================== */

    function scrollChat() {

        const messages =
            get("chatMessages");

        if (messages) {

            messages.scrollTop =
                messages.scrollHeight;

        }

    }


    /* =====================================================
       ADD USER MESSAGE
    ===================================================== */

    function addUserMessage(message) {

        const messages =
            get("chatMessages");

        if (!messages) {
            return;
        }


        const wrapper =
            document.createElement("div");

        wrapper.className =
            "user-message";


        const content =
            document.createElement("div");

        content.className =
            "message-content";


        const bubble =
            document.createElement("div");

        bubble.className =
            "user";


        bubble.textContent =
            message;


        content.appendChild(bubble);

        wrapper.appendChild(content);

        messages.appendChild(wrapper);


        scrollChat();

    }


    /* =====================================================
       ADD BOT MESSAGE
    ===================================================== */

    function addBotMessage(message) {

        const messages =
            get("chatMessages");

        if (!messages) {
            return;
        }


        const wrapper =
            document.createElement("div");

        wrapper.className =
            "bot-message";


        const avatar =
            document.createElement("div");

        avatar.className =
            "message-avatar";

        avatar.innerHTML =
            '<i class="fa-solid fa-robot"></i>';


        const content =
            document.createElement("div");

        content.className =
            "message-content";


        const bubble =
            document.createElement("div");

        bubble.className =
            "bot";


        /*
         * textContent is used for safety.
         * AI response cannot inject HTML.
         */

        bubble.textContent =
            message;


        content.appendChild(bubble);

        wrapper.appendChild(avatar);

        wrapper.appendChild(content);

        messages.appendChild(wrapper);


        scrollChat();

    }


    /* =====================================================
       SEND QUESTION TO FLASK
    ===================================================== */

    async function askAI(question) {

        question =
            String(question || "").trim();


        if (!question) {
            return;
        }


        addUserMessage(question);

        showTyping();


        try {

            console.log(
                "Sending question:",
                question
            );


            const response =
                await fetch(
                    chatbotUrl,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"
                        },

                        body: JSON.stringify({

                            message:
                                question,

                            question:
                                question,

                            role:
                                config.role ||
                                "farmer",

                            language:
                                config.language ||
                                "en",

                            user_name:
                                config.userName ||
                                "Farmer"

                        })
                    }
                );


            console.log(
                "Chatbot HTTP status:",
                response.status
            );


            let data = {};

            try {

                data =
                    await response.json();

            } catch (error) {

                console.error(
                    "Invalid JSON response:",
                    error
                );

            }


            hideTyping();


            /* =============================================
               SERVER ERROR
            ============================================= */

            if (!response.ok) {

                console.error(
                    "Chatbot server error:",
                    data
                );


                addBotMessage(
                    data.error ||
                    data.message ||
                    "Sorry, something went wrong. Please try again."
                );


                return;

            }


            /* =============================================
               GET AI ANSWER
            ============================================= */

            const answer =
                data.reply ||
                data.response ||
                data.answer ||
                data.message;


            if (answer) {

                addBotMessage(
                    String(answer)
                );

            } else {

                addBotMessage(
                    "I received your question, but I could not generate an answer."
                );

            }


        } catch (error) {

            hideTyping();


            console.error(
                "Chatbot connection error:",
                error
            );


            addBotMessage(
                "Unable to connect to the AI assistant. Please check your internet connection or try again."
            );

        }

    }


    /* =====================================================
       SEND BUTTON
    ===================================================== */

    function sendMessage() {

        const input =
            get("chatMessageInput");

        if (!input) {

            console.error(
                "chatMessageInput not found"
            );

            return;

        }


        const question =
            input.value.trim();


        if (!question) {

            input.focus();

            return;

        }


        input.value = "";


        askAI(question);

    }


    /* =====================================================
       CLEAR CHAT
    ===================================================== */

    function clearChat() {

        const messages =
            get("chatMessages");

        if (!messages) {
            return;
        }


        messages.innerHTML = "";


        addBotMessage(
            "Hello! 👋 How can I help you today?"
        );

    }


    /* =====================================================
       SUGGESTION BUTTONS
    ===================================================== */

    function handleSuggestion(button) {

        const question =
            button.getAttribute(
                "data-question"
            );


        if (!question) {
            return;
        }


        openChat();


        const input =
            get("chatMessageInput");


        if (input) {

            input.value =
                question;

        }


        askAI(question);

    }


    /* =====================================================
       CLICK EVENTS
    ===================================================== */

    document.addEventListener(
        "click",
        function (event) {


            /* Robot button */

            const chatbotButton =
                event.target.closest(
                    "#chatbotButton"
                );


            if (chatbotButton) {

                event.preventDefault();

                toggleChat();

                return;

            }


            /* Close button */

            const closeButton =
                event.target.closest(
                    "#closeChatButton"
                );


            if (closeButton) {

                event.preventDefault();

                closeChat();

                return;

            }


            /* Send button */

            const sendButton =
                event.target.closest(
                    "#sendChatButton"
                );


            if (sendButton) {

                event.preventDefault();

                sendMessage();

                return;

            }


            /* Clear button */

            const clearButton =
                event.target.closest(
                    "#clearChatButton"
                );


            if (clearButton) {

                event.preventDefault();

                clearChat();

                return;

            }


            /* Suggestions */

            const suggestion =
                event.target.closest(
                    ".suggestion-btn, .ai-feature-btn"
                );


            if (suggestion) {

                event.preventDefault();

                handleSuggestion(
                    suggestion
                );

            }

        }
    );


    /* =====================================================
       ENTER KEY
    ===================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.target &&
                event.target.id ===
                "chatMessageInput"
            ) {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    sendMessage();

                }

            }


            /* ESC = close */

            if (
                event.key === "Escape"
            ) {

                closeChat();

            }

        }
    );


    /* =====================================================
       GLOBAL FUNCTIONS
    ===================================================== */

    window.openKisanChat =
        openChat;

    window.closeKisanChat =
        closeChat;

    window.toggleKisanChat =
        toggleChat;

    window.sendKisanChatMessage =
        sendMessage;

    window.askKisanAI =
        askAI;


    /* =====================================================
       INITIALIZATION
    ===================================================== */

    function initializeChatbot() {

        const button =
            get("chatbotButton");

        const box =
            get("chatBox");

        const input =
            get("chatMessageInput");


        if (button) {

            button.setAttribute(
                "aria-expanded",
                "false"
            );

            console.log(
                "Chatbot button found"
            );

        } else {

            console.error(
                "Chatbot button NOT found: #chatbotButton"
            );

        }


        if (box) {

            box.classList.remove("open");
            box.classList.remove("active");

            box.setAttribute(
                "aria-hidden",
                "true"
            );

        } else {

            console.error(
                "Chatbox NOT found: #chatBox"
            );

        }


        if (input) {

            input.setAttribute(
                "autocomplete",
                "off"
            );

        }


        console.log(
            "KisanVision360+ chatbot initialized"
        );


        console.log(
            "Chatbot API:",
            chatbotUrl
        );

    }


    /* =====================================================
       START
    ===================================================== */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initializeChatbot
        );

    } else {

        initializeChatbot();

    }

})();