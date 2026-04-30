import { renderHeader } from "../components/header.js";
import { PostsAPI, UsersAPI, AuthAPI } from "../assets/api.js";
import { formatDate, formatCount, getFileUrl } from "../assets/utils.js";

renderHeader({ showBack: false });

// 로그인 유저 확인(안되어 있으면 로그인으로)
try {
  await AuthAPI.me();
} catch (_) {
  location.href = "./login.html";
}

const cardsEl = document.getElementById("cards");
const goMake = document.getElementById("goMake");
goMake.addEventListener("click", () => (location.href = "./make-post.html"));

let offset = 0;
const limit = 10;
let loading = false;
let done = false;

// --- caches (무한스크롤에서 중복 요청 방지) ---
const authorCache = new Map();        // userId -> user
const commentCountCache = new Map();  // postId -> number

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// 상세에서 좋아요 누른 뒤 목록에 바로 반영되게(있으면 사용)
function getCachedLikeCount(postId) {
  const v = Number(localStorage.getItem(`likeCount:${postId}`));
  return Number.isFinite(v) ? v : null;
}

async function getAuthor(userId) {
  if (authorCache.has(userId)) return authorCache.get(userId);

  try {
    const u = await UsersAPI.getUser(userId);
    const data = u?.data ?? null;
    authorCache.set(userId, data);
    return data;
  } catch (_) {
    authorCache.set(userId, null);
    return null;
  }
}

// ✅ 핵심: 목록에서도 댓글 수 보이게 (댓글 리스트 조회 후 length)
async function getCommentCount(postId) {
  if (commentCountCache.has(postId)) return commentCountCache.get(postId);

  try {
    const res = await PostsAPI.listComments(postId);
    const items = res?.data?.items;
    const count = Array.isArray(items) ? items.length : 0;
    commentCountCache.set(postId, count);
    return count;
  } catch (e) {
    commentCountCache.set(postId, 0);
    return 0;
  }
}

async function renderPosts() {
  if (loading || done) return;
  loading = true;

  try {
    const res = await PostsAPI.list({ offset, limit });
    const items = res?.data?.items || [];

    if (offset === 0 && items.length === 0) {
      cardsEl.innerHTML = `
        <div style="text-align:center; color:#6B7280; padding:24px 0;">
          게시글이 없습니다. 첫 게시글을 작성해보세요.
        </div>`;
      done = true;
      return;
    }

    if (items.length < limit) done = true;

    // ✅ 작성자 + 댓글 수를 병렬로 미리 가져오기 (렌더링 중 await로 끊기지 않게)
    const [authors, commentCounts] = await Promise.all([
      Promise.all(items.map((p) => getAuthor(p.authorUserId))),
      Promise.all(items.map((p) => getCommentCount(p.postId))),
    ]);

    items.forEach((p, idx) => {
      const author = authors[idx];
      const commentCount = commentCounts[idx] ?? 0;

      // 좋아요는 캐시가 있으면 우선 적용
      const cachedLike = getCachedLikeCount(p.postId);
      const likeToShow = cachedLike !== null ? cachedLike : p.likeCount;

      const div = document.createElement("div");
      div.className = "card";
      div.innerHTML = `
        <div class="card-title">${escapeHtml(p.title)}</div>
        <div class="card-meta">
          <div class="card-stats">
            <span>Like ${formatCount(likeToShow)}</span>
            <span>Comment ${formatCount(commentCount)}</span>
            <span>View ${formatCount(p.hits)}</span>
          </div>
          <div>${formatDate(p.createdAt)}</div>
        </div>
        <div class="card-author">
          <div class="mini-avatar">
            ${author?.profileImageUrl ? `<img alt="a" src="${getFileUrl(author.profileImageUrl)}">` : ""}
          </div>
          <div class="name">${author?.nickname || `user#${p.authorUserId}`}</div>
        </div>
      `;

      div.addEventListener("click", () => {
        location.href = `./post.html?postId=${p.postId}`;
      });

      cardsEl.appendChild(div);
    });

    offset += items.length;
  } finally {
    loading = false;
  }
}

// infinite scroll
const sentinel = document.getElementById("sentinel");
const io = new IntersectionObserver(async (entries) => {
  if (entries.some((e) => e.isIntersecting)) {
    await renderPosts();
  }
});
io.observe(sentinel);

// initial
await renderPosts();

