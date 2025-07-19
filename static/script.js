const chatHistory = document.getElementById("chatHistory");
const chatControls = document.getElementById("chatControls");
let chatData = [];
let isLearning = false;
let lastUnknownPhrase = "";

function getScrollbarWidth() {
    const scrollDiv = document.createElement("div");
    scrollDiv.style.visibility = "hidden";
    scrollDiv.style.overflow = "scroll";
    scrollDiv.style.position = "absolute";
    scrollDiv.style.top = "-9999px";
    scrollDiv.style.width = "100px";
    scrollDiv.style.height = "100px";

    document.body.appendChild(scrollDiv);
    const scrollbarWidth = scrollDiv.offsetWidth - scrollDiv.clientWidth;
    document.body.removeChild(scrollDiv);

    return scrollbarWidth;
}

function showSettingsDB() {
    document.querySelector(".teach-section").classList.toggle("open");
}

function showModal(id) {
    const modal = document.getElementById(id);
    modal.classList.add("open");
    modal.style.zIndex = "1";
    modal.style.opacity = "1";
    const scrollbarWidth = getScrollbarWidth();
    const hasVerticalScroll = document.documentElement.scrollHeight > window.innerHeight;
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = hasVerticalScroll ? scrollbarWidth + "px" : "";
}

function closeModal(id) {
    const modal = document.getElementById(id);    
    modal.classList.remove("open");
    modal.style.opacity = "0";
    modal.style.zIndex = "-1";
    document.body.style.overflow = "auto";
    document.body.style.paddingRight = "";
    const inputs = modal.querySelectorAll("input");
    inputs.forEach(input => input.value = "");
    const responseDivs = modal.querySelectorAll(".response");
    responseDivs.forEach(div => div.innerText = "");
}

window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        closeModal(event.target.id);
    }
}

function saveHistoryToLocalStorage() {
    localStorage.setItem("chatData", JSON.stringify(chatData));
}

function renderChat() {
    chatHistory.innerHTML = "";

    chatData.forEach(entry => {
        const div = document.createElement("div");
        div.className = `chat-entry ${entry.role}`;
        div.innerHTML = `<div class="chat-bubble">${entry.text}</div>`;
        chatHistory.appendChild(div);
    });

    const hasChat = chatData.length > 0;

    chatHistory.style.display = hasChat ? "block" : "none";

    const clearBtn = document.getElementById("clearHistoryBtn");
    if (clearBtn) {
        clearBtn.style.display = hasChat ? "block" : "none";
    }

    chatHistory.scrollTop = chatHistory.scrollHeight;
}


function loadHistoryFromLocalStorage() {
    const saved = localStorage.getItem("chatData");
    if(saved) {
        chatData = JSON.parse(saved);
        renderChat();
    }
    renderChat(); 
}
window.onload = loadHistoryFromLocalStorage;

async function openKnowledgeModal() {
    const [phrasesRes, synonymsRes] = await Promise.all([
        fetch("/all-phrases"),
        fetch("/all-synonyms")
    ]);

    const phrasesData = await phrasesRes.json();
    const synonymsData = await synonymsRes.json();

    const db = phrasesData.data;
    const syn = synonymsData.data;

    const allData = Object.keys(db).map(phrase => ({
        phrase,
        answers: db[phrase],
        synonyms: syn[phrase] || []
    }));

    const searchInput = document.getElementById("knowledgeSearch");
    const list = document.getElementById("knowledgeList");

    function renderList(filtered) {
        list.innerHTML = "";

        if (filtered.length === 0) {
            list.innerHTML = "<p><i>No matches found.</i></p>";
            return;
        }

        filtered.forEach(item => {
            const answerList = item.answers.map(ans => `– ${ans}`).join("<br>");
            const synonymList = item.synonyms.length ? item.synonyms.map(s => `~ ${s}`).join("<br>") : "<i>no synonyms</i>";
            list.innerHTML += `
                <div style="margin-bottom: 20px;">
                    <b>${item.phrase}</b><br>
                    <u>Answers:</u><br>${answerList}<br>
                    <u>Synonyms:</u><br>${synonymList}
                </div>
            `;
        });
    }

    renderList(allData);

    searchInput.oninput = () => {
        const query = searchInput.value.trim().toLowerCase();
        const filtered = allData.filter(item =>
            item.phrase.includes(query) ||
            item.answers.some(ans => ans.toLowerCase().includes(query)) ||
            item.synonyms.some(s => s.toLowerCase().includes(query))
        );
        renderList(filtered);
    };

    const modal = document.getElementById("knowledgeModal");
    modal.classList.add("open");
    modal.style.zIndex = "1";
    modal.style.opacity = "1";
    const scrollbarWidth = getScrollbarWidth();
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = scrollbarWidth + "px";
}

async function askBot() {
    const input = document.getElementById("messageInput");
    const message = input.value.trim();
    if (!message) return;

    if (isLearning) {
        const teachRes = await fetch("/teach", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ phrase: lastUnknownPhrase, answer: message })
        });
        const data = await teachRes.json();
        chatData.push({ role: "user", text: message });
        chatData.push({ role: "bot", text: "Thanks! I've learned how to answer that." });
        isLearning = false;
        lastUnknownPhrase = "";
        renderChat();
        saveHistoryToLocalStorage();
        input.value = "";
        return;
    }

    const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    });
    const data = await res.json();

    chatData.push({ role: "user", text: message });
    chatData.push({ role: "bot", text: data.response });

    if (data.response && data.response.includes("Please teach me")) {
        isLearning = true;
        lastUnknownPhrase = message;
    }

    renderChat();
    saveHistoryToLocalStorage();
    input.value = "";
}

function clearHistory() {
    chatData = [];
    chatHistory.innerHTML = "";
    chatHistory.style.display = "none";
    localStorage.removeItem("chatData");
    renderChat();
}

async function teachBot() {
    const phrase = document.getElementById("teachPhrase").value;
    const answer = document.getElementById("teachAnswer").value;
    const res = await fetch("/teach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase, answer })
    });
    const data = await res.json();
    document.getElementById("teachResponse").innerText = data.message;
}

async function editBotAnswer() {
    const phrase = document.getElementById("editPhrase").value.trim();
    const oldAnswer = document.getElementById("editOldAnswer").value.trim();
    const newAnswer = document.getElementById("editNewAnswer").value.trim();

    if (!phrase || !oldAnswer || !newAnswer) return;

    const res = await fetch("/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase, old_answer: oldAnswer, new_answer: newAnswer })
    });

    const data = await res.json();
    document.getElementById("editResponse").innerText = data.message;
}

async function deleteFromBot() {
    const phrase = document.getElementById("deletePhrase").value.trim();
    const answer = document.getElementById("deleteAnswer").value.trim();
            
    if(!phrase) return;

    const res = await fetch("/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phrase, answer: answer || null })
    });

    const data = await res.json();
    document.getElementById("deleteResponse").innerText = data.message;
}

async function addSynonym() {
    const main = document.getElementById("mainPhrase").value.trim();
    const synonym = document.getElementById("newSynonym").value.trim();

    if (!main || !synonym) return;

    const res = await fetch("/add-synonym", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ main, synonym }) 
    });

    const data = await res.json();
    document.getElementById("synonymResponse").innerText = data.message;
}

async function editSynonym() {
    const main = document.getElementById("editSynMain").value.trim();
    const old_syn = document.getElementById("editSynOld").value.trim();
    const new_syn = document.getElementById("editSynNew").value.trim();

    if (!main || !old_syn || !new_syn) return;

    const res = await fetch("/edit-synonym", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ main, old_syn, new_syn })
    });

    const data = await res.json();
    document.getElementById("editSynResponse").innerText = data.message;
}

async function deleteSynonym() {
    const main = document.getElementById("deleteSynMain").value.trim();
    const synonym = document.getElementById("deleteSynOne").value.trim();

    if (!main) {
        document.getElementById("deleteSynResponse").innerText = "Please enter the main phrase.";
        return;
    }

    const res = await fetch("/delete-synonym", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ main, synonym })
    })

    const data = await res.json();
    document.getElementById("deleteSynResponce").innerText = data.message;
}