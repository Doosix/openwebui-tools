from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import datetime
import hashlib
import math
import re
import os
import secrets
import string
import json
import base64
import urllib.parse
from typing import Optional, List
from youtube_transcript_api import YouTubeTranscriptApi
import trafilatura
from duckduckgo_search import DDGS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY", "")  

app = FastAPI(
    title="OpenWebUI Ultimate-Tool Server",
    description="V4: 15+ Tools including Search, Crypto, and more.",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Symbols & Data ──
CURRENCY_SYMBOLS = {
    "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥", 
    "AUD": "A$", "CAD": "C$", "CHF": "Fr", "CNY": "¥", "AED": "د.إ", "BTC": "₿", "ETH": "Ξ"
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

# ── 1. WEB SEARCH (NEW) ──
@app.get("/search", tags=["Super Tools"], dependencies=[Depends(verify_api_key)])
def web_search(q: str = Query(..., description="Query to search on the web")):
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=5):
                results.append(r)
        
        formatted = "\n\n".join([f"🔹 **[{r['title']}]({r['href']})**\n{r['body']}" for r in results])
        return {
            "ui_header": f"🔍 **Search Results for: {q}**",
            "results_markdown": formatted,
            "raw_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── 2. CRYPTO PRICES (NEW) ──
@app.get("/crypto", tags=["Finance"], dependencies=[Depends(verify_api_key)])
async def get_crypto_price(coin: str = Query("bitcoin", description="Coin name, e.g., bitcoin, ethereum, dogecoin")):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd,inr&include_24hr_change=true"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
    
    if coin.lower() not in data:
        raise HTTPException(status_code=404, detail="Coin not found")
        
    prices = data[coin.lower()]
    change = round(prices.get("usd_24h_change", 0), 2)
    change_emoji = "📈" if change >= 0 else "📉"
    
    return {
        "ui_msg": f"🪙 **{coin.capitalize()} Price**\n- USD: ${prices['usd']:,}\n- INR: ₹{prices['inr']:,}\n- 24h Change: {change_emoji} {change}%",
        "usd": prices['usd'],
        "inr": prices['inr'],
        "change_24h": change
    }

# ── 3. PASSWORD GENERATOR (NEW) ──
@app.get("/password", tags=["Security"], dependencies=[Depends(verify_api_key)])
def generate_password(length: int = 16):
    length = max(8, min(64, length))
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = ''.join(secrets.choice(alphabet) for i in range(length))
    return {
        "ui_msg": f"🔑 **Secure Password Generated**\n`{pwd}`",
        "password": pwd,
        "length": length,
        "tip": "Never share your password with anyone."
    }

# ── 4. WIKIPEDIA (NEW) ──
@app.get("/wiki", tags=["Text"], dependencies=[Depends(verify_api_key)])
async def wiki_summary(q: str):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(q)}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Topic not found on Wikipedia")
        data = resp.json()
    
    return {
        "ui_header": f"📚 **Wikipedia: {data.get('title')}**",
        "summary": data.get("extract"),
        "link": data.get("content_urls", {}).get("desktop", {}).get("page"),
        "thumbnail": data.get("thumbnail", {}).get("source")
    }

# ── 5. UNIT CONVERTER (NEW) ──
@app.get("/convert/units", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def convert_units(value: float, from_unit: str, to_unit: str):
    # Simple common conversions
    conversions = {
        ("km", "miles"): 0.621371,
        ("miles", "km"): 1.60934,
        ("kg", "lbs"): 2.20462,
        ("lbs", "kg"): 0.453592,
        ("m", "ft"): 3.28084,
        ("ft", "m"): 0.3048,
    }
    
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = round(value * conversions[key], 2)
        return {"ui_msg": f"📐 **Conversion**: {value}{from_unit} = **{result}{to_unit}**", "result": result}
    
    # Temperature special logic
    if from_unit.lower() == "c" and to_unit.lower() == "f":
        res = round((value * 9/5) + 32, 2)
        return {"ui_msg": f"🌡️ **Temperature**: {value}°C = **{res}°F**", "result": res}
    if from_unit.lower() == "f" and to_unit.lower() == "c":
        res = round((value - 32) * 5/9, 2)
        return {"ui_msg": f"🌡️ **Temperature**: {value}°F = **{res}°C**", "result": res}
        
    return {"error": "Conversion not supported yet. Try km to miles, kg to lbs, or C to F."}


# ── PREVIOUS TOOLS (RICH UI) ──

@app.get("/currency", tags=["Finance"], dependencies=[Depends(verify_api_key)])
async def convert_currency(from_currency: str, to_currency: str, amount: float = 1.0):
    fc, tc = from_currency.upper(), to_currency.upper()
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://open.er-api.com/v6/latest/{fc}")
        data = r.json()
    rate = data["rates"].get(tc)
    res = round(amount * rate, 2)
    s_to = CURRENCY_SYMBOLS.get(tc, "")
    return {"formatted_result": f"{CURRENCY_SYMBOLS.get(fc,'')}{amount} {fc} = {s_to}{res} {tc}", "ui_msg": f"💱 **Exchange Rate**: 1 {fc} = {s_to}{rate} {tc}"}

@app.get("/weather", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
async def get_weather(lat: float, lon: float):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    curr = data['current_weather']
    emoji = WEATHER_EMOJIS.get(curr['weathercode'], "🌡️")
    return {"summary": f"{emoji} {curr['temperature']}°C", "ui_msg": f"{emoji} **Weather**: {curr['temperature']}°C | Wind: {curr['windspeed']}km/h"}

@app.get("/youtube/transcript", tags=["Super Tools"], dependencies=[Depends(verify_api_key)])
def get_youtube_transcript(url: str):
    v_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1]
    try:
        t = YouTubeTranscriptApi.get_transcript(v_id)
        txt = " ".join([i['text'] for i in t])
        return {"ui_header": "📺 **Transcript Extracted**", "transcript": txt}
    except: raise HTTPException(400, "Transcript error")

@app.get("/scrape", tags=["Super Tools"], dependencies=[Depends(verify_api_key)])
async def scrape_site(url: str):
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        return {"ui_header": f"🔗 **Content from {url}**", "content": trafilatura.extract(r.text)}

@app.get("/time", dependencies=[Depends(verify_api_key)])
def get_current_time(timezone_offset: int = 330):
    now = datetime.datetime.utcnow() + datetime.timedelta(minutes=timezone_offset)
    return {"ui_msg": f"🕒 **Current Time**: {now.strftime('%I:%M %p')} ({now.strftime('%A')})"}

@app.get("/qr-code", dependencies=[Depends(verify_api_key)])
def generate_qr(data: str):
    return {"qr_url": f"https://api.qrserver.com/v1/create-qr-code/?data={urllib.parse.quote(data)}&size=200x200", "ui_msg": "📱 **QR Code Ready**"}

@app.get("/ip-lookup", dependencies=[Depends(verify_api_key)])
async def ip_lookup(ip: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"http://ip-api.com/json/{ip}")
        d = r.json()
        return {"ui_msg": f"🌍 **Location**: {d.get('city')}, {d.get('country')}"}

@app.get("/math", dependencies=[Depends(verify_api_key)])
def calculate(expression: str):
    try:
        res = eval(expression, {"__builtins__": {}}, {"sqrt": math.sqrt, "pow": pow, "pi": math.pi})
        return {"ui_msg": f"🔢 **Result**: `{res}`"}
    except: return {"error": "Invalid math"}

@app.get("/")
def root():
    return {"name": "OpenWebUI Ultimate-Tool Server", "version": "4.0.0", "author": "Mohan Ram"}
