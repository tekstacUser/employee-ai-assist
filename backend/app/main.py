"""
Employee AI Assistant — backend
A thin FastAPI layer that forwards chat requests to the LiteLLM proxy.
No business logic about routing tiers lives here — that is entirely owned
by litellm/config.yaml (Coding Question 1). The backend just picks a
tier hint based on simple heuristics and lets LiteLLM's routing rules
decide the actual model.
"""
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

LITELLM_BASE_URL = os.environ.get("LITELLM_BASE_URL", "http://litellm:4000")
LITELLM_MASTER_KEY = os.environ.get("LITELLM_MASTER_KEY", "")

app = FastAPI(title="Employee AI Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    business_unit: str = "hr"   # hr | it | finance
    tier_hint: str = "standard-tier"  # simple-tier | standard-tier | complex-tier


class ChatResponse(BaseModel):
    reply: str
    model_used: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Forwards the message to LiteLLM using the OpenAI-compatible
    chat/completions endpoint. The `model` field maps to one of the
    tier names defined in litellm/config.yaml (simple-tier /
    standard-tier / complex-tier) once Coding Question 1 is complete.
    """
    payload = {
        "model": req.tier_hint,
        "messages": [{"role": "user", "content": req.message}],
        "metadata": {"bu": req.business_unit},
    }
    headers = {"Authorization": f"Bearer {LITELLM_MASTER_KEY}"}

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(
                f"{LITELLM_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"LiteLLM proxy error: {exc}",
            )

    data = resp.json()
    reply = data["choices"][0]["message"]["content"]
    model_used = data.get("model", req.tier_hint)
    return ChatResponse(reply=reply, model_used=model_used)
