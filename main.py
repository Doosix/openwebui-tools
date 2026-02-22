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
API_KEY = os.getenv("API_KEY", "")  # Set this in Coolify environment or .env

app = FastAPI(
    title="OpenWebUI Super-Tool Server",
    description="V2: Security + YouTube Transcripts + Advanced Web Scraping + Weather",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── SECURITY MIDDLEWARE ───────────────────────────────────

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if not API_KEY:
        return  # Security disabled if no API_KEY is set
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    # Support "Bearer <key>" or just "<key>"
    token = authorization.split(" ")[-1] if " " in authorization else authorization
    
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# ── NEW: YOUTUBE TRANSCRIPT TOOL ──────────────────────────

@app.get(
    "/youtube/transcript",
    summary="Get YouTube Video Transcript",
    description="Fetches the full text transcript of a YouTube video using its URL or Video ID.",
    tags=["Super Tools"],
    dependencies=[Depends(verify_api_key)]
)
def get_youtube_transcript(
    url: str = Query(..., description="YouTube URL or Video ID (e.g., https://youtube.com/watch?v=dQw4w9WgXcQ)")
):
    video_id = url
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([t['text'] for t in transcript_list])
        return {
            "video_id": video_id,
            "transcript": full_text,
            "length_characters": len(full_text),
            "word_count": len(full_text.split())
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch transcript: {str(e)}")

# ── NEW: ADVANCED WEB SCRAPER ─────────────────────────────

@app.get(
    "/scrape",
    summary="Scrape Website Content",
    description="Extracts clean text content from any article or webpage, removing ads and headers.",
    tags=["Super Tools"],
    dependencies=[Depends(verify_api_key)]
)
async def scrape_site(
    url: str = Query(..., description="URL of the webpage to scrape")
):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Failed to fetch page")
            
            # Simple metadata extract
            html = resp.text
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else "Unknown Title"
            
            # Trafilatura extracting main content
            content = trafilatura.extract(html)
            
            return {
                "title": title,
                "url": str(resp.url),
                "content": content if content else "Could not extract main text.",
                "length": len(content) if content else 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── NEW: WEATHER TOOL (FREE) ──────────────────────────────

@app.get(
    "/weather",
    summary="Get Weather Forecast",
    description="Current weather and 3-day forecast using Open-Meteo (No API Key required).",
    tags=["Utilities"],
    dependencies=[Depends(verify_api_key)]
)
async def get_weather(
    lat: float = Query(..., description="Latitude (e.g., 12.97 for Bangalore)"),
    lon: float = Query(..., description="Longitude (e.g., 77.59 for Bangalore)"),
):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
    
    current = data.get("current_weather", {})
    daily = data.get("daily", {})
    
    return {
        "current": {
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "condition_code": current.get("weathercode"),
            "time": current.get("time")
        },
        "forecast": [
            {"date": d, "max": tmx, "min": tmn} 
            for d, tmx, tmn in zip(daily.get("time", []), daily.get("temperature_2m_max", []), daily.get("temperature_2m_min", []))
        ],
        "unit": "Celsius"
    }

# ── PREVIOUS TOOLS (UPDATED WITH AUTH) ────────────────────

@app.get("/time", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def get_current_time(timezone_offset: int = 330):
    utc_now = datetime.datetime.utcnow()
    local_now = utc_now + datetime.timedelta(minutes=timezone_offset)
    return {"local": local_now.strftime("%Y-%m-%d %H:%M:%S"), "day": local_now.strftime("%A")}

@app.get("/currency", tags=["Finance"], dependencies=[Depends(verify_api_key)])
async def convert_currency(from_currency: str, to_currency: str, amount: float = 1.0):
    url = f"https://open.er-api.com/v6/latest/{from_currency.upper()}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
    rate = data["rates"].get(to_currency.upper())
    return {"from": from_currency, "to": to_currency, "amount": amount, "result": round(amount * rate, 4)}

@app.get("/qr-code", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def generate_qr(data: str, size: int = 200):
    encoded = urllib.parse.quote(data)
    return {"qr_url": f"https://api.qrserver.com/v1/create-qr-code/?data={encoded}&size={size}x{size}"}

@app.get("/ip-lookup", tags=["Network"], dependencies=[Depends(verify_api_key)])
async def ip_lookup(ip: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://ip-api.com/json/{ip}")
        return resp.json()

@app.get("/math", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def calculate(expression: str):
    try:
        # Very basic safe eval for demo
        safe_dict = {"sqrt": math.sqrt, "pow": pow, "pi": math.pi}
        return {"result": eval(expression, {"__builtins__": {}}, safe_dict)}
    except: return {"error": "Invalid math"}

# ──────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return {
        "status": "Online",
        "version": "2.0.0",
        "author": "Mohan Ram",
        "security": "Enabled" if API_KEY else "Disabled",
        "features": ["YouTube Transcripts", "Advanced Scraping", "Weather", "Currency", "QR", "IP Lookup"]
    }
