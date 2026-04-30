import { renderHeader } from "../components/header.js";
import { AuthAPI, UsersAPI, ApiError } from "../assets/api.js";
import { fileToDataUrl, setEnabled, getFileUrl } from "../assets/utils.js";
import { confirmModal } from "../components/modal.js";

renderHeader({ showBack: false });

let me = null;
try {
  me = (await AuthAPI.me())?.data;
} catch (_) {
  location.href = "./login.html";
}

const emailEl = document.getElementById("email");
const nickEl = document.getElementById("nickname");
const nickH = document.getElementById("nickHelper");
const saveBtn = document.getElementById("saveBtn");
const toast = document.getElementById("toast");

const profilePicker = document.getElementById("profilePicker");
const profileFile = document.getElementById("profileFile");
const profilePreview = document.getElementById("profilePreview");

let profileUrl = me.profileImageUrl || null;
let lastNickChecked = "";
let nickAvailable = null;

emailEl.value = me.email;
nickEl.value = me.nickname;

if (profileUrl) {
  // If base64 (new upload) -> use as is. If relative (from DB) -> use getFileUrl
  profilePreview.src = profileUrl.startsWith("data:") ? profileUrl : getFileUrl(profileUrl);
  profilePreview.style.display = "block";
  profilePicker.classList.add("has");
}

profilePicker.addEventListener("click", () => profileFile.click());
profileFile.addEventListener("change", async () => {
  const f = profileFile.files?.[0];
  if (!f) return;
  profileUrl = await fileToDataUrl(f);
  profilePreview.src = profileUrl;
  profilePreview.style.display = "block";
  profilePicker.classList.add("has");
  validate();
});

async function checkNickAvailability() {
  const nick = nickEl.value.trim();
  if (!nick) return;
  if (nick === me.nickname) {
    nickAvailable = true;
    return;
  }
  if (nick === lastNickChecked) return;
  lastNickChecked = nick;

  try {
    const res = await AuthAPI.nicknameAvailability(nick);
    nickAvailable = !!res?.data?.available;
  } catch (_) { }
}

function validate() {
  nickH.textContent = "";
  const nick = nickEl.value.trim();

  let ok = true;
  if (!nick) {
    ok = false;
    nickH.textContent = "* 닉네임을 입력해주세요.";
  } else if (nick.includes(" ")) {
    ok = false;
    nickH.textContent = "* 띄어쓰기를 없애주세요";
  } else if (nick.length > 10) {
    ok = false;
    nickH.textContent = "* 닉네임은 최대 10자 까지 작성 가능합니다.";
  } else if (nickAvailable === false && lastNickChecked === nick) {
    ok = false;
    nickH.textContent = "* 중복된 닉네임 입니다.";
  }

  setEnabled(saveBtn, ok && (nick !== me.nickname || profileUrl !== me.profileImageUrl));
}

nickEl.addEventListener("input", () => {
  nickAvailable = null;
  validate();
});
nickEl.addEventListener("blur", async () => {
  await checkNickAvailability();
  if (nickAvailable === false) nickH.textContent = "* 중복된 닉네임 입니다.";
  validate();
});

document.getElementById("profileForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  toast.style.display = "none";
  saveBtn.disabled = true;

  try {
    await checkNickAvailability();
    validate();
    if (saveBtn.disabled) return;

    await UsersAPI.updateMe({
      nickname: nickEl.value.trim(),
      profileImageUrl: profileUrl,
    });

    toast.style.display = "block";
    setTimeout(() => (toast.style.display = "none"), 1500);
    alert("회원정보 수정이 완료되었습니다."); // Alert added

    me = (await AuthAPI.me())?.data;
  } catch (err) {
    if (err instanceof ApiError) {
      nickH.textContent = "* " + err.message;
    } else {
      nickH.textContent = "* 네트워크 오류가 발생했습니다.";
    }
  } finally {
    validate();
  }
});

document.getElementById("withdrawBtn").addEventListener("click", async () => {
  const ok = await confirmModal({
    title: "회원탈퇴 하시겠습니까?",
    desc: "작성된 게시글과 댓글은 삭제됩니다.",
  });
  if (!ok) return;

  await UsersAPI.deleteMe();
  alert("회원탈퇴가 완료되었습니다."); // Alert added
  location.href = "./login.html";
});

validate();
