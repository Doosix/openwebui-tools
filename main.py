from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
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
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
import trafilatura
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY", "")

app = FastAPI(
    title="OpenWebUI Ultimate-Tool Server",
    description="V5: 20+ Tools — Search, Crypto, Stocks, Translate, News, Domain, and more.",
    version="5.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

CURRENCY_SYMBOLS = {"USD":"$","INR":"₹","EUR":"€","GBP":"£","JPY":"¥","AUD":"A$","CAD":"C$","CHF":"Fr","CNY":"¥","AED":"د.إ","BTC":"₿","ETH":"Ξ"}
WEATHER_EMOJIS = {0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",51:"🌦️",53:"🌦️",55:"🌦️",61:"🌧️",63:"🌧️",65:"🌧️",71:"❄️",73:"❄️",75:"❄️",80:"🌦️",81:"🌦️",82:"🌦️",95:"⛈️",96:"⛈️",99:"⛈️"}

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if not API_KEY: return
    if not authorization: raise HTTPException(401, "Missing Auth")
    token = authorization.split(" ")[-1] if " " in authorization else authorization
    if token != API_KEY: raise HTTPException(403, "Invalid Key")

# ═══════════════════════════════════════════════════════════
# 🔍 SEARCH & WEB TOOLS
# ═══════════════════════════════════════════════════════════

@app.get("/search", summary="Search the Web", description="Live web search using DuckDuckGo. Returns top 5 results with title, URL, and snippet.", tags=["Search & Web"], dependencies=[Depends(verify_api_key)])
def web_search(q: str = Query(..., description="Search query")):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, max_results=5):
            results.append(r)
    formatted = "\n\n".join([f"🔹 **[{r['title']}]({r['href']})**\n{r['body']}" for r in results])
    return {"ui_header": f"🔍 **Search: {q}**", "results_markdown": formatted, "raw_results": results}

@app.get("/news", summary="Get Latest News", description="Fetches latest news headlines on any topic using DuckDuckGo News.", tags=["Search & Web"], dependencies=[Depends(verify_api_key)])
def get_news(topic: str = Query(..., description="News topic, e.g., 'AI', 'India', 'Cricket'")):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(topic, max_results=5):
            results.append(r)
    formatted = "\n\n".join([f"📰 **[{r['title']}]({r['url']})**\n_{r.get('date','')}_\n{r.get('body','')}" for r in results])
    return {"ui_header": f"📰 **Latest News: {topic}**", "news_markdown": formatted, "raw_results": results}

@app.get("/scrape", summary="Scrape Website Content", description="Extracts clean text from any article or webpage.", tags=["Search & Web"], dependencies=[Depends(verify_api_key)])
async def scrape_site(url: str = Query(..., description="URL to scrape")):
    if not url.startswith("http"): url = "https://" + url
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        return {"ui_header": f"🔗 **Content from {url}**", "content": trafilatura.extract(r.text) or "No text found."}

@app.get("/wiki", summary="Wikipedia Summary", description="Returns Wikipedia summary for any topic.", tags=["Search & Web"], dependencies=[Depends(verify_api_key)])
async def wiki_summary(q: str = Query(..., description="Topic to look up")):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(q)}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code != 200: raise HTTPException(404, "Topic not found")
        d = r.json()
    return {"ui_header": f"📚 **Wikipedia: {d.get('title')}**", "summary": d.get("extract"), "link": d.get("content_urls",{}).get("desktop",{}).get("page"), "thumbnail": d.get("thumbnail",{}).get("source")}

# ═══════════════════════════════════════════════════════════
# 💰 FINANCE TOOLS
# ═══════════════════════════════════════════════════════════

@app.get("/currency", summary="Convert Currency", description="Live exchange rates with currency symbols (₹, $, €, £).", tags=["Finance"], dependencies=[Depends(verify_api_key)])
async def convert_currency(from_currency: str = Query(..., description="e.g. USD"), to_currency: str = Query(..., description="e.g. INR"), amount: float = 1.0):
    fc, tc = from_currency.upper(), to_currency.upper()
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://open.er-api.com/v6/latest/{fc}")
        data = r.json()
    rate = data["rates"].get(tc)
    if not rate: raise HTTPException(400, f"Unknown currency: {tc}")
    res = round(amount * rate, 2)
    s_f, s_t = CURRENCY_SYMBOLS.get(fc,""), CURRENCY_SYMBOLS.get(tc,"")
    return {"formatted_result": f"{s_f}{amount:,.2f} {fc} = {s_t}{res:,.2f} {tc}", "ui_msg": f"💱 **Exchange Rate**: 1 {fc} = {s_t}{rate} {tc}", "result": res, "rate": rate}

@app.get("/crypto", summary="Crypto Price", description="Live cryptocurrency prices in USD and INR with 24h change.", tags=["Finance"], dependencies=[Depends(verify_api_key)])
async def get_crypto_price(coin: str = Query("bitcoin", description="e.g. bitcoin, ethereum, dogecoin, solana")):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd,inr&include_24hr_change=true"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    if coin.lower() not in data: raise HTTPException(404, "Coin not found")
    p = data[coin.lower()]
    chg = round(p.get("usd_24h_change", 0), 2)
    e = "📈" if chg >= 0 else "📉"
    return {"ui_msg": f"🪙 **{coin.capitalize()}**\n💵 USD: ${p['usd']:,}\n₹ INR: ₹{p['inr']:,}\n{e} 24h: {chg}%", "usd": p['usd'], "inr": p['inr'], "change_24h": chg}

@app.get("/stock", summary="Stock Price", description="Get live stock price, market cap, and 52-week range for any ticker symbol.", tags=["Finance"], dependencies=[Depends(verify_api_key)])
async def get_stock_price(symbol: str = Query(..., description="Stock ticker, e.g. AAPL, GOOGL, RELIANCE.NS, TCS.NS")):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?interval=1d&range=1d"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = r.json()
    try:
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice", 0)
        prev = meta.get("chartPreviousClose", 0)
        change = round(price - prev, 2)
        pct = round((change / prev) * 100, 2) if prev else 0
        e = "📈" if change >= 0 else "📉"
        currency = meta.get("currency", "USD")
        sym = CURRENCY_SYMBOLS.get(currency, "")
        return {
            "ui_msg": f"📊 **{symbol.upper()}**\n💰 Price: {sym}{price:,.2f} {currency}\n{e} Change: {sym}{change} ({pct}%)\n🏢 Exchange: {meta.get('exchangeName','')}",
            "price": price, "change": change, "change_pct": pct, "currency": currency
        }
    except: raise HTTPException(400, f"Could not fetch data for {symbol}")

# ═══════════════════════════════════════════════════════════
# 🎬 MEDIA TOOLS
# ═══════════════════════════════════════════════════════════

@app.get("/youtube/transcript", summary="YouTube Transcript", description="Full text transcript from any YouTube video.", tags=["Media"], dependencies=[Depends(verify_api_key)])
def get_youtube_transcript(url: str = Query(..., description="YouTube URL or video ID")):
    vid = url
    if "v=" in url: vid = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url: vid = url.split("youtu.be/")[1].split("?")[0]
    try:
        t = YouTubeTranscriptApi.get_transcript(vid)
        txt = " ".join([i['text'] for i in t])
        return {"ui_header": f"📺 **YouTube Transcript** ({len(txt.split())} words)", "transcript": txt}
    except Exception as e: raise HTTPException(400, f"Transcript error: {str(e)}")

# ═══════════════════════════════════════════════════════════
# 🌦️ UTILITIES
# ═══════════════════════════════════════════════════════════

@app.get("/weather", summary="Weather Forecast", description="Current weather + forecast using Open-Meteo (free, no API key needed).", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
async def get_weather(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    curr = data['current_weather']
    emoji = WEATHER_EMOJIS.get(curr['weathercode'], "🌡️")
    daily = data.get("daily", {})
    forecast = "\n".join([f"📅 {d}: ⬆️{mx}°C ⬇️{mn}°C" for d, mx, mn in zip(daily.get("time",[])[:3], daily.get("temperature_2m_max",[])[:3], daily.get("temperature_2m_min",[])[:3])])
    return {"ui_msg": f"{emoji} **Weather Now**: {curr['temperature']}°C | Wind: {curr['windspeed']}km/h\n\n**3-Day Forecast:**\n{forecast}"}

@app.get("/time", summary="Current Date & Time", description="Returns current date/time for any timezone offset.", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def get_current_time(timezone_offset: int = Query(330, description="Offset in minutes from UTC (330 = IST)")):
    now = datetime.datetime.utcnow() + datetime.timedelta(minutes=timezone_offset)
    return {"ui_msg": f"🕒 **{now.strftime('%I:%M %p')}** — {now.strftime('%A, %d %B %Y')}"}

@app.get("/convert/units", summary="Unit Converter", description="Converts between common units: km/miles, kg/lbs, m/ft, °C/°F.", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def convert_units(value: float = Query(...), from_unit: str = Query(..., description="e.g. km, miles, kg, lbs, C, F"), to_unit: str = Query(...)):
    conversions = {("km","miles"):0.621371,("miles","km"):1.60934,("kg","lbs"):2.20462,("lbs","kg"):0.453592,("m","ft"):3.28084,("ft","m"):0.3048,("cm","in"):0.393701,("in","cm"):2.54,("l","gal"):0.264172,("gal","l"):3.78541}
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        res = round(value * conversions[key], 2)
        return {"ui_msg": f"📐 **{value} {from_unit}** = **{res} {to_unit}**", "result": res}
    if from_unit.lower() == "c" and to_unit.lower() == "f":
        return {"ui_msg": f"🌡️ **{value}°C** = **{round((value*9/5)+32, 2)}°F**", "result": round((value*9/5)+32, 2)}
    if from_unit.lower() == "f" and to_unit.lower() == "c":
        return {"ui_msg": f"🌡️ **{value}°F** = **{round((value-32)*5/9, 2)}°C**", "result": round((value-32)*5/9, 2)}
    return {"error": f"Unsupported: {from_unit} → {to_unit}. Try km/miles, kg/lbs, C/F, l/gal, cm/in."}

@app.get("/qr-code", summary="Generate QR Code", description="Create a QR code for any text or URL.", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def generate_qr(data: str = Query(..., description="Text or URL to encode"), size: int = 200):
    return {"qr_url": f"https://api.qrserver.com/v1/create-qr-code/?data={urllib.parse.quote(data)}&size={size}x{size}", "ui_msg": f"📱 **QR Code for**: `{data}`"}

@app.get("/math", summary="Math Calculator", description="Evaluate safe math expressions (sqrt, sin, cos, log, pi, etc).", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
def calculate(expression: str = Query(..., description="e.g. sqrt(144) + 2**10")):
    safe = {"__builtins__":{},"sqrt":math.sqrt,"sin":math.sin,"cos":math.cos,"tan":math.tan,"log":math.log,"log10":math.log10,"pi":math.pi,"e":math.e,"abs":abs,"round":round,"pow":pow,"floor":math.floor,"ceil":math.ceil}
    try:
        res = eval(expression, safe)
        return {"ui_msg": f"🔢 `{expression}` = **{res}**", "result": res}
    except Exception as ex: raise HTTPException(400, f"Invalid: {str(ex)}")

@app.get("/translate", summary="Translate Text", description="Translate text between languages using MyMemory API (free).", tags=["Utilities"], dependencies=[Depends(verify_api_key)])
async def translate_text(text: str = Query(..., description="Text to translate"), from_lang: str = Query("en", description="Source language code (en, ta, hi, fr, de, etc.)"), to_lang: str = Query("ta", description="Target language code")):
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={from_lang}|{to_lang}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    translated = data.get("responseData", {}).get("translatedText", "Translation failed")
    return {"ui_msg": f"🌐 **Translation ({from_lang} → {to_lang})**\n\n📝 Original: {text}\n✅ Translated: **{translated}**", "translated": translated}

# ═══════════════════════════════════════════════════════════
# 🔐 SECURITY TOOLS
# ═══════════════════════════════════════════════════════════

@app.get("/password", summary="Generate Secure Password", description="Creates a cryptographically secure random password.", tags=["Security"], dependencies=[Depends(verify_api_key)])
def generate_password(length: int = Query(16, description="Password length (8–64)")):
    length = max(8, min(64, length))
    pwd = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(length))
    return {"ui_msg": f"🔑 **Secure Password:**\n```\n{pwd}\n```\n📏 Length: {length} characters", "password": pwd}

@app.get("/hash", summary="Hash Generator", description="Generates MD5, SHA1, SHA256, and SHA512 hashes.", tags=["Security"], dependencies=[Depends(verify_api_key)])
def generate_hash(text: str = Query(..., description="Text to hash")):
    e = text.encode("utf-8")
    return {"ui_msg": f"🔐 **Hashes for** `{text[:30]}...`\n\n| Algorithm | Hash |\n|---|---|\n| MD5 | `{hashlib.md5(e).hexdigest()}` |\n| SHA256 | `{hashlib.sha256(e).hexdigest()}` |", "md5": hashlib.md5(e).hexdigest(), "sha1": hashlib.sha1(e).hexdigest(), "sha256": hashlib.sha256(e).hexdigest(), "sha512": hashlib.sha512(e).hexdigest()}

# ═══════════════════════════════════════════════════════════
# 🌍 NETWORK TOOLS
# ═══════════════════════════════════════════════════════════

@app.get("/ip-lookup", summary="IP Geolocation", description="Returns city, country, ISP, and coordinates for any IP.", tags=["Network"], dependencies=[Depends(verify_api_key)])
async def ip_lookup(ip: str = Query(..., description="IP address, e.g. 8.8.8.8")):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"http://ip-api.com/json/{ip}")
        d = r.json()
    return {"ui_msg": f"🌍 **IP: {ip}**\n📍 Location: {d.get('city')}, {d.get('regionName')}, {d.get('country')}\n🏢 ISP: {d.get('isp')}\n🕐 Timezone: {d.get('timezone')}\n📡 Coordinates: {d.get('lat')}, {d.get('lon')}", "details": d}

@app.get("/domain-info", summary="Domain Info / WHOIS", description="Lookup domain registration details — owner, registrar, expiry date.", tags=["Network"], dependencies=[Depends(verify_api_key)])
async def domain_info(domain: str = Query(..., description="Domain name, e.g. google.com")):
    try:
        import whois
        w = whois.whois(domain)
        return {
            "ui_msg": f"🌐 **Domain: {domain}**\n🏢 Registrar: {w.registrar}\n📅 Created: {w.creation_date}\n⏰ Expires: {w.expiration_date}\n🔒 Status: {w.status if isinstance(w.status, str) else w.status[0] if w.status else 'N/A'}",
            "registrar": w.registrar, "created": str(w.creation_date), "expires": str(w.expiration_date)
        }
    except Exception as e: raise HTTPException(400, f"WHOIS error: {str(e)}")

@app.get("/dns-lookup", summary="DNS Lookup", description="Resolve DNS records for a domain using public DNS.", tags=["Network"], dependencies=[Depends(verify_api_key)])
async def dns_lookup(domain: str = Query(..., description="Domain to resolve, e.g. google.com")):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://dns.google/resolve?name={domain}&type=A")
        data = r.json()
    answers = data.get("Answer", [])
    ips = [a["data"] for a in answers if a.get("type") == 1]
    return {"ui_msg": f"🔎 **DNS for {domain}**\n\n" + "\n".join([f"📡 `{ip}`" for ip in ips]) if ips else f"❌ No A records found for {domain}", "ips": ips}

# ═══════════════════════════════════════════════════════════
# 📝 TEXT TOOLS
# ═══════════════════════════════════════════════════════════

@app.get("/text-analyze", summary="Analyze Text", description="Word count, sentence count, reading time, and top words.", tags=["Text"], dependencies=[Depends(verify_api_key)])
def analyze_text(text: str = Query(..., description="Text to analyze")):
    words = len(re.findall(r'\b\w+\b', text))
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    read_sec = round((words / 200) * 60)
    top = {}
    for w in re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()):
        top[w] = top.get(w, 0) + 1
    top5 = sorted(top.items(), key=lambda x: x[1], reverse=True)[:5]
    return {"ui_msg": f"📝 **Text Analysis**\n\n| Metric | Value |\n|---|---|\n| Words | {words} |\n| Sentences | {sentences} |\n| Reading Time | {read_sec//60}m {read_sec%60}s |\n| Avg Words/Sentence | {round(words/sentences,1)} |\n\n**Top Words:** {', '.join([f'`{w}`({c})' for w,c in top5])}"}

@app.get("/define", summary="Dictionary", description="English word definition, phonetics, and examples.", tags=["Text"], dependencies=[Depends(verify_api_key)])
async def define_word(word: str = Query(..., description="English word, e.g. 'ephemeral'")):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}")
        if r.status_code == 404: raise HTTPException(404, f"No definition for '{word}'")
        data = r.json()
    entry = data[0]
    meanings = []
    for m in entry.get("meanings", [])[:3]:
        d = m.get("definitions", [{}])[0]
        meanings.append(f"**{m['partOfSpeech']}**: {d.get('definition','')}")
    phonetic = entry.get("phonetic", "")
    return {"ui_msg": f"📖 **{word}** {phonetic}\n\n" + "\n\n".join(meanings)}

# ═══════════════════════════════════════════════════════════
# 👤 TESTING
# ═══════════════════════════════════════════════════════════

@app.get("/fake-user", summary="Generate Fake User", description="Random fake user profile for testing purposes.", tags=["Testing"], dependencies=[Depends(verify_api_key)])
async def fake_user():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://randomuser.me/api/?nat=in,us,gb")
        data = r.json()
    u = data["results"][0]
    return {"ui_msg": f"👤 **{u['name']['first']} {u['name']['last']}**\n📧 {u['email']}\n📱 {u['phone']}\n🎂 Age: {u['dob']['age']}\n📍 {u['location']['city']}, {u['location']['country']}\n🖼️ [Avatar]({u['picture']['large']})"}

# ═══════════════════════════════════════════════════════════

@app.get("/", include_in_schema=False)
def root():
    return {"name": "OpenWebUI Ultimate-Tool Server", "version": "5.0.0", "tools": 20, "author": "Mohan Ram", "docs": "/docs"}
