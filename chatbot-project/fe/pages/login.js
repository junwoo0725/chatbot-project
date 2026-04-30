import { renderHeader } from "../components/header.js";
import { AuthAPI, ApiError } from "../assets/api.js";
import { EMAIL_RE, PW_RE, setEnabled } from "../assets/utils.js";

renderHeader({ showBack: false });

const emailEl = document.getElementById("email");
const pwEl = document.getElementById("password");
const btn = document.getElementById("loginBtn");
const form = document.getElementById("loginForm");

const emailH = document.getElementById("emailHelper");
const pwH = document.getElementById("pwHelper");

document.getElementById("toSignup").addEventListener("click", () => (location.href = "./signup.html"));

function validate() {
  const email = emailEl.value.trim();
  const pw = pwEl.value;

  emailH.textContent = "";
  pwH.textContent = "";

  let ok = true;

  if (!email) {
    ok = false;
    emailH.textContent = "* 이메일을 입력해주세요.";
  } else if (!EMAIL_RE.test(email)) {
    ok = false;
    emailH.textContent = "* 올바른 이메일 주소 형식을 입력해주세요. (예: example@adapterz.kr)";
  }

  if (!pw) {
    ok = false;
    pwH.textContent = "* 비밀번호를 입력해주세요";
  } else if (!PW_RE.test(pw)) {
    ok = false;
    pwH.textContent =
      "* 비밀번호는 8자 이상, 20자 이하이며, 대문자, 소문자, 숫자, 특수문자를 각각 최소 1개 포함해야 합니다.";
  }

  setEnabled(btn, ok);
}

emailEl.addEventListener("input", validate);
pwEl.addEventListener("input", validate);

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  btn.disabled = true;

  try {
    await AuthAPI.login({ email: emailEl.value.trim(), password: pwEl.value });
    alert("로그인 성공!"); // Alert added
    location.href = "./posts.html";
  } catch (err) {
    validate(); // Re-enable button
    if (err instanceof ApiError) {
      if (err.status === 404) {
        emailH.textContent = "* 존재하지 않는 이메일입니다.";
      } else if (err.status === 401) {
        pwH.textContent = "* 비밀번호가 틀렸습니다.";
      } else {
        pwH.textContent = "* " + err.message;
      }
    } else {
      pwH.textContent = "* 네트워크 오류가 발생했습니다.";
    }
  }
});

validate();
