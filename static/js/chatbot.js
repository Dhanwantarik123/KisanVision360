// =========================================================
// KisanVision360 AI CHATBOT
// =========================================================


// =========================================================
// TOGGLE CHAT
// =========================================================

function toggleChat() {

    const chatBox = document.getElementById("chatBox");

    if (chatBox) {
        chatBox.classList.toggle("active");
    }

}


// =========================================================
// QUICK QUESTION
// =========================================================

function quickQuestion(question) {

    const input = document.getElementById("message");

    if (!input) {
        return;
    }

    input.value = question;

    sendMessage();

}


// =========================================================
// ADD USER MESSAGE
// =========================================================

function addUserMessage(message) {

    const chatBody = document.getElementById("chat-box");

    if (!chatBody) {
        return;
    }

    const div = document.createElement("div");

    div.className = "user-message";

    div.innerHTML = `
        <div class="message-content">
            ${escapeHTML(message)}
        </div>
    `;

    chatBody.appendChild(div);

    chatBody.scrollTop = chatBody.scrollHeight;

}


// =========================================================
// ADD BOT MESSAGE
// =========================================================

function addBotMessage(message) {

    const chatBody = document.getElementById("chat-box");

    if (!chatBody) {
        return;
    }

    const div = document.createElement("div");

    div.className = "bot-reply";

    div.innerHTML = `
        <div class="message-avatar">
            🤖
        </div>

        <div class="message-content">
            <div class="bot">
                ${formatBotMessage(message)}
            </div>
        </div>
    `;

    chatBody.appendChild(div);

    chatBody.scrollTop = chatBody.scrollHeight;

}


// =========================================================
// SEND MESSAGE
// =========================================================

async function sendMessage() {

    const input = document.getElementById("message");

    const chatBody = document.getElementById("chat-box");

    const typingIndicator =
        document.getElementById("typingIndicator");


    if (!input || !chatBody) {

        console.error(
            "❌ Chatbot HTML elements not found."
        );

        return;

    }


    const message = input.value.trim();


    if (!message) {
        return;
    }


    // -----------------------------------------
    // SHOW USER MESSAGE
    // -----------------------------------------

    addUserMessage(message);

    input.value = "";


    // -----------------------------------------
    // SHOW TYPING
    // -----------------------------------------

    if (typingIndicator) {

        typingIndicator.style.display = "block";

    }


    try {

        // -----------------------------------------
        // SEND TO FLASK
        // -----------------------------------------

        const response = await fetch(
            "/ask_chatbot",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })
            }
        );


        // -----------------------------------------
        // CHECK HTTP STATUS
        // -----------------------------------------

        if (!response.ok) {

            throw new Error(
                "Server returned HTTP " +
                response.status
            );

        }


        const data = await response.json();


        // -----------------------------------------
        // HIDE TYPING
        // -----------------------------------------

        if (typingIndicator) {

            typingIndicator.style.display = "none";

        }


        // -----------------------------------------
        // BOT RESPONSE
        // -----------------------------------------

        if (data.reply) {

            addBotMessage(data.reply);

        }

        else {

            addBotMessage(
                "🤖 Sorry, I could not generate an answer."
            );

        }


    }

    catch (error) {

        console.error(
            "❌ CHATBOT ERROR:",
            error
        );


        // Hide typing

        if (typingIndicator) {

            typingIndicator.style.display = "none";

        }


        addBotMessage(
            "⚠️ Unable to connect to KisanVision360 AI. Please try again."
        );

    }

}


// =========================================================
// ENTER KEY
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const input =
            document.getElementById("message");


        if (!input) {

            console.error(
                "❌ Chat input #message not found."
            );

            return;

        }


        input.addEventListener(
            "keydown",
            function (event) {

                if (event.key === "Enter") {

                    event.preventDefault();

                    sendMessage();

                }

            }
        );

    }
);


// =========================================================
// FORMAT BOT MESSAGE
// =========================================================

function formatBotMessage(message) {

    if (!message) {
        return "";
    }


    let text = String(message);


    // First escape HTML

    text = escapeHTML(text);


    // Convert **text** to bold

    text = text.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    // Convert line breaks

    text = text.replace(
        /\n/g,
        "<br>"
    );


    return text;

}


// =========================================================
// SECURITY
// =========================================================

function escapeHTML(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;

}