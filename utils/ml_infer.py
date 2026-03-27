import os
import pickle
import numpy as np

# Suppress TensorFlow C++ logging and oneDNN warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_DIR = os.path.join(_BASE, "models")

MAXLEN = 120

_tokenizer     = None
_label_encoder = None
_emotion_model = None

# Mental-health related keywords for routing decisions
MENTAL_HEALTH_KEYWORDS = {
    "depress", "depression", "anxiety", "anxious", "stress", "stressed",
    "panic", "ptsd", "trauma", "trauma", "bipolar", "schizophrenia",
    "ocd", "phobia", "disorder", "mental", "suicide", "suicidal",
    "self-harm", "self harm", "harm myself", "harm myslef", "kill myself", "kill myslef", "end my life",
    "hopeless", "helpless", "worthless", "numb", "empty", "grief", "grieve",
    "lonely", "loneliness", "isolat", "detach", "emotion", "feeling", "feel",
    "mood", "sleep", "insomnia", "crying", "cry", "overwhelm", "burnout",
    "breakdown", "therapy", "therapist", "psychiatrist", "psychologist",
    "counselling", "counseling", "medication", "antidepressant", "sad",
    "sadness", "anger", "angry", "fear", "scared", "worried", "worry",
    "ashamed", "guilt", "regret", "nervous", "irritable", "exhausted",
    "tired", "fatigue", "paranoid", "hallucination", "delusion"
}


def is_mental_health_query(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in MENTAL_HEALTH_KEYWORDS)


def _lazy_load():
    global _tokenizer, _label_encoder, _emotion_model

    if _tokenizer is None:
        tok_path = os.path.join(_MODEL_DIR, "mental_health_tokenizer.pkl")
        with open(tok_path, "rb") as f:
            _tokenizer = pickle.load(f)

    if _label_encoder is None:
        le_path = os.path.join(_MODEL_DIR, "mental_health_label_encoder.pkl")
        with open(le_path, "rb") as f:
            _label_encoder = pickle.load(f)

    if _emotion_model is None:
        try:
            import tensorflow as tf
            model_path = os.path.join(_MODEL_DIR, "best_mental_health_bilstm_model.keras")
            _emotion_model = tf.keras.models.load_model(model_path, compile=False)
        except Exception:
            _emotion_model = None


def predict_all(user_text: str) -> dict:
    """
    Returns:
      {
        "emotion":        str,          # top predicted class
        "emotion_conf":   float,        # confidence of top class
        "emotion_probs":  dict[str, float],  # all class probabilities
        "suicide_prob":   float,        # derived from negative/crisis emotions
        "model_available": bool
      }
    """
    from utils.text_cleaning import clean_text

    _lazy_load()

    if _emotion_model is None or _tokenizer is None or _label_encoder is None:
        return {
            "emotion": "unknown",
            "emotion_conf": 0.0,
            "emotion_probs": {},
            "suicide_prob": 0.0,
            "model_available": False
        }

    cleaned = clean_text(user_text)

    # Tokenise
    seq = _tokenizer.texts_to_sequences([cleaned])

    # Pad sequences — handle both tf.keras, standalone keras, and Keras 3
    try:
        from keras.preprocessing.sequence import pad_sequences
    except ImportError:
        try:
            from tensorflow.keras.preprocessing.sequence import pad_sequences
        except ImportError:
            from tensorflow.keras.utils import pad_sequences

    x = pad_sequences(seq, maxlen=MAXLEN, padding="post", truncating="post")

    # Predict
    probs = _emotion_model.predict(x, verbose=0)[0]
    labels = list(_label_encoder.classes_)

    # Build prob dict
    prob_dict = {labels[i]: float(probs[i]) for i in range(len(labels))}

    top_idx   = int(np.argmax(probs))
    top_label = labels[top_idx]
    top_conf  = float(probs[top_idx])

    # --- Heuristic Override block to fix model blindspots ---
    # The pre-trained model heavily biases "stress" towards "normal".
    heuristic_map = {
        "stress": ["stress", "stressed", "overwhelm", "overwhelmed", "burnout", "exhausted"],
        "anxiety": ["anxious", "anxiety", "panic", "nervous"],
        "depression": ["depress", "depression", "hopeless", "worthless"]
    }
    for emotion, kws in heuristic_map.items():
        if any(kw in cleaned for kw in kws):
            # Bump the probability of the mapped emotion heavily 
            prob_dict[emotion] = max(prob_dict.get(emotion, 0.0), 0.85)

    # Re-evaluate top_label and top_conf after heuristics
    top_label = max(prob_dict.items(), key=lambda x: x[1])[0]
    top_conf = prob_dict[top_label]
    # --------------------------------------------------------

    # Derive a crisis/suicide proxy from high-negativity classes
    crisis_classes = {"suicidal", "suicide", "depression", "anxiety", "hopeless", "fear", "sad", "anger"}
    suicide_proxy = sum(
        prob_dict.get(lbl, 0.0)
        for lbl in labels
        if any(c in lbl.lower() for c in crisis_classes)
    )
    suicide_proxy = min(float(suicide_proxy), 1.0)

    return {
        "emotion":         top_label,
        "emotion_conf":    top_conf,
        "emotion_probs":   prob_dict,
        "suicide_prob":    suicide_proxy,
        "model_available": True
    }


def predict_emotion(text: str) -> str:
    res = predict_all(text)
    return res.get("emotion", "neutral")


def detect_suicide(text: str) -> bool:
    res = predict_all(text)
    return res.get("suicide_prob", 0.0) >= 0.5