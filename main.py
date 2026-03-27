from fastapi import FastAPI
from api.chat import router as chat_router

app = FastAPI(title="NeuroVed_AI")

app.include_router(chat_router)