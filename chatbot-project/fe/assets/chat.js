import { API_BASE } from "./config.js";
import { ChatAPI, AuthAPI } from "./api.js";
import { formatDate, getFileUrl } from "./utils.js";

// Global state
let currentUser = null;
let currentConversationId = null;
let currentOtherUserId = null;
let ws = null;
let globalUnreadCount = 0;

// Initialize Widget
export async function initChatWidget() {
    try {
        const res = await AuthAPI.me();
        currentUser = res.data;
    } catch (e) {
        // Not logged in, don't show chat
        return;
    }

    injectChatHTML();
    loadStyles();
    bindEvents();

    // Connect WS automatically so we can receive notifications in background
    connectWebSocket();

    // Fetch initial unread count
    try {
        const res = await ChatAPI.getConversations();
        const convs = res.data;
        globalUnreadCount = convs.reduce((sum, c) => sum + (c.unread_count || 0), 0);

        if (globalUnreadCount > 0) {
            const badge = document.getElementById("chat-unread-badge");
            if (badge) {
                badge.innerText = globalUnreadCount > 99 ? "99+" : globalUnreadCount;
                badge.style.display = "flex";
            }
        }
    } catch (e) { /* ignore */ }
}

function loadStyles() {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/assets/chat.css?v=2";
    document.head.appendChild(link);
}

function injectChatHTML() {
    const html = `
    <div id="chat-widget-container">
        <button id="chat-widget-btn">
            💬
            <div id="chat-unread-badge"></div>
        </button>
        <div id="chat-window">
            <div id="chat-sidebar">
                <div class="chat-header" style="justify-content: center;">대화 목록</div>
                <div id="chat-list-view"></div>
            </div>
            <div id="chat-main">
                <div class="chat-header">
                    <div style="display:flex; align-items:center;">
                        <div id="chat-header-avatar" class="chat-avatar chat-header-avatar" style="display:none;"></div>
                        <span id="chat-header-title">메시지</span>
                    </div>
                    <div class="chat-header-actions">
                        <button id="chat-close-btn">✖</button>
                    </div>
                </div>
                <div id="chat-empty-state">대화 상대를 선택해주세요.</div>
                <div id="chat-message-view" style="display:none;">
                    <div id="chat-messages-container"></div>
                    <div class="chat-input-area">
                        <input type="text" id="chat-input-field" placeholder="메시지 입력..." />
                        <button id="chat-send-btn">➤</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
    const div = document.createElement("div");
    div.innerHTML = html;
    document.body.appendChild(div.firstElementChild);
}

function bindEvents() {
    const btn = document.getElementById("chat-widget-btn");
    const windowEl = document.getElementById("chat-window");
    const closeBtn = document.getElementById("chat-close-btn");
    const sendBtn = document.getElementById("chat-send-btn");
    const inputField = document.getElementById("chat-input-field");

    btn.addEventListener("click", async () => {
        windowEl.style.display = "flex";
        btn.style.display = "none";
        // Hide badge when opening
        globalUnreadCount = 0;
        document.getElementById("chat-unread-badge").style.display = "none";

        await showChatList();
        connectWebSocket();
    });

    closeBtn.addEventListener("click", () => {
        windowEl.style.display = "none";
        btn.style.display = "flex";
        if (ws) {
            ws.close();
            ws = null;
        }
    });

    sendBtn.addEventListener("click", sendMessage);
    inputField.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
}

function getWebSocketUrl() {
    let base = API_BASE;
    if (!base) {
        // relative to current host
        base = window.location.origin;
    }
    return base.replace(/^http/, "ws") + "/v1/chat/ws";
}

function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    ws = new WebSocket(getWebSocketUrl());

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.error) {
            console.error(msg.error);
            return;
        }

        // If currently in this conversation, append message
        if (currentConversationId === msg.conversation_id && document.getElementById("chat-window").style.display === "flex") {
            appendMessage(msg);
            scrollToBottom();
        } else {
            // Otherwise
            const windowEl = document.getElementById("chat-window");
            if (windowEl.style.display !== "flex") {
                // Widget is closed -> Show global unread badge
                globalUnreadCount++;
                const badge = document.getElementById("chat-unread-badge");
                if (badge) {
                    badge.innerText = globalUnreadCount > 99 ? "99+" : globalUnreadCount;
                    badge.style.display = "flex";
                }
            } else if (document.getElementById("chat-list-view").style.display !== "none") {
                // Refresh list if looking at it
                showChatList();
            }
        }
    };

    ws.onclose = () => {
        // attempt reconnect if window is still open
        const windowEl = document.getElementById("chat-window");
        if (windowEl && windowEl.style.display === "flex") {
            setTimeout(connectWebSocket, 3000);
        }
    };
}

async function showChatList() {
    const listEl = document.getElementById("chat-list-view");

    listEl.innerHTML = '<div style="padding:20px; text-align:center; color:#6b7280;">로딩중...</div>';

    try {
        const res = await ChatAPI.getConversations();
        const convs = res.data;

        // Calculate total initial unread count correctly to show it on load if widget isn't open yet
        // However, the widget is open if we are here, so we clear the global badge.
        globalUnreadCount = 0;
        const badge = document.getElementById("chat-unread-badge");
        if (badge) badge.style.display = "none";

        listEl.innerHTML = "";
        if (convs.length === 0) {
            listEl.innerHTML = '<div style="padding:20px; text-align:center; color:#6b7280;">진행중인 대화가 없습니다.</div>';
            return;
        }

        convs.forEach(c => {
            const item = document.createElement("div");
            item.className = "chat-list-item" + (c.id === currentConversationId ? " active" : "");

            const avatarHtml = c.other_user_profile
                ? `<img src="${getFileUrl(c.other_user_profile)}" />`
                : "";

            let unreadBadge = '';
            if (c.unread_count > 0 && c.id !== currentConversationId) {
                unreadBadge = `<span style="background-color:red; color:white; border-radius:10px; padding:2px 8px; font-size:12px; margin-left:10px;">${c.unread_count}</span>`;
            }

            item.innerHTML = `
                <div class="chat-avatar chat-list-avatar">${avatarHtml}</div>
                <div class="chat-list-info">
                    <div class="chat-list-name">${c.other_user_nickname} ${unreadBadge}</div>
                    <div class="chat-list-preview">${c.last_message || '대화가 없습니다.'}</div>
                </div>
            `;

            item.addEventListener("click", () => openConversation(c.id, c.other_user_nickname, c.other_user_id, c.other_user_profile));
            listEl.appendChild(item);
        });
    } catch (e) {
        listEl.innerHTML = '<div style="padding:20px; text-align:center; color:red;">목록을 불러올 수 없습니다.</div>';
    }
}

async function openConversation(convId, otherName, otherUserId, otherAvatar) {
    currentConversationId = convId;
    currentOtherUserId = otherUserId;

    const msgEl = document.getElementById("chat-message-view");
    const emptyState = document.getElementById("chat-empty-state");
    const title = document.getElementById("chat-header-title");
    const avatar = document.getElementById("chat-header-avatar");
    const msgsContainer = document.getElementById("chat-messages-container");

    emptyState.style.display = "none";
    msgEl.style.display = "flex";
    title.innerText = otherName;

    if (avatar) {
        if (otherAvatar) {
            avatar.innerHTML = `<img src="${getFileUrl(otherAvatar)}" />`;
        } else {
            avatar.innerHTML = "";
        }
        avatar.style.display = "flex";
    }

    // Refresh list to highlight the selected active tab
    showChatList();

    msgsContainer.innerHTML = '<div style="padding:20px; text-align:center; color:#6b7280;">로딩중...</div>';

    try {
        const res = await ChatAPI.getMessages(convId);
        const msgs = res.data;

        msgsContainer.innerHTML = "";
        msgs.forEach(m => appendMessage(m));
        scrollToBottom();
    } catch (e) {
        msgsContainer.innerHTML = '<div style="padding:20px; text-align:center; color:red;">메시지를 불러올 수 없습니다.</div>';
    }
}

function appendMessage(msg) {
    const container = document.getElementById("chat-messages-container");
    const isMine = msg.sender_id === currentUser.userId;

    const div = document.createElement("div");
    div.className = "message-bubble " + (isMine ? "message-sent" : "message-received");

    // Convert newlines to br 
    const textHtml = msg.content.replace(/\\n/g, "<br/>");
    div.innerHTML = textHtml;

    container.appendChild(div);
}

function scrollToBottom() {
    const container = document.getElementById("chat-messages-container");
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

async function sendMessage() {
    const input = document.getElementById("chat-input-field");
    const content = input.value.trim();
    if (!content || !currentConversationId) return;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            conversation_id: currentConversationId,
            content: content
        }));
        input.value = "";
    } else {
        alert("연결이 끊어졌습니다. 다시 시도해주세요.");
    }
}

// Global helper to start DM from other pages
window.startDirectMessage = async function (otherUserId) {
    if (otherUserId === currentUser?.userId) {
        alert("자신에게는 메시지를 보낼 수 없습니다.");
        return;
    }

    try {
        // Get or Create conversation
        const res = await ChatAPI.createConversation(otherUserId);
        const convId = res.data.conversation_id;

        // Open Chat Widget
        document.getElementById("chat-window").style.display = "flex";
        document.getElementById("chat-widget-btn").style.display = "none";

        // Connect WS
        connectWebSocket();

        // Open the specific conversation
        // We need the other user's name, ideally we should fetch it or get from API
        // For now, let's just show '대화방' and open it.
        await openConversation(convId, "대화방", otherUserId, null);
    } catch (e) {
        alert("대화를 시작할 수 없습니다.");
    }
}
