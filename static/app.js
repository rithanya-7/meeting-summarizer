const fileInput = document.getElementById("audioFile");
const fileName = document.getElementById("fileName");
const dropZone = document.getElementById("dropZone");
const summarizeButton = document.getElementById("summarizeButton");
const statusText = document.getElementById("status");

fileInput.addEventListener("change", () => updateSelectedFile(fileInput.files[0]));

["dragenter", "dragover"].forEach(name => dropZone.addEventListener(name, e => {
    e.preventDefault();
    dropZone.classList.add("dragging");
}));

["dragleave", "drop"].forEach(name => dropZone.addEventListener(name, e => {
    e.preventDefault();
    dropZone.classList.remove("dragging");
}));

dropZone.addEventListener("drop", e => {
    const file = e.dataTransfer.files[0];
    if (!file) return;
    fileInput.files = e.dataTransfer.files;
    updateSelectedFile(file);
});

function updateSelectedFile(file) {
    fileName.textContent = file ? file.name : "No file selected";
}

summarizeButton.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) {
        statusText.textContent = "Please choose a meeting recording first.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    summarizeButton.disabled = true;
    summarizeButton.innerHTML = "<span>◌</span> Processing...";
    statusText.textContent = "Transcribing the recording and preparing meeting notes...";

    try {
        const response = await fetch("/meetings", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Something went wrong.");

        showMeeting(data);
        await loadHistory();
        statusText.textContent = "Done — your meeting notes are ready.";
        document.getElementById("summary-card").scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (error) {
        statusText.textContent = error.message;
    } finally {
        summarizeButton.disabled = false;
        summarizeButton.innerHTML = "<span>✧</span> Summarize Meeting";
    }
});

function showMeeting(data) {
    setText("summary", data.summary, "Your meeting summary will appear here.");
    renderList("decisions", data.decisions, "Decisions will appear here.");
    renderActions(data.action_items);
    renderList("questions", data.open_questions, "Open questions will appear here.");
    document.getElementById("transcript").textContent = data.transcript || "No transcript was generated.";
}

function setText(id, value, fallback) {
    const el = document.getElementById(id);
    el.innerHTML = "";
    if (!value) {
        const span = document.createElement("span");
        span.className = "placeholder";
        span.textContent = fallback;
        el.appendChild(span);
    } else el.textContent = value;
}

function renderList(id, items, fallback) {
    const el = document.getElementById(id);
    el.innerHTML = "";
    if (!items || !items.length) {
        const span = document.createElement("span");
        span.className = "placeholder";
        span.textContent = fallback;
        el.appendChild(span);
        return;
    }
    const ul = document.createElement("ul");
    ul.className = "clean-list";
    items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = typeof item === "string" ? item : JSON.stringify(item);
        ul.appendChild(li);
    });
    el.appendChild(ul);
}

function renderActions(items) {
    const el = document.getElementById("actions");
    el.innerHTML = "";
    if (!items || !items.length) {
        const span = document.createElement("span");
        span.className = "placeholder";
        span.textContent = "No action items were identified.";
        el.appendChild(span);
        return;
    }
    items.forEach(item => {
        const div = document.createElement("div");
        div.className = "action";
        const strong = document.createElement("strong");
        strong.textContent = item.task || "Task not specified";
        const meta = document.createElement("div");
        meta.className = "action-meta";
        meta.textContent = `Owner: ${item.owner || "Not specified"}  •  Due: ${item.due_date || "Not specified"}`;
        div.appendChild(strong);
        div.appendChild(meta);
        el.appendChild(div);
    });
}

async function loadHistory() {
    const el = document.getElementById("history");
    try {
        const response = await fetch("/meetings");
        const meetings = await response.json();
        el.innerHTML = "";
        if (!meetings.length) {
            el.innerHTML = '<div class="empty-history">No previous meetings yet.</div>';
            return;
        }
        meetings.forEach(meeting => {
            const item = document.createElement("div");
            item.className = "history-item";
            const icon = document.createElement("div");
            icon.className = "history-file-icon";
            icon.textContent = "▤";
            const info = document.createElement("div");
            info.className = "history-info";
            const name = document.createElement("span");
            name.className = "history-name";
            name.textContent = meeting.filename;
            const date = document.createElement("span");
            date.className = "history-date";
            date.textContent = `Meeting #${meeting.id}`;
            info.append(name, date);
            const button = document.createElement("button");
            button.className = "open-button";
            button.textContent = "›";
            button.title = "Open meeting";
            button.onclick = () => openMeeting(meeting.id);
            item.append(icon, info, button);
            el.appendChild(item);
        });
    } catch {
        el.innerHTML = '<div class="empty-history">Could not load meeting history.</div>';
    }
}

async function openMeeting(id) {
    const response = await fetch(`/meetings/${id}`);
    const data = await response.json();
    if (!response.ok) {
        statusText.textContent = data.detail || "Meeting could not be loaded.";
        return;
    }
    showMeeting(data);
    statusText.textContent = `Loaded ${data.filename}`;
}

document.querySelectorAll(".nav-item").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        const target = document.getElementById(button.dataset.scroll);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
});

document.getElementById("viewAllButton").onclick = () => document.getElementById("history-section").scrollIntoView({ behavior: "smooth" });

loadHistory();
