import { renderHeader } from "../components/header.js";
import { PostsAPI, UsersAPI, AuthAPI } from "../assets/api.js";
import { formatDate, formatCount, setEnabled, getFileUrl } from "../assets/utils.js";
import { confirmModal } from "../components/modal.js";

renderHeader({ showBack: true });

const params = new URLSearchParams(location.search);
const postId = Number(params.get("postId"));

if (!postId) location.href = "./posts.html";

let me = null;
try {
  me = (await AuthAPI.me())?.data;
} catch (_) {
  location.href = "./login.html";
}

const titleEl = document.getElementById("postTitle");
const contentEl = document.getElementById("postContent");
const authorNickEl = document.getElementById("authorNick");
const authorAvatarEl = document.getElementById("authorAvatar");
const dateEl = document.getElementById("postDate");
const imgWrap = document.getElementById("postImageWrap");
const imgEl = document.getElementById("postImage");

const ownerActions = document.getElementById("ownerActions");
const editBtn = document.getElementById("editPostBtn");
const deleteBtn = document.getElementById("deletePostBtn");

const sendDmBtn = document.getElementById("sendDmBtn");

const likeBtn = document.getElementById("likeBtn");      // ✅ 추가
const likeCountEl = document.getElementById("likeCount");
const hitCountEl = document.getElementById("hitCount");
const commentCountEl = document.getElementById("commentCount");

const commentInput = document.getElementById("commentInput");
const commentSubmit = document.getElementById("commentSubmit");
const commentsEl = document.getElementById("comments");

let post = null;
let author = null;
let editingCommentId = null;

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function canSubmitComment() {
  const ok = commentInput.value.trim().length > 0;
  setEnabled(commentSubmit, ok);
}

commentInput.addEventListener("input", canSubmitComment);

// ✅ 좋아요 상태/카운트 캐시(목록 반영용)
function likeKey() {
  return `liked:${me.userId}:${postId}`;
}
function likeCountKey() {
  return `likeCount:${postId}`;
}
function isLiked() {
  return localStorage.getItem(likeKey()) === "1";
}
function setLiked(v) {
  localStorage.setItem(likeKey(), v ? "1" : "0");
}
function setCachedLikeCount(cnt) {
  localStorage.setItem(likeCountKey(), String(cnt));
}
function applyLikeStyle() {
  // 피그마 스펙: disable(D9D9D9) ↔ enable(ACA0EB)
  if (!likeBtn) return;
  likeBtn.style.background = isLiked() ? "#ACA0EB" : "#D9D9D9";
  likeBtn.style.cursor = "pointer";
}

async function load() {
  const res = await PostsAPI.get(postId);
  post = res?.data;

  const u = await UsersAPI.getUser(post.authorUserId);
  author = u?.data;

  titleEl.textContent = post.title;
  contentEl.textContent = post.content;
  authorNickEl.textContent = author?.nickname || `user#${post.authorUserId}`;
  dateEl.textContent = formatDate(post.createdAt);

  if (author?.profileImageUrl) {
    authorAvatarEl.innerHTML = `<img alt="a" src="${getFileUrl(author.profileImageUrl)}">`;
  }

  if (post.fileUrl) {
    imgWrap.style.display = "block";
    imgEl.src = getFileUrl(post.fileUrl);
  }

  likeCountEl.textContent = formatCount(post.likeCount);
  hitCountEl.textContent = formatCount(post.hits);

  // ✅ 목록 반영용 캐시 저장 + 색상 반영
  setCachedLikeCount(post.likeCount);
  applyLikeStyle();

  if (me?.userId === post.authorUserId) {
    ownerActions.style.display = "flex";
  } else if (me) {
    // Show DM button if not author and logged in
    sendDmBtn.style.display = "block";
    sendDmBtn.onclick = () => {
      if (window.startDirectMessage) {
        window.startDirectMessage(post.authorUserId);
      }
    };
  }

  await loadComments();
}

async function loadComments() {
  const res = await PostsAPI.listComments(postId);
  const items = res?.data?.items || [];
  commentCountEl.textContent = formatCount(items.length);

  commentsEl.innerHTML = "";
  for (const c of items) {
    let cu = null;
    try {
      cu = (await UsersAPI.getUser(c.authorUserId))?.data;
    } catch (_) { }

    const item = document.createElement("div");
    item.className = "comment-item";
    item.innerHTML = `
      <div class="comment-left">
        <div class="mini-avatar">${cu?.profileImageUrl ? `<img alt="p" src="${getFileUrl(cu.profileImageUrl)}">` : ""}</div>
        <div class="comment-body">
          <div class="top">
            <div class="nick">${cu?.nickname || `user#${c.authorUserId}`}</div>
            <div class="date">${formatDate(c.createdAt)}</div>
          </div>
          <div class="text" data-text>${escapeHtml(c.content)}</div>
        </div>
      </div>
      <div class="comment-actions" data-actions style="display:${c.authorUserId === me.userId ? "flex" : "none"}">
        <button data-edit>수정</button>
        <button data-del>삭제</button>
      </div>
    `;

    if (c.authorUserId === me.userId) {
      item.querySelector("[data-edit]").addEventListener("click", () => {
        editingCommentId = c.commentId;
        commentInput.value = c.content;
        commentSubmit.textContent = "댓글 수정";
        canSubmitComment();
      });

      item.querySelector("[data-del]").addEventListener("click", async () => {
        const ok = await confirmModal({
          title: "댓글을 삭제하시겠습니까?",
          desc: "삭제한 내용은 복구 할 수 없습니다.",
        });
        if (!ok) return;
        await PostsAPI.deleteComment(postId, c.commentId);
        await loadComments();
      });
    }

    commentsEl.appendChild(item);
  }
}

commentSubmit.addEventListener("click", async () => {
  const text = commentInput.value.trim();
  if (!text) return;

  if (!editingCommentId) {
    await PostsAPI.createComment(postId, { content: text });
  } else {
    await PostsAPI.updateComment(postId, editingCommentId, { content: text });
    editingCommentId = null;
    commentSubmit.textContent = "댓글 등록";
  }

  commentInput.value = "";
  canSubmitComment();
  await loadComments();
});

// ✅ 좋아요 토글
if (likeBtn) {
  likeBtn.addEventListener("click", async () => {
    try {
      let res;
      if (!isLiked()) {
        res = await PostsAPI.like(postId);
        setLiked(true);
      } else {
        res = await PostsAPI.unlike(postId);
        setLiked(false);
      }

      const newCnt = res?.data?.likeCount ?? post.likeCount;
      post.likeCount = newCnt;

      likeCountEl.textContent = formatCount(newCnt);
      setCachedLikeCount(newCnt); // ✅ 목록 반영
      applyLikeStyle();           // ✅ 색상 토글
    } catch (e) {
      console.error(e);
    }
  });
}

editBtn.addEventListener("click", () => {
  location.href = `./edit-post.html?postId=${postId}`;
});

deleteBtn.addEventListener("click", async () => {
  const ok = await confirmModal({
    title: "게시글을 삭제하시겠습니까?",
    desc: "삭제한 내용은 복구 할 수 없습니다.",
  });
  if (!ok) return;
  await PostsAPI.remove(postId);
  location.href = "./posts.html";
});

await load();
canSubmitComment();
