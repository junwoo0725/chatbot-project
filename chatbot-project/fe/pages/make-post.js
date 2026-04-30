import { renderHeader } from "../components/header.js";
import { PostsAPI, AuthAPI } from "../assets/api.js";
import { setEnabled, fileToDataUrl, validatePostForm } from "../assets/utils.js";

renderHeader({ showBack: true });

try {
  await AuthAPI.me();
} catch (_) {
  location.href = "./login.html";
}

const form = document.getElementById("makeForm");
const titleEl = document.getElementById("title");
const contentEl = document.getElementById("content");
const fileEl = document.getElementById("file");

const titleH = document.getElementById("titleHelper");
const contentH = document.getElementById("contentHelper");
const btn = document.getElementById("submitBtn");

let fileUrl = null;

fileEl.addEventListener("change", async () => {
  const f = fileEl.files?.[0];
  if (!f) {
    fileUrl = null;
    validate();
    return;
  }
  fileUrl = await fileToDataUrl(f);
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

  const res = await PostsAPI.create({
    title: titleEl.value.trim(),
    content: contentEl.value.trim(),
    fileUrl,
  });

  const newId = res?.data?.postId;
  location.href = `./post.html?postId=${newId}`;
});

validate();
