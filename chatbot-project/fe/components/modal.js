export function confirmModal({ title, desc, okText = "확인", cancelText = "취소" }) {
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop open";

  backdrop.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true">
      <div class="title">${title}</div>
      <div class="desc">${desc}</div>
      <div class="actions">
        <button class="cancel">${cancelText}</button>
        <button class="ok">${okText}</button>
      </div>
    </div>
  `;

  document.body.appendChild(backdrop);

  return new Promise((resolve) => {
    const close = (val) => {
      backdrop.remove();
      resolve(val);
    };

    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) close(false);
    });

    backdrop.querySelector(".cancel").addEventListener("click", () => close(false));
    backdrop.querySelector(".ok").addEventListener("click", () => close(true));
  });
}
