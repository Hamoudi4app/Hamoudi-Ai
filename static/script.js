const chatContainer = document.getElementById("chat-container");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

function addMessage(text, sender = "ai") {
    const row = document.createElement("div");
    row.classList.add("message-row", sender);

    const bubble = document.createElement("div");
    bubble.classList.add("message-bubble");
    bubble.textContent = text;

    row.appendChild(bubble);
    chatContainer.appendChild(row);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function sendMessage(event) {
    event.preventDefault();

    const text = userInput.value.trim();
    if (!text) return;

    // رسالة المستخدم
    addMessage(text, "user");
    userInput.value = "";
    userInput.focus();

    // رسالة انتظار من Hamoudi AI
    const loadingText = "… جاري التفكير";
    const loadingId = Date.now().toString();
    addMessage(loadingText, "ai");
    const loadingBubble = chatContainer.lastChild.querySelector(".message-bubble");

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();

        // تحديث رسالة الـ AI
        loadingBubble.textContent = data.reply || "ماقدرتش أفهم الرد.";
    } catch (error) {
        console.error(error);
        loadingBubble.textContent = "حصل خطأ أثناء الاتصال بـ Hamoudi AI.";
    }
}

chatForm.addEventListener("submit", sendMessage);