from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from utils.ml_infer import predict_all, is_mental_health_query
from utils.safety import india_helplines
from utils.gemini_api import ask_gemini
from utils.rag_pipeline import process_rag_query
from utils.semantic_cache import get_cache_instance

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

SAFETY_NOTE = (
    "I hear you, and I care. What you're feeling matters — you matter. 💙\n\n"
    "Please reach out to someone right now. If you're in India:"
)

CRISIS_KEYWORDS = {
    "suicide", "suicidal", "suicide", "suicde", "suiside",
    "kill myself", "kill myslef", "kill my self",
    "end my life", "end life", "end it all",
    "want to die", "i want to die", "wanna die",
    "harm myself", "harm myslef", "harm my self",
    "self-harm", "self harm", "selfharm",
    "no reason to live", "worthless life",
    "not worth living", "life is not worth",
    "jump off", "hang myself", "take my life"
}

def _is_crisis(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in CRISIS_KEYWORDS)


def _risk_reply() -> str:
    helplines = india_helplines()
    lines = [SAFETY_NOTE]
    for h in helplines:
        lines.append(f"  📞 {h['name']}: {h['number']}")
    lines += [
        "",
        "Are you safe right now? Please reach out to a trusted person nearby.",
        "You don't have to face this alone. Tell me what's happening if you feel comfortable."
    ]
    return "\n".join(lines)


def build_mental_health_reply(user_text: str, pred: dict) -> str:
    """Build a reply using the ML model + retrieval pipeline."""
    suicide_prob = pred.get("suicide_prob", 0.0)
    emotion = pred.get("emotion", "neutral")

    # High crisis risk
    if suicide_prob >= 0.65:
        return _risk_reply()

    top_3_text = ""
    if "emotion_probs" in pred and pred["emotion_probs"]:
        sorted_probs = sorted(pred["emotion_probs"].items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_probs[:3]
        top_3_text = "\n\n**Top 3 Detected Conditions:**\n" + "\n".join([f"• {k.title()}: {v*100:.1f}%" for k, v in top_3])

    # Try retrieval first
    retrieved, score = retrieve_answer(user_text, min_score=0.33)
    if retrieved:
        return f"{retrieved}\n\n—\nI sense you may be experiencing signs of **{emotion}**.{top_3_text}\n\nIs there more you'd like to share?"

    # Medium risk
    if 0.35 <= suicide_prob < 0.65:
        return (
            f"{SAFETY_NOTE}\n\n"
            f"I'm noticing some distress. Your condition looks like **{emotion}**.{top_3_text}\n\n"
            "What triggered this today? Are you having thoughts of harming yourself (yes/no)?"
        )

    # Low/general emotional support
    emotion_responses = {
        "depression": "I hear you — it's okay to feel down. What's weighing on your heart today?",
        "anxiety":    "It sounds like you're feeling anxious. Take a deep breath. Want to talk about what's making you anxious?",
        "stress":     "I can tell you're under a lot of stress. Let's take it one step at a time.",
        "bipolar":    "It sounds like you're experiencing some intense shifts. I'm here to listen.",
        "personality disorder": "I'm here to support you without judgment. Tell me what's on your mind.",
        "normal":     "You seem to be doing okay, but I'm always here to chat. What's been on your mind lately?",
        "non-suicide":"It's good that you're reaching out. Tell me more about how you're sorting through things.",
        "faq":        "If you have general questions about mental health, I'm happy to help. 🌸",
    }
    msg = emotion_responses.get(emotion.lower(),
        f"I sense you may be dealing with **{emotion}**. Let's talk through it together.")

    return (
        f"{msg}{top_3_text}\n\n"
        "Here are some gentle questions if you'd like:\n"
        "1️⃣ What happened today?\n"
        "2️⃣ What thought keeps repeating?\n"
        "3️⃣ What's one small thing that might help in the next hour?"
    )


@chat_bp.route("/", methods=["GET"])
@login_required
def page():
    return render_template("chatbot.html")


def _is_informational_query(text: str) -> bool:
    t = text.lower().strip()
    starters = (
        "what", "why", "how", "when", "where", "who",
        "can", "could", "would", "should",
        "is", "are", "do", "does", "did", "tell me"
    )
    return any(t.startswith(q) for q in starters)


@chat_bp.route("/api", methods=["POST"])
@login_required
def api():
    data = request.get_json(force=True)
    msg = (data.get("message") or "").strip()

    if not msg:
        return jsonify({
            "reply": "Please type or say something so I can help. 🌸",
            "pred": None,
            "source": "system"
        })

    # Always evaluate with ML model
    pred = predict_all(msg)

    # Crisis override — always check first
    if _is_crisis(msg):
        return jsonify({
            "reply": _risk_reply(),
            "pred": {"emotion": "suicidal", "emotion_conf": 1.0, "emotion_probs": {"suicidal": 1.0}, "suicide_prob": 1.0},
            "source": "crisis"
        })

    # Gemini for answer and model for prediction (UI charts)
    top_emotion = pred.get("emotion", "neutral") if pred and pred.get("model_available", False) else "neutral"

    # 1. Check Semantic/Exact Cache
    cache = get_cache_instance()
    cached_reply, hit_type = cache.get_cached_response(msg)
    
    if cached_reply:
        return jsonify({
            "reply": cached_reply["reply"],
            "pred": pred,
            "source": f"cache-{hit_type}",
            "retrieved_chunks": cached_reply.get("retrieved_chunks", [])
        })

    # 2. Use RAG Pipeline if Cache Miss
    print(f"[Cache] Cache Miss for query: {msg}")
    print(f"[API] API call triggered to Gemini via RAG Pipeline for query: {msg}")
    rag_result = process_rag_query(msg, top_emotion, min_score=0.20)
    
    # 3. Store Results to Cache
    cache.add_to_cache(msg, {
        "reply": rag_result["reply"],
        "retrieved_chunks": rag_result["retrieved_chunks"]
    })

    return jsonify({
        "reply": rag_result["reply"],
        "pred": pred,
        "source": "rag" if rag_result["used_rag"] else "gemini",
        "retrieved_chunks": rag_result["retrieved_chunks"]
    })

@chat_bp.route("/test_rag", methods=["GET"])
def test_rag():
    try:
        from utils.ml_infer import predict_all
        pred = predict_all("Hi")
        top_emotion = pred.get("emotion", "neutral")
        rag_result = process_rag_query("Hi", top_emotion, min_score=0.20)
        return jsonify(rag_result)
    except Exception as e:
        import traceback
        return traceback.format_exc(), 500