document.addEventListener("DOMContentLoaded", () => {
  const chatBox     = document.getElementById("chatBox");
  const msgInput    = document.getElementById("msg");
  const sendBtn     = document.getElementById("send");
  const micBtn      = document.getElementById("mic");
  const speakToggle = document.getElementById("speakToggle");
  const statusBar   = document.getElementById("statusBar");
  const predPanel   = document.getElementById("predPanel");
  const sourceBadge = document.getElementById("sourceBadge");
  const topEmotion  = document.getElementById("topEmotion");
  const topConf     = document.getElementById("topConf");
  const riskBar     = document.getElementById("riskBar");
  const riskVal     = document.getElementById("riskVal");
  const sourceDetail= document.getElementById("sourceDetail");

  let speakOn = true;
  let recognizing = false;
  let recognition = null;
  let emotionChart = null;

  // ── Helpers ────────────────────────────────────────────────
  function bubble(text, who) {
    const div = document.createElement("div");
    div.className = "bubble " + who;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
  }

  function setStatus(msg) {
    if (!statusBar) return;
    if (msg) { statusBar.textContent = msg; statusBar.style.display = "block"; }
    else { statusBar.style.display = "none"; }
  }

  function speak(text) {
    if (!speakOn || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text.replace(/\*\*/g, "").slice(0, 350));
    u.rate = 0.95; u.pitch = 1.05; u.lang = "en-IN";
    window.speechSynthesis.speak(u);
  }

  // ── Chart rendering ────────────────────────────────────────
  const EMOTION_COLORS = {
    anxiety:               "rgba(251,191,36,.80)",   // amber
    bipolar:               "rgba(192,132,252,.80)",  // purple
    depression:            "rgba(130,140,248,.80)",  // indigo
    faq:                   "rgba(148,163,184,.80)",  // slate
    "non-suicide":         "rgba(167,243,208,.80)",  // emerald light
    normal:                "rgba(134,239,172,.80)",  // green
    "personality disorder":"rgba(244,114,182,.80)",  // pink
    stress:                "rgba(248,113,113,.80)",  // red light
    suicidal:              "rgba(220,38,38,.80)",    // red dark
    default:               "rgba(180,140,255,.60)",
  };

  function buildChart(probDict) {
    const canvas = document.getElementById("emotionChart");
    if (!canvas || !probDict || Object.keys(probDict).length === 0) return;

    // Sort by probability descending, take top 3
    const sorted = Object.entries(probDict).sort((a, b) => b[1] - a[1]).slice(0, 3);
    const labels = sorted.map(([k]) => k.charAt(0).toUpperCase() + k.slice(1));
    const data   = sorted.map(([, v]) => parseFloat((v * 100).toFixed(1)));
    const colors = sorted.map(([k]) => EMOTION_COLORS[k.toLowerCase()] || EMOTION_COLORS.default);

    if (emotionChart) emotionChart.destroy();

    emotionChart = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderColor: "rgba(255,255,255,.08)",
          borderWidth: 2,
          hoverBorderWidth: 3,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              color: "rgba(200,185,240,.70)",
              font: { size: 11 },
              padding: 10,
              boxWidth: 12,
            }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(1)}%`
            }
          }
        },
        cutout: "60%",
        animation: { animateRotate: true, duration: 600 }
      }
    });
  }

  function updatePredPanel(pred, source, retrieved_chunks = []) {
    if (!predPanel) return;

    // Show/update source badge
    if (sourceBadge) {
      sourceBadge.style.display = "block";
      const labels = { model: "🧠 Model", gemini: "✨ Gemini", crisis: "🚨 Crisis", rag: "📚 Knowledge-Assisted" };
      sourceBadge.textContent = labels[source] || source;
      sourceBadge.className = "source-badge " + (source || "");
    }

    if (!pred || !pred.emotion_probs || Object.keys(pred.emotion_probs).length === 0) {
      // Gemini / no pred — show panel with source but no chart data
      predPanel.style.display = "flex";
      if (topEmotion) topEmotion.textContent = "—";
      if (topConf) topConf.textContent = "";
      if (riskBar) riskBar.style.width = "0%";
      if (riskVal) riskVal.textContent = "—";
      if (sourceDetail) {
        if (source === "rag") {
            let srcText = "Grounded response using trusted knowledge.";
            if (retrieved_chunks && retrieved_chunks.length > 0) {
                const sources = [...new Set(retrieved_chunks.map(c => c.source.split('.')[0]))].join(", ");
                srcText += `<br>Sources: ${sources}`;
            }
            sourceDetail.innerHTML = srcText;
        } else {
            const msgs = {
              gemini: "This response came from Gemini AI — used for general questions outside the mental health model's scope.",
              crisis: "Crisis response triggered. Your safety is the priority.",
              system: "System message."
            };
            sourceDetail.textContent = msgs[source] || "";
        }
      }
      return;
    }

    predPanel.style.display = "flex";

    const emotion  = pred.emotion || "—";
    const conf     = ((pred.emotion_conf || 0) * 100).toFixed(0);
    const riskPct  = ((pred.suicide_prob || 0) * 100).toFixed(0);

    if (topEmotion) topEmotion.textContent = emotion.charAt(0).toUpperCase() + emotion.slice(1);
    if (topConf) topConf.textContent = `${conf}% confidence`;

    if (riskBar) {
      riskBar.style.width = riskPct + "%";
      const pct = parseFloat(riskPct);
      riskBar.style.background = pct >= 65
        ? "linear-gradient(90deg, var(--danger), #ff4444)"
        : pct >= 35
        ? "linear-gradient(90deg, var(--amber), orange)"
        : "linear-gradient(90deg, var(--green), var(--teal))";
    }
    if (riskVal) riskVal.textContent = riskPct + "%";

    if (sourceDetail) {
      if (source === "rag") {
          let srcText = "Grounded response using trusted knowledge.";
          if (retrieved_chunks && retrieved_chunks.length > 0) {
              const sources = [...new Set(retrieved_chunks.map(c => c.source.split('.')[0]))].join(", ");
              srcText += `<br>Sources: ${sources}`;
          }
          sourceDetail.innerHTML = srcText;
      } else if (source === "model") {
          sourceDetail.textContent = `Analyzed using the NeuroVed trained BiLSTM model. Top class: ${emotion} (${conf}%)`;
      } else if (source === "gemini") {
          sourceDetail.textContent = "This response came from Gemini AI — used for general questions outside the mental health model's scope.";
      } else if (source === "crisis") {
          sourceDetail.textContent = "Crisis response triggered. Your safety is the priority.";
      } else {
          sourceDetail.textContent = "";
      }
    }

    buildChart(pred.emotion_probs);
  }

  // ── Send message ───────────────────────────────────────────
  async function sendMsg(textOverride = null) {
    const text = (textOverride !== null ? textOverride : (msgInput.value || "")).trim();
    if (!text) return;

    msgInput.value = "";
    bubble(text, "user");
    const loadingBubble = bubble("🌸 Thinking…", "bot loading");
    setStatus("Analyzing…");

    try {
      const res = await fetch("/chat/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();

      loadingBubble.remove();
      const reply = data.reply || "No reply received.";
      bubble(reply, "bot");
      speak(reply);
      setStatus("");
      updatePredPanel(data.pred, data.source, data.retrieved_chunks);

    } catch (e) {
      console.error(e);
      loadingBubble.remove();
      bubble("Error: " + (e.message || e), "bot");
      setStatus("");
    }
  }

  // ── Controls ───────────────────────────────────────────────
  sendBtn.addEventListener("click", () => sendMsg());
  msgInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMsg(); }
  });

  speakToggle.addEventListener("click", () => {
    speakOn = !speakOn;
    speakToggle.textContent = speakOn ? "🔊" : "🔇";
    if (!speakOn && window.speechSynthesis) window.speechSynthesis.cancel();
  });

  // ── Voice input ────────────────────────────────────────────
  function setupRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return null;
    const r = new SR();
    r.continuous = false; r.interimResults = false; r.lang = "en-IN";

    r.onstart = () => { recognizing = true; micBtn.textContent = "🛑"; setStatus("Listening…"); };
    r.onend   = () => { recognizing = false; micBtn.textContent = "🎙️"; setStatus(""); };
    r.onerror = (ev) => { recognizing = false; micBtn.textContent = "🎙️"; setStatus(""); bubble("Voice error: " + (ev.error || "unknown"), "bot"); };
    r.onresult = (ev) => {
      const t = ev.results[0]?.[0]?.transcript || "";
      if (t.trim()) { setStatus(""); sendMsg(t); }
    };
    return r;
  }

  recognition = setupRecognition();
  if (!recognition) { micBtn.disabled = true; micBtn.title = "Voice not supported (try Chrome/Edge)"; micBtn.textContent = "🎙️ N/A"; }

  micBtn.addEventListener("click", () => {
    if (!recognition) return;
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (recognizing) { recognition.stop(); return; }
    recognition.start();
  });
});