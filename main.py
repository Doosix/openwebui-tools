from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import datetime
import hashlib
import math
import re
import os
import json
import base64
import urllib.parse
from typing import Optional, List
from youtube_transcript_api import YouTubeTranscriptApi
import trafilatura
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY", "")  

app = FastAPI(
    title="OpenWebUI Elite-Tool Server",
    description="V3: Rich UI + Symbols + Security + Super Tools",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Symbols Mapping ──
CURRENCY_SYMBOLS = {
    "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥", 
    "AUD": "A$", "CAD": "C$", "CHF": "Fr", "CNY": "¥", "AED": "د.إ"
}

WEATHER_EMOJIS = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌦️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
    71: "❄️", 73: "❄️", 75: "❄️", 80: "🌦️", 81: "🌦️", 82: "🌦️",
    95: "⛈️", 96: "⛈️", 99: "⛈️"
}

# ── Security ──
async def verify_api_key(authorization: Optional[str] = Header(None)):
    if not API_KEY: return
    if not authorization: raise HTTPException(status_code=401, detail="Missing Auth")
    token = authorization.split(" ")[-1] if " " in authorization else authorization
    if token != API_KEY: raise HTTPException(status_code=403, detail="Invalid Key")

# ── 1. CURRENCY (Rich UI) ──
@app.get("/currency", tags=["Finance"], dependencies=[Depends(verify_api_key)])
async def convert_currency(from_currency: str, to_currency: str, amount: float = 1.0):
    fc, tc = from_currency.upper(), to_currency.upper()
    url = f"https://open.er-api.com/v6/latest/{fc}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
    
    rate = data["rates"].get(tc)
    result = round(amount * rate, 2)
    
    s_from = CURRENCY_SYMBOLS.get(fc, "")
    s_to = CURRENCY_SYMBOLS.get(tc, "")
    
    return {
        "formatted_result": f"{s_from}{amount} {fc} = {s_to}{result} {tc}",
        "symbol": s_to,
        "amount": result,
        "rate": rate,
        "ui_msg": f"💱 **Exchange Rate**: 1 {fc} = {s_to}{rate} {tc}"
    }

# ── 2. WEATHER (Rich UI) ──
@app.get("/weather", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
async def get_weather(lat: float, lon: float):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
    
    current = data.get("current_weather", {})
    code = current.get("weathercode", 0)
    emoji = WEATHER_EMOJIS.get(code, "🌡️")
    
    return {
        "summary": f"{emoji} {current['temperature']}°C (Wind: {current['windspeed']} km/h)",
        "emoji": emoji,
        "temp": current['temperature'],
        "daily_forecast": f"Max: {data['daily']['temperature_2m_max'][0]}°C | Min: {data['daily']['temperature_2m_min'][0]}°C"
    }

# ── 3. YOUTUBE TRANSCRIPT ──
@app.get("/youtube/transcript", tags=["Super Tools"], dependencies=[Depends(verify_api_key)])
def get_youtube_transcript(url: str):
    video_id = url
    if "v=" in url: video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url: video_id = url.split("youtu.be/")[1].split("?")[0]
        
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([t['text'] for t in transcript_list])
        return {
            "ui_header": "📺 **YouTube Transcript Extracted**",
            "word_count": len(full_text.split()),
            "transcript": full_text
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── 4. ADVANCED SCRAPER ──
@app.get("/scrape", tags=["Super Tools"], dependencies=[Depends(verify_api_key)])
async def scrape_site(url: str):
    if not url.startswith("http"): url = "https://" + url
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        content = trafilatura.extract(resp.text)
        return {
            "ui_header": f"🔗 **Content from {url}**",
            "content": content if content else "No text found."
        }

# ── 5. TIME ──
@app.get("/time", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def get_current_time(timezone_offset: int = 330):
    utc_now = datetime.datetime.utcnow()
    local_now = utc_now + datetime.timedelta(minutes=timezone_offset)
    return {
        "ui_msg": f"🕒 **Current Time**: {local_now.strftime('%I:%M %p')} ({local_now.strftime('%A, %d %b %Y')})",
        "time": local_now.strftime("%H:%M:%S")
    }

# ── 6. OTHER TOOLS (SIMPLIFIED) ──
@app.get("/qr-code", dependencies=[Depends(verify_api_key)])
def generate_qr(data: str, size: int = 200):
    encoded = urllib.parse.quote(data)
    return {"qr_url": f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size={size}x{size}", "ui_msg": "📱 **QR Code Generated Successfully**"}

@app.get("/ip-lookup", dependencies=[Depends(verify_api_key)])
async def ip_lookup(ip: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"http://ip-api.com/json/{ip}")
        d = r.json()
        return {"ui_msg": f"🌍 **IP Location**: {d.get('city')}, {d.get('country')}", "details": d}

@app.get("/math", dependencies=[Depends(verify_api_key)])
def calculate(expression: str):
    try:
        res = eval(expression, {"__builtins__": {}}, {"sqrt": math.sqrt, "pow": pow, "pi": math.pi})
        return {"ui_msg": f"🔢 **Result**: `{res}`", "result": res}
    except: return {"error": "Invalid math"}

@app.get("/")
def root():
    return {"name": "OpenWebUI Elite-Tool Server", "version": "3.0.0", "author": "Mohan Ram"}
