// ================================
// KisanVision360 AI Chatbot
// ================================

// Open / Close Chat
function toggleChat() {

    const chat = document.getElementById("chatBox");

    if (chat.style.display === "flex") {

        chat.style.display = "none";

    } else {

        chat.style.display = "flex";

        document.getElementById("message").focus();

    }

}

// Quick Suggestion Buttons
function quickQuestion(text) {

    document.getElementById("message").value = text;

    sendMessage();

}

// Send Message
function sendMessage() {

    const input = document.getElementById("message");
    const box = document.getElementById("chat-box");

    let message = input.value.trim();

    if (message === "") return;

    // User Message
    box.innerHTML += `
        <div class="user">
            ${message}
        </div>
    `;

    input.value = "";

    // Scroll
    box.scrollTop = box.scrollHeight;

    // Typing Indicator
    const typing = document.createElement("div");
    typing.className = "bot";
    typing.id = "typing";

    typing.innerHTML = `
        🤖 <i>Typing...</i>
    `;

    box.appendChild(typing);

    box.scrollTop = box.scrollHeight;

    fetch("/ask_chatbot", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            message: message
        })

    })

    .then(response => response.json())

    .then(data => {

        document.getElementById("typing").remove();

        box.innerHTML += `
            <div class="bot">
                ${data.reply}
            </div>
        `;

        box.scrollTop = box.scrollHeight;

    })

    .catch(error => {

        const typingBox = document.getElementById("typing");

        if (typingBox) typingBox.remove();

        box.innerHTML += `
            <div class="bot">
                ❌ Unable to connect to AI server.
            </div>
        `;

        console.log(error);

    });

}

// Press Enter
document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("message");

    if (input) {

        input.addEventListener("keypress", function(e) {

            if (e.key === "Enter") {

                e.preventDefault();

                sendMessage();

            }

        });

    }

});

// Auto Welcome Popup (Optional)
window.onload = function() {

    setTimeout(() => {

        const btn = document.querySelector(".chatbot-button");

        if(btn){

            btn.classList.add("bounce");

        }

    },1500);

};