import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

_model = None

def _get_model():
    global _model
    if _model is None:
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return None
        _model = genai.Client(api_key=api_key)
    return _model


def ask_gemini(prompt: str) -> str:
    """Call Gemini API with the given prompt. Returns a fallback string on failure."""
    client = _get_model()
    if not client:
        return (
            "I'm here to listen and support you. For general questions, "
            "I rely on an external AI — but that service is not configured yet. "
            "If this is a mental health concern, please feel free to share more."
        )
        
    system_context = (
        "You are a compassionate mental health support assistant. "
        "Be empathetic, concise, and supportive. If the topic is urgent or about self-harm, "
        "always recommend professional help and helplines."
    )
    full_prompt = f"{system_context}\n\nUser: {prompt}"
    
    import time
    import random
    
    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]
    response = None
    
    for model_name in models_to_try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                if response is not None:
                    return response.text.strip()
            except Exception as e:
                error_str = str(e).lower()
                if any(code in error_str for code in ["429", "503", "500", "quota"]):
                    if attempt < max_retries - 1:
                        time.sleep((2 ** attempt) + random.uniform(0, 1))
                        continue
                    else:
                        break # Exhausted retries for this model
                else:
                    break # Break out of retries for non-transient errors
        if response is not None:
            break
                
    # If all models failed or a non-quota error occurred, clear the cache
    global _model
    _model = None
        
    # Emergency failover: if API fails, at least check for crisis
    crisis_keywords = ["suicide", "kill myself", "end my life", "harm myself", "myslef"]
    if any(kw in prompt.lower() for kw in crisis_keywords):
        return (
            "I'm really sorry you're feeling this way. I'm having some technical trouble right now, "
            "but please know that you matter. If you're in India, you can call KIRAN at 1800-599-0019. "
            "Are you safe? Please reach out to someone you trust."
        )
    return "I'm having trouble reaching my knowledge base right now. Please try again in a moment. 🌸"