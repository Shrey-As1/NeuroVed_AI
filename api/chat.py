from fastapi import APIRouter
from pydantic import BaseModel

from utils.retrieval import retrieve_answer
from utils.ml_infer import predict_emotion, detect_suicide
from utils.gemini_api import ask_gemini

router = APIRouter()

class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(request: ChatRequest):

    user_message = request.message

    # 1️⃣ Suicide Detection
    if detect_suicide(user_message):
        return {
            "response": "I'm really sorry you're feeling this way. Please reach out to a professional or someone you trust."
        }

    # 2️⃣ Dataset Retrieval
    dataset_answer = retrieve_answer(user_message)

    if dataset_answer:
        return {"response": dataset_answer}

    # 3️⃣ Emotion Detection
    emotion = predict_emotion(user_message)

    emotion_map = {
        "sad": "I'm here for you. Want to talk about it?",
        "angry": "That sounds frustrating. I'm listening.",
        "fear": "It's okay to feel anxious sometimes.",
        "happy": "That's great to hear!",
        "neutral": None
    }

    if emotion in emotion_map and emotion_map[emotion]:
        return {"response": emotion_map[emotion]}

    # 4️⃣ Gemini Fallback
    return {"response": ask_gemini(user_message)}