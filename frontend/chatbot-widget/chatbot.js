/**
 * NGPiTECH AI Assistant widget.
 * Drop-in script: builds its own DOM, doesn't touch the host page otherwise.
 * Configure the API base by setting `window.NGP_CHAT_API_BASE` before this
 * script loads (defaults to http://localhost:8000/api for local dev).
 */
(function () {
  const API_BASE = window.NGP_CHAT_API_BASE || "http://localhost:8000/api";

  const launcher = document.createElement("button");
  launcher.id = "ngp-chat-launcher";
  launcher.setAttribute("aria-label", "Open NGPiTECH AI Assistant");
  launcher.innerHTML = "💬";
  document.body.appendChild(launcher);

  const panel = document.createElement("div");
  panel.id = "ngp-chat-panel";
  panel.innerHTML = `
    <div id="ngp-chat-header">
      <div>NGPiTECH AI Assistant<span class="sub">Ask about academics, exams, facilities &amp; more</span></div>
      <div id="ngp-chat-close" role="button" aria-label="Close chat">&times;</div>
    </div>
    <div id="ngp-chat-messages"></div>
    <div id="ngp-chat-typing" style="display:none;">NGPiTECH AI is typing…</div>
    <div id="ngp-chat-input-row">
      <input id="ngp-chat-input" type="text" placeholder="Ask something…" autocomplete="off" />
      <button id="ngp-chat-send">Send</button>
    </div>
  `;
  document.body.appendChild(panel);

  const messagesEl = panel.querySelector("#ngp-chat-messages");
  const inputEl = panel.querySelector("#ngp-chat-input");
  const sendBtn = panel.querySelector("#ngp-chat-send");
  const typingEl = panel.querySelector("#ngp-chat-typing");

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function addMessage(text, sender, sources) {
    const el = document.createElement("div");
    el.className = "ngp-msg " + sender;
    el.textContent = text;

    if (sources && sources.length) {
      const src = document.createElement("div");
      src.className = "ngp-sources";
      src.innerHTML =
        "Sources:<br>" +
        sources
          .map((s) => `📄 ${escapeHtml(s.document)}${s.page ? " p." + s.page : ""}`)
          .join("<br>");
      el.appendChild(src);
    }

    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function greet() {
    addMessage(
      "Hi! I'm the NGPiTECH AI Assistant. Ask me about academics, examinations, departments, facilities, or admissions.",
      "bot"
    );
  }

  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    addMessage(text, "user");
    inputEl.value = "";
    sendBtn.disabled = true;
    typingEl.style.display = "block";

    try {
      const res = await fetch(API_BASE + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) throw new Error("Request failed: " + res.status);

      const data = await res.json();
      addMessage(data.answer || "It is not available in the sources.", "bot", data.sources);
    } catch (err) {
      addMessage(
        "Sorry, I couldn't reach the assistant right now. Please make sure the chatbot server is running and try again.",
        "bot"
      );
    } finally {
      typingEl.style.display = "none";
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  launcher.addEventListener("click", () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open") && !messagesEl.hasChildNodes()) greet();
  });
  panel.querySelector("#ngp-chat-close").addEventListener("click", () => panel.classList.remove("open"));
  sendBtn.addEventListener("click", sendMessage);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
  });
})();
