import { AuthAPI } from "../assets/api.js";
import { getFileUrl } from "../assets/utils.js";
import { initChatWidget } from "../assets/chat.js?v=3";

export function renderHeader({ showBack = false } = {}) {
  const header = document.querySelector("[data-header]");
  if (!header) return;

  header.innerHTML = `
    <div class="header">
      <div class="header-inner">
        ${showBack ? `<button class="back-btn" id="backBtn" aria-label="back">&lt;</button>` : ""}
        <div class="header-title" id="headerTitle" style="cursor:pointer; font-family: 'Helvetica Neue', sans-serif;">OOTD</div>
        <div class="avatar-wrap" id="avatarWrap" style="display:none;">
          <div class="avatar" id="avatarBtn" aria-label="menu"></div>
          <div class="dropdown" id="dropdown">
            <button id="goProfile">회원정보수정</button>
            <button id="goPassword">비밀번호수정</button>
            <button id="doLogout">로그아웃</button>
          </div>
        </div>
      </div>
    </div>
  `;

  if (showBack) {
    document.getElementById("backBtn")?.addEventListener("click", () => history.back());
  }

  document.getElementById("headerTitle")?.addEventListener("click", () => {
    location.href = "./posts.html";
  });

  const avatarWrap = document.getElementById("avatarWrap");
  const avatarBtn = document.getElementById("avatarBtn");
  const dropdown = document.getElementById("dropdown");

  document.addEventListener("click", (e) => {
    if (!dropdown) return;
    const inside = avatarWrap?.contains(e.target);
    if (!inside) dropdown.classList.remove("open");
  });

  AuthAPI.me()
    .then((res) => {
      const me = res?.data;
      if (!me) return;
      avatarWrap.style.display = "flex";

      if (me.profileImageUrl) {
        avatarBtn.innerHTML = `<img alt="profile" src="${getFileUrl(me.profileImageUrl)}">`;
      } else {
        avatarBtn.innerHTML = "";
      }

      avatarBtn.addEventListener("click", () => dropdown.classList.toggle("open"));

      document.getElementById("goProfile").addEventListener("click", () => {
        location.href = "./profile.html";
      });
      document.getElementById("goPassword").addEventListener("click", () => {
        location.href = "./edit-password.html";
      });
      document.getElementById("doLogout").addEventListener("click", async () => {
        try {
          await AuthAPI.logout();
        } catch (_) { }
        location.href = "./login.html";
      });

      // Show Chat Widget
      initChatWidget();
    })
    .catch(() => { });
}
