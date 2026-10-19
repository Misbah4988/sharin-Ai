import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from livekit.agents import inference
from livekit.agents import llm as livekit_llm

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "").strip()
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "").strip()
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "").strip()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Sargodha").strip() or "Sargodha"

LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-4-31b-it")
SYSTEM_PROMPT = """You are Sharin, a helpful browser-based AI assistant.
Answer in clear, natural English by default. Be friendly, concise, and useful.
When asked to introduce yourself, say you are Sharin, an AI assistant, and include
the exact credit: "Designed by Misbah Ur Rehman."
Be honest about limitations. You cannot directly control the user's operating system
or other desktop applications from a browser. Never claim an action was performed unless it was.
"""

app = FastAPI(title="Sharin AI")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    history: list[dict] = Field(default_factory=list)

@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")

def intro_answer(message: str):
    cmd = re.sub(r"[.!?]+$", "", message.lower().strip())
    patterns = [
        r"\bintroduce yourself\b", r"\bwho are you\b", r"\babout yourself\b",
        r"\bwhat is your name\b", r"\btell me about yourself\b"
    ]
    if any(re.search(p, cmd) for p in patterns):
        return ("Hello! I'm Sharin, your browser-based AI assistant. I can answer questions, "
                "check weather, help draft text, and open supported websites. "
                "Designed by Misbah Ur Rehman.")
    return None

def weather_answer(message: str):
    if not OPENWEATHER_API_KEY:
        return ("Weather isn't configured yet. Add OPENWEATHER_API_KEY to your hosting "
                "environment variables to enable live weather.")
    match = re.search(r"\b(?:weather|temperature|forecast)\s+(?:in|for|at)\s+([a-zA-Z\s,-]+)", message, re.I)
    city = (match.group(1).strip() if match else DEFAULT_CITY).rstrip("?.! ")
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"},
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        return (f"Weather in {data['name']}: {data['weather'][0]['description']}. "
                f"Temperature: {data['main']['temp']}°C, feels like "
                f"{data['main']['feels_like']}°C, humidity {data['main']['humidity']}%.")
    except requests.RequestException:
        return "I couldn't retrieve the weather right now. Check the city name and weather API key."
    except (KeyError, ValueError, IndexError):
        return "The weather service returned an unexpected response."

@app.post("/api/chat")
async def chat(body: ChatRequest):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please enter a message.")

    local = intro_answer(message)
    if local:
        return {"answer": local}

    if any(word in message.lower() for word in ("weather", "temperature", "forecast")):
        return {"answer": weather_answer(message)}

    if not all([LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET]):
        raise HTTPException(
            status_code=503,
            detail="Sharin's AI service isn't configured. Add LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET to the hosting environment variables."
        )

    model = inference.LLM(model=LLM_MODEL)
    context = livekit_llm.ChatContext()
    try:
        context.add_message(role="system", content=SYSTEM_PROMPT)
        # Only accept valid conversational roles and bound history size.
        for item in body.history[-16:]:
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and isinstance(content, str):
                context.add_message(role=role, content=content[:8000])
        context.add_message(role="user", content=message)
        response = await model.chat(chat_ctx=context).collect()
        answer = (getattr(response, "text", "") or "").strip()
        if not answer:
            answer = "I received an empty response. Please try again."
        if re.search(r"\b(introduce yourself|who are you|what is your name|tell me about yourself)\b", message, re.I) and "Designed by Misbah Ur Rehman." not in answer:
            answer += "\n\nDesigned by Misbah Ur Rehman."
        return {"answer": answer}
    except Exception as exc:
        # Keep server credentials and internal exception details out of browser responses.
        raise HTTPException(status_code=502, detail="The AI service request failed. Check the server logs and LiveKit configuration.") from exc
    finally:
        await model.aclose()
