import { renderHeader } from "../components/header.js";
import { AuthAPI, ApiError } from "../assets/api.js";
import { EMAIL_RE, PW_RE, setEnabled, fileToDataUrl } from "../assets/utils.js";

renderHeader({ showBack: true });

const profilePicker = document.getElementById("profilePicker");
const profileFile = document.getElementById("profileFile");
const profilePreview = document.getElementById("profilePreview");

const emailEl = document.getElementById("email");
const pwEl = document.getElementById("password");
const pw2El = document.getElementById("passwordConfirm");
const nickEl = document.getElementById("nickname");

const emailH = document.getElementById("emailHelper");
const pwH = document.getElementById("pwHelper");
const pw2H = document.getElementById("pw2Helper");
const nickH = document.getElementById("nickHelper");

const btn = document.getElementById("signupBtn");
const form = document.getElementById("signupForm");

let profileDataUrl = null;

let lastEmailChecked = "";
let lastNickChecked = "";
let emailAvailable = null;
let nickAvailable = null;

profilePicker.addEventListener("click", () => profileFile.click());
profileFile.addEventListener("change", async () => {
  const f = profileFile.files?.[0];
  if (!f) return;
  profileDataUrl = await fileToDataUrl(f);
  profilePreview.src = profileDataUrl;
  profilePreview.style.display = "block";
  profilePicker.classList.add("has");
  validateAll();
});

document.getElementById("toLogin").addEventListener("click", () => (location.href = "./login.html"));

async function checkEmailAvailability() {
  const email = emailEl.value.trim();
  if (!email || !EMAIL_RE.test(email)) return;
  if (email === lastEmailChecked) return;

  lastEmailChecked = email;
  try {
    const res = await AuthAPI.emailAvailability(email);
    emailAvailable = !!res?.data?.available;
    if (!emailAvailable) emailH.textContent = "* 중복된 이메일 입니다.";
  } catch (_) { }
}

async function checkNickAvailability() {
  const nick = nickEl.value.trim();
  if (!nick) return;
  if (nick === lastNickChecked) return;
  lastNickChecked = nick;
  try {
    const res = await AuthAPI.nicknameAvailability(nick);
    nickAvailable = !!res?.data?.available;
    if (!nickAvailable) nickH.textContent = "* 중복된 닉네임 입니다.";
  } catch (_) { }
}

function validateAll() {
  const email = emailEl.value.trim();
  const pw = pwEl.value;
  const pw2 = pw2El.value;
  const nick = nickEl.value.trim();

  emailH.textContent = "";
  pwH.textContent = "";
  pw2H.textContent = "";
  nickH.textContent = "";

  let ok = true;

  if (!email) {
    ok = false;
    emailH.textContent = "* 이메일을 입력해주세요.";
  } else if (!EMAIL_RE.test(email)) {
    ok = false;
    emailH.textContent = "* 올바른 이메일 주소 형식을 입력해주세요. (예: example@example.com)";
  } else if (emailAvailable === false && lastEmailChecked === email) {
    ok = false;
    emailH.textContent = "* 중복된 이메일 입니다.";
  }

  if (emailH.textContent) emailEl.classList.add("error");
  else emailEl.classList.remove("error");

  if (!pw) {
    ok = false;
    pwH.textContent = "* 비밀번호를 입력해주세요.";
  } else if (!PW_RE.test(pw)) {
    ok = false;
    pwH.textContent = "* 비밀번호는 8자 이상, 20자 이하이며, 대문자, 소문자, 숫자, 특수문자를 각각 최소 1개 포함해야 합니다.";
  }

  if (pwH.textContent) pwEl.classList.add("error");
  else pwEl.classList.remove("error");

  if (!pw2) {
    ok = false;
    pw2H.textContent = "* 비밀번호를 한번 더 입력해주세요.";
  } else if (pw !== pw2) {
    ok = false;
    pw2H.textContent = "* 비밀번호가 다릅니다.";
  }

  if (pw2H.textContent) pw2El.classList.add("error");
  else pw2El.classList.remove("error");

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

  if (nickH.textContent) nickEl.classList.add("error");
  else nickEl.classList.remove("error");

  setEnabled(btn, ok);
}

emailEl.addEventListener("input", () => {
  emailAvailable = null;
  validateAll();
});
emailEl.addEventListener("blur", async () => {
  await checkEmailAvailability();
  validateAll();
});

nickEl.addEventListener("input", () => {
  nickAvailable = null;
  validateAll();
});
nickEl.addEventListener("blur", async () => {
  await checkNickAvailability();
  validateAll();
});

pwEl.addEventListener("input", validateAll);
pw2El.addEventListener("input", validateAll);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  btn.disabled = true;

  try {
    await checkEmailAvailability();
    await checkNickAvailability();
    validateAll();
    if (btn.disabled) return;

    await AuthAPI.signup({
      email: emailEl.value.trim(),
      password: pwEl.value,
      passwordConfirm: pw2El.value,
      nickname: nickEl.value.trim(),
      profileImageUrl: profileDataUrl,
    });

    alert("회원가입이 완료되었습니다."); // Alert added
    location.href = "./login.html";
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.code.startsWith("EMAIL")) emailH.textContent = "* " + err.message;
      else if (err.code.startsWith("PASSWORD")) pwH.textContent = "* " + err.message;
      else if (err.code.startsWith("NICKNAME")) nickH.textContent = "* " + err.message;
      else pw2H.textContent = "* " + err.message;
    } else {
      pw2H.textContent = "* 네트워크 오류가 발생했습니다.";
    }
  } finally {
    validateAll();
  }
});

validateAll();
