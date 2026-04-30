import { renderHeader } from "../components/header.js";
import { PostsAPI, AuthAPI } from "../assets/api.js";
import { setEnabled, fileToDataUrl, getFileUrl, validatePostForm } from "../assets/utils.js";

renderHeader({ showBack: true });

let me = null;
try {
  me = (await AuthAPI.me())?.data;
} catch (_) {
  location.href = "./login.html";
}

const params = new URLSearchParams(location.search);
const postId = Number(params.get("postId"));
if (!postId) location.href = "./posts.html";

const form = document.getElementById("editForm");
const titleEl = document.getElementById("title");
const contentEl = document.getElementById("content");
const fileEl = document.getElementById("file");
const imagePreviewEl = document.getElementById("imagePreview");
const btn = document.getElementById("submitBtn");

const titleH = document.getElementById("titleHelper");
const contentH = document.getElementById("contentHelper");

let fileUrl = null;

// Initial validation should happen after data load
async function loadPost() {
  const p = (await PostsAPI.get(postId))?.data;
  if (p.authorUserId !== me.userId) {
    location.href = `./post.html?postId=${postId}`;
    return;
  }

  titleEl.value = p.title;
  contentEl.value = p.content;
  fileUrl = p.fileUrl || null;

  renderImagePreview();
  validate();
}

function renderImagePreview() {
  imagePreviewEl.innerHTML = "";
  if (fileUrl) {
    const img = document.createElement("img");
    img.src = fileUrl.startsWith("data:") ? fileUrl : getFileUrl(fileUrl);
    img.alt = "Preview";
    img.style.maxWidth = "100%";
    img.style.marginTop = "10px";
    img.style.borderRadius = "8px";
    imagePreviewEl.appendChild(img);
  }
}

fileEl.addEventListener("change", async () => {
  const f = fileEl.files?.[0];
  if (!f) {
    // If user cancels selection, keep previous fileUrl? Or clear? 
    // Usually file input clear clears the selection. 
    // Let's assume we keep the old one if they didn't pick anything new,
    // BUT standard file input behavior is if you open and cancel, it might clear.
    // However, here let's validat if 'f' exists.
    return;
  }
  fileUrl = await fileToDataUrl(f);
  renderImagePreview();
  validate();
});

function validate() {
  const title = titleEl.value.trim();
  const content = contentEl.value.trim();

  const { valid, errors } = validatePostForm(title, content);

  titleH.textContent = errors.title;
  contentH.textContent = errors.content;

  setEnabled(btn, valid);
}

titleEl.addEventListener("input", validate);
contentEl.addEventListener("input", validate);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (btn.disabled) return;

  const title = titleEl.value.trim();
  const content = contentEl.value.trim();

  await PostsAPI.update(postId, { title, content, fileUrl });
  location.href = `./post.html?postId=${postId}`;
});

loadPost();
