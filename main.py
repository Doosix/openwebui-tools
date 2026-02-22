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
    description="V6: 20+ Tools with Rich UI — Beautiful markdown output with emojis, tables, and formatting.",
    version="6.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

CURRENCY_SYMBOLS = {"USD":"$","INR":"₹","EUR":"€","GBP":"£","JPY":"¥","AUD":"A$","CAD":"C$","CHF":"Fr","CNY":"¥","AED":"د.إ","BTC":"₿","ETH":"Ξ","SGD":"S$","MYR":"RM","KRW":"₩","THB":"฿","RUB":"₽","BRL":"R$","ZAR":"R","SEK":"kr","NOK":"kr","DKK":"kr","PLN":"zł","TRY":"₺","HKD":"HK$","TWD":"NT$","NZD":"NZ$"}
CURRENCY_FLAGS = {"USD":"🇺🇸","INR":"🇮🇳","EUR":"🇪🇺","GBP":"🇬🇧","JPY":"🇯🇵","AUD":"🇦🇺","CAD":"🇨🇦","CHF":"🇨🇭","CNY":"🇨🇳","AED":"🇦🇪","SGD":"🇸🇬","MYR":"🇲🇾","KRW":"🇰🇷","THB":"🇹🇭","RUB":"🇷🇺","BRL":"🇧🇷","ZAR":"🇿🇦","SEK":"🇸🇪","NOK":"🇳🇴","DKK":"🇩🇰","PLN":"🇵🇱","TRY":"🇹🇷","HKD":"🇭🇰","TWD":"🇹🇼","NZD":"🇳🇿"}
WEATHER_EMOJIS = {0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",51:"🌦️",53:"🌦️",55:"🌦️",61:"🌧️",63:"🌧️",65:"🌧️",71:"❄️",73:"❄️",75:"❄️",80:"🌦️",81:"🌦️",82:"🌦️",95:"⛈️",96:"⛈️",99:"⛈️"}
WEATHER_NAMES = {0:"Clear Sky",1:"Mostly Clear",2:"Partly Cloudy",3:"Overcast",45:"Foggy",48:"Rime Fog",51:"Light Drizzle",53:"Drizzle",55:"Heavy Drizzle",61:"Light Rain",63:"Rain",65:"Heavy Rain",71:"Light Snow",73:"Snow",75:"Heavy Snow",80:"Rain Showers",81:"Heavy Showers",82:"Violent Showers",95:"Thunderstorm",96:"Thunderstorm + Hail",99:"Severe Thunderstorm"}

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if not API_KEY: return
    if not authorization: raise HTTPException(401, "🔒 Missing Authorization header")
    token = authorization.split(" ")[-1] if " " in authorization else authorization
    if token != API_KEY: raise HTTPException(403, "🔒 Invalid API Key")

# ═══════════════════════════════════════════════════════════
# 🔍 SEARCH & WEB
# ═══════════════════════════════════════════════════════════

@app.get("/search", summary="🔍 Web Search", description="Live web search powered by DuckDuckGo. Returns top 5 results.", tags=["🔍 Search & Web"], dependencies=[Depends(verify_api_key)])
def web_search(q: str = Query(..., description="Search query")):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, max_results=5):
            results.append(r)
    if not results:
        return {"ui_msg": f"🔍 **No results found for:** `{q}`"}
    
    lines = [f"## 🔍 Search Results for: *\"{q}\"*", "---"]
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. [{r['title']}]({r['href']})")
        lines.append(f"> {r['body']}")
        lines.append("")
    lines.append(f"---\n🔎 *Showing top {len(results)} results from DuckDuckGo*")
    return {"ui_msg": "\n".join(lines), "raw_results": results}

@app.get("/news", summary="📰 Latest News", description="Fetches latest news headlines on any topic.", tags=["🔍 Search & Web"], dependencies=[Depends(verify_api_key)])
def get_news(topic: str = Query(..., description="News topic, e.g. 'AI', 'India', 'Cricket'")):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(topic, max_results=5):
            results.append(r)
    if not results:
        return {"ui_msg": f"📰 No news found for **{topic}**"}
    
    lines = [f"## 📰 Latest News: *{topic}*", "---"]
    for i, r in enumerate(results, 1):
        date = r.get('date', '')[:10] if r.get('date') else ''
        source = r.get('source', 'Unknown')
        lines.append(f"### {i}. 🗞️ [{r['title']}]({r['url']})")
        lines.append(f"📅 {date} • 🏢 *{source}*")
        if r.get('body'): lines.append(f"> {r['body'][:200]}...")
        lines.append("")
    lines.append(f"---\n📡 *{len(results)} headlines fetched just now*")
    return {"ui_msg": "\n".join(lines), "raw_results": results}

@app.get("/scrape", summary="🔗 Scrape Website", description="Extracts clean readable text from any article or webpage.", tags=["🔍 Search & Web"], dependencies=[Depends(verify_api_key)])
async def scrape_site(url: str = Query(..., description="URL to scrape")):
    if not url.startswith("http"): url = "https://" + url
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        content = trafilatura.extract(r.text) or "❌ Could not extract text from this page."
    word_count = len(content.split())
    lines = [
        f"## 🔗 Web Scrape Results",
        f"**🌐 URL:** `{url}`",
        f"**📝 Words:** {word_count:,} | **⏱️ Read:** ~{max(1, word_count//200)} min",
        "---",
        content,
        "---",
        f"*🤖 Extracted using Trafilatura*"
    ]
    return {"ui_msg": "\n\n".join(lines)}

@app.get("/wiki", summary="📚 Wikipedia", description="Returns Wikipedia summary with thumbnail for any topic.", tags=["🔍 Search & Web"], dependencies=[Depends(verify_api_key)])
async def wiki_summary(q: str = Query(..., description="Topic to look up")):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(q)}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code != 200: raise HTTPException(404, f"❌ '{q}' not found on Wikipedia")
        d = r.json()
    
    thumb = d.get("thumbnail", {}).get("source", "")
    link = d.get("content_urls", {}).get("desktop", {}).get("page", "")
    lines = [
        f"## 📚 Wikipedia: {d.get('title', q)}",
        "---",
    ]
    if thumb: lines.append(f"![{d.get('title')}]({thumb})")
    lines.extend([
        "",
        d.get("extract", "No summary available."),
        "",
        "---",
        f"🔗 [Read full article on Wikipedia]({link})" if link else ""
    ])
    return {"ui_msg": "\n".join(lines)}

# ═══════════════════════════════════════════════════════════
# 💰 FINANCE
# ═══════════════════════════════════════════════════════════

@app.get("/currency", summary="💱 Convert Currency", description="Live exchange rates with currency symbols and flags.", tags=["💰 Finance"], dependencies=[Depends(verify_api_key)])
async def convert_currency(from_currency: str = Query(..., description="e.g. USD"), to_currency: str = Query(..., description="e.g. INR"), amount: float = 1.0):
    fc, tc = from_currency.upper(), to_currency.upper()
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://open.er-api.com/v6/latest/{fc}")
        data = r.json()
    rate = data["rates"].get(tc)
    if not rate: raise HTTPException(400, f"❌ Unknown currency: {tc}")
    res = round(amount * rate, 2)
    sf, st = CURRENCY_SYMBOLS.get(fc,""), CURRENCY_SYMBOLS.get(tc,"")
    ff, ft = CURRENCY_FLAGS.get(fc,"💵"), CURRENCY_FLAGS.get(tc,"💵")

    lines = [
        f"## 💱 Currency Conversion",
        "---",
        f"| | Currency | Amount |",
        f"|---|---|---|",
        f"| {ff} **From** | {fc} | {sf}{amount:,.2f} |",
        f"| {ft} **To** | {tc} | **{st}{res:,.2f}** |",
        "",
        f"📊 **Exchange Rate:** 1 {fc} = {st}{rate:,.4f} {tc}",
        "",
        f"---",
        f"*💡 Rates from Open Exchange Rates • Updated in real-time*"
    ]
    return {"ui_msg": "\n".join(lines), "result": res, "rate": rate}

@app.get("/crypto", summary="🪙 Crypto Price", description="Live cryptocurrency prices in USD and INR with 24h change.", tags=["💰 Finance"], dependencies=[Depends(verify_api_key)])
async def get_crypto_price(coin: str = Query("bitcoin", description="e.g. bitcoin, ethereum, dogecoin, solana")):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd,inr&include_24hr_change=true&include_market_cap=true"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    if coin.lower() not in data: raise HTTPException(404, f"❌ Coin '{coin}' not found")
    p = data[coin.lower()]
    chg = round(p.get("usd_24h_change", 0), 2)
    e = "📈" if chg >= 0 else "📉"
    color = "🟢" if chg >= 0 else "🔴"
    mcap = p.get("usd_market_cap", 0)
    mcap_str = f"${mcap/1e9:.1f}B" if mcap > 1e9 else f"${mcap/1e6:.1f}M"
    
    lines = [
        f"## 🪙 {coin.capitalize()} Price",
        "---",
        f"| Metric | Value |",
        f"|---|---|",
        f"| 💵 **USD Price** | **${p['usd']:,.2f}** |",
        f"| ₹ **INR Price** | **₹{p['inr']:,.2f}** |",
        f"| {color} **24h Change** | {e} **{chg}%** |",
        f"| 🏦 **Market Cap** | {mcap_str} |",
        "",
        "---",
        f"*📡 Live data from CoinGecko*"
    ]
    return {"ui_msg": "\n".join(lines), "usd": p['usd'], "inr": p['inr'], "change_24h": chg}

@app.get("/stock", summary="📊 Stock Price", description="Live stock prices with change, exchange info, and currency.", tags=["💰 Finance"], dependencies=[Depends(verify_api_key)])
async def get_stock_price(symbol: str = Query(..., description="Ticker: AAPL, GOOGL, MSFT, RELIANCE.NS, TCS.NS")):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?interval=1d&range=5d"
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
        color = "🟢" if change >= 0 else "🔴"
        currency = meta.get("currency", "USD")
        sym = CURRENCY_SYMBOLS.get(currency, "")
        exchange = meta.get("exchangeName", "Unknown")
        
        lines = [
            f"## 📊 {symbol.upper()} — Stock Price",
            "---",
            f"| Metric | Value |",
            f"|---|---|",
            f"| 💰 **Current Price** | **{sym}{price:,.2f} {currency}** |",
            f"| {color} **Today's Change** | {e} {sym}{change:+,.2f} ({pct:+.2f}%) |",
            f"| 📉 **Previous Close** | {sym}{prev:,.2f} |",
            f"| 🏢 **Exchange** | {exchange} |",
            "",
            "---",
            f"*📡 Live data from Yahoo Finance*"
        ]
        return {"ui_msg": "\n".join(lines), "price": price, "change": change, "change_pct": pct}
    except: raise HTTPException(400, f"❌ Could not find stock: {symbol}")

# ═══════════════════════════════════════════════════════════
# 🎬 MEDIA
# ═══════════════════════════════════════════════════════════

@app.get("/youtube/transcript", summary="📺 YouTube Transcript", description="Full text transcript from any YouTube video.", tags=["🎬 Media"], dependencies=[Depends(verify_api_key)])
def get_youtube_transcript(url: str = Query(..., description="YouTube URL or video ID")):
    vid = url
    if "v=" in url: vid = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url: vid = url.split("youtu.be/")[1].split("?")[0]
    try:
        t = YouTubeTranscriptApi.get_transcript(vid)
        txt = " ".join([i['text'] for i in t])
        words = len(txt.split())
        duration_min = round(t[-1]['start'] / 60) if t else 0
        
        lines = [
            f"## 📺 YouTube Transcript",
            "---",
            f"| Info | Value |",
            f"|---|---|",
            f"| 🎬 **Video ID** | `{vid}` |",
            f"| 📝 **Word Count** | {words:,} words |",
            f"| ⏱️ **Duration** | ~{duration_min} minutes |",
            f"| ⏱️ **Reading Time** | ~{max(1,words//200)} min |",
            "---",
            "",
            txt,
            "",
            "---",
            f"*🔗 [Watch on YouTube](https://youtube.com/watch?v={vid})*"
        ]
        return {"ui_msg": "\n".join(lines)}
    except Exception as e: raise HTTPException(400, f"❌ Transcript error: {str(e)}")

# ═══════════════════════════════════════════════════════════
# 🌦️ UTILITIES
# ═══════════════════════════════════════════════════════════

@app.get("/weather", summary="🌦️ Weather Forecast", description="Current weather + 3-day forecast (free, no API key).", tags=["🌦️ Utilities"], dependencies=[Depends(verify_api_key)])
async def get_weather(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    curr = data['current_weather']
    emoji = WEATHER_EMOJIS.get(curr['weathercode'], "🌡️")
    name = WEATHER_NAMES.get(curr['weathercode'], "Unknown")
    daily = data.get("daily", {})
    
    lines = [
        f"## {emoji} Weather Report",
        f"**📍 Location:** {lat}°N, {lon}°E",
        "---",
        f"### 🌡️ Right Now",
        f"| Metric | Value |",
        f"|---|---|",
        f"| {emoji} **Condition** | {name} |",
        f"| 🌡️ **Temperature** | **{curr['temperature']}°C** |",
        f"| 💨 **Wind Speed** | {curr['windspeed']} km/h |",
        f"| 🧭 **Wind Direction** | {curr['winddirection']}° |",
        "",
        "### 📅 3-Day Forecast",
        f"| Day | Condition | 🔺 High | 🔻 Low | 🌧️ Rain |",
        f"|---|---|---|---|---|",
    ]
    for i in range(min(3, len(daily.get("time", [])))):
        d = daily["time"][i]
        wc = daily["weathercode"][i]
        mx = daily["temperature_2m_max"][i]
        mn = daily["temperature_2m_min"][i]
        rain = daily.get("precipitation_sum", [0]*3)[i]
        de = WEATHER_EMOJIS.get(wc, "🌡️")
        dn = WEATHER_NAMES.get(wc, "")
        lines.append(f"| {d} | {de} {dn} | {mx}°C | {mn}°C | {rain}mm |")
    
    lines.extend(["", "---", "*🌐 Data from Open-Meteo (free & open-source)*"])
    return {"ui_msg": "\n".join(lines)}

@app.get("/time", summary="🕒 Current Time", description="Returns current date and time for any timezone.", tags=["🌦️ Utilities"], dependencies=[Depends(verify_api_key)])
def get_current_time(timezone_offset: int = Query(330, description="UTC offset in minutes (330=IST, 0=UTC, -300=EST)")):
    now = datetime.datetime.utcnow() + datetime.timedelta(minutes=timezone_offset)
    tz_hrs = timezone_offset // 60
    tz_min = abs(timezone_offset % 60)
    tz_str = f"UTC{'+' if timezone_offset>=0 else ''}{tz_hrs}:{tz_min:02d}"
    
    lines = [
        f"## 🕒 Current Date & Time",
        "---",
        f"| | |",
        f"|---|---|",
        f"| 🕒 **Time** | **{now.strftime('%I:%M:%S %p')}** |",
        f"| 📅 **Date** | {now.strftime('%A, %d %B %Y')} |",
        f"| 🌐 **Timezone** | {tz_str} |",
        f"| 📆 **Day of Year** | {now.timetuple().tm_yday}/365 |",
    ]
    return {"ui_msg": "\n".join(lines)}

@app.get("/convert/units", summary="📐 Unit Converter", description="Convert between units: km/miles, kg/lbs, °C/°F, L/gal, cm/in.", tags=["🌦️ Utilities"], dependencies=[Depends(verify_api_key)])
def convert_units(value: float = Query(...), from_unit: str = Query(..., description="e.g. km, miles, kg, lbs, C, F, l, gal"), to_unit: str = Query(...)):
    conversions = {("km","miles"):0.621371,("miles","km"):1.60934,("kg","lbs"):2.20462,("lbs","kg"):0.453592,("m","ft"):3.28084,("ft","m"):0.3048,("cm","in"):0.393701,("in","cm"):2.54,("l","gal"):0.264172,("gal","l"):3.78541,("km","m"):1000,("m","km"):0.001,("g","kg"):0.001,("kg","g"):1000,("oz","g"):28.3495,("g","oz"):0.035274}
    f_u, t_u = from_unit.lower(), to_unit.lower()
    result = None
    
    if (f_u, t_u) in conversions:
        result = round(value * conversions[(f_u, t_u)], 4)
    elif f_u == "c" and t_u == "f":
        result = round((value * 9/5) + 32, 2)
    elif f_u == "f" and t_u == "c":
        result = round((value - 32) * 5/9, 2)
    
    if result is not None:
        lines = [
            f"## 📐 Unit Conversion",
            "---",
            f"| Direction | Value |",
            f"|---|---|",
            f"| ➡️ **From** | **{value:,.4g} {from_unit}** |",
            f"| ✅ **To** | **{result:,.4g} {to_unit}** |",
            "",
            f"📊 Formula: `1 {from_unit} = {round(result/value if value else 0, 6)} {to_unit}`",
            "---"
        ]
        return {"ui_msg": "\n".join(lines), "result": result}
    return {"ui_msg": f"❌ **Unsupported conversion:** `{from_unit}` → `{to_unit}`\n\n💡 **Supported:** km↔miles, kg↔lbs, m↔ft, cm↔in, L↔gal, °C↔°F, g↔oz, g↔kg"}

@app.get("/qr-code", summary="📱 QR Code Generator", description="Create a QR code for any text or URL.", tags=["🌦️ Utilities"], dependencies=[Depends(verify_api_key)])
def generate_qr(data: str = Query(..., description="Text or URL to encode"), size: int = 300):
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={urllib.parse.quote(data)}&size={size}x{size}"
    lines = [
        f"## 📱 QR Code",
        "---",
        f"**📝 Content:** `{data[:80]}`",
        "",
        f"![QR Code]({qr_url})",
        "",
        f"📥 [Download QR Code]({qr_url})",
        "---"
    ]
    return {"ui_msg": "\n".join(lines), "qr_url": qr_url}

@app.get("/math", summary="🔢 Calculator", description="Evaluate math expressions (sqrt, sin, cos, log, pi, etc).", tags=["🌦️ Utilities"], dependencies=[Depends(verify_api_key)])
def calculate(expression: str = Query(..., description="e.g. sqrt(144) + 2**10")):
    safe = {"__builtins__":{},"sqrt":math.sqrt,"sin":math.sin,"cos":math.cos,"tan":math.tan,"log":math.log,"log10":math.log10,"pi":math.pi,"e":math.e,"abs":abs,"round":round,"pow":pow,"floor":math.floor,"ceil":math.ceil}
    try:
        res = eval(expression, safe)
        lines = [
            f"## 🔢 Calculator",
            "---",
            f"| | |",
            f"|---|---|",
            f"| 📝 **Expression** | `{expression}` |",
            f"| ✅ **Result** | **`{res}`** |",
            "---"
        ]
        return {"ui_msg": "\n".join(lines), "result": res}
    except Exception as ex: raise HTTPException(400, f"❌ Invalid expression: `{expression}`\n\nError: {str(ex)}")

@app.get("/translate", summary="🌐 Translate Text", description="Translate text between 50+ languages using MyMemory API.", tags=["🌦️ Utilities"], dependencies=[Depends(verify_api_key)])
async def translate_text(text: str = Query(..., description="Text to translate"), from_lang: str = Query("en", description="Source: en, ta, hi, fr, de, es, ja, ko, zh..."), to_lang: str = Query("ta", description="Target language code")):
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={from_lang}|{to_lang}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        data = r.json()
    translated = data.get("responseData", {}).get("translatedText", "Translation failed")
    
    lines = [
        f"## 🌐 Translation",
        "---",
        f"| | |",
        f"|---|---|",
        f"| 🗣️ **From** | `{from_lang}` |",
        f"| 🎯 **To** | `{to_lang}` |",
        "",
        f"### 📝 Original",
        f"> {text}",
        "",
        f"### ✅ Translated",
        f"> **{translated}**",
        "---",
        f"*🌍 Powered by MyMemory Translation*"
    ]
    return {"ui_msg": "\n".join(lines), "translated": translated}

# ═══════════════════════════════════════════════════════════
# 🔐 SECURITY
# ═══════════════════════════════════════════════════════════

@app.get("/password", summary="🔑 Password Generator", description="Creates a cryptographically secure random password.", tags=["🔐 Security"], dependencies=[Depends(verify_api_key)])
def generate_password(length: int = Query(16, description="Length: 8–64")):
    length = max(8, min(64, length))
    pwd = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}") for _ in range(length))
    
    has_upper = bool(re.search(r'[A-Z]', pwd))
    has_lower = bool(re.search(r'[a-z]', pwd))
    has_digit = bool(re.search(r'\d', pwd))
    has_special = bool(re.search(r'[^a-zA-Z0-9]', pwd))
    strength = sum([has_upper, has_lower, has_digit, has_special, length >= 12, length >= 20])
    strength_bar = "🟢" * strength + "⚪" * (6 - strength)
    strength_label = ["Weak","Weak","Fair","Good","Strong","Very Strong","Ultra Strong"][strength]
    
    lines = [
        f"## 🔑 Secure Password",
        "---",
        f"```",
        f"{pwd}",
        f"```",
        "",
        f"| Check | Status |",
        f"|---|---|",
        f"| 📏 Length | {length} characters |",
        f"| 🔠 Uppercase | {'✅' if has_upper else '❌'} |",
        f"| 🔡 Lowercase | {'✅' if has_lower else '❌'} |",
        f"| 🔢 Numbers | {'✅' if has_digit else '❌'} |",
        f"| 🔣 Symbols | {'✅' if has_special else '❌'} |",
        f"| 💪 Strength | {strength_bar} {strength_label} |",
        "---",
        f"*⚠️ Save this password now — it won't be shown again!*"
    ]
    return {"ui_msg": "\n".join(lines), "password": pwd}

@app.get("/hash", summary="🔐 Hash Generator", description="Generates MD5, SHA1, SHA256, and SHA512 hashes.", tags=["🔐 Security"], dependencies=[Depends(verify_api_key)])
def generate_hash(text: str = Query(..., description="Text to hash")):
    e = text.encode("utf-8")
    lines = [
        f"## 🔐 Hash Generator",
        f"**📝 Input:** `{text[:50]}{'...' if len(text)>50 else ''}`",
        "---",
        f"| Algorithm | Hash |",
        f"|---|---|",
        f"| **MD5** | `{hashlib.md5(e).hexdigest()}` |",
        f"| **SHA1** | `{hashlib.sha1(e).hexdigest()}` |",
        f"| **SHA256** | `{hashlib.sha256(e).hexdigest()}` |",
        f"| **SHA512** | `{hashlib.sha512(e).hexdigest()[:64]}...` |",
        "---"
    ]
    return {"ui_msg": "\n".join(lines), "md5": hashlib.md5(e).hexdigest(), "sha1": hashlib.sha1(e).hexdigest(), "sha256": hashlib.sha256(e).hexdigest(), "sha512": hashlib.sha512(e).hexdigest()}

# ═══════════════════════════════════════════════════════════
# 🌍 NETWORK
# ═══════════════════════════════════════════════════════════

@app.get("/ip-lookup", summary="🌍 IP Geolocation", description="City, country, ISP, and coordinates for any IP address.", tags=["🌍 Network"], dependencies=[Depends(verify_api_key)])
async def ip_lookup(ip: str = Query(..., description="IP address, e.g. 8.8.8.8")):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"http://ip-api.com/json/{ip}")
        d = r.json()
    
    lines = [
        f"## 🌍 IP Geolocation",
        f"**🔎 IP:** `{ip}`",
        "---",
        f"| Info | Details |",
        f"|---|---|",
        f"| 📍 **City** | {d.get('city','N/A')} |",
        f"| 🏙️ **Region** | {d.get('regionName','N/A')} |",
        f"| 🌏 **Country** | {d.get('country','N/A')} |",
        f"| 🏢 **ISP** | {d.get('isp','N/A')} |",
        f"| 🏛️ **Organization** | {d.get('org','N/A')} |",
        f"| 🕐 **Timezone** | {d.get('timezone','N/A')} |",
        f"| 📡 **Coordinates** | {d.get('lat','')}, {d.get('lon','')} |",
        "---"
    ]
    return {"ui_msg": "\n".join(lines), "details": d}

@app.get("/domain-info", summary="🌐 Domain WHOIS", description="Domain registration details — registrar, creation, expiry.", tags=["🌍 Network"], dependencies=[Depends(verify_api_key)])
async def domain_info(domain: str = Query(..., description="e.g. google.com")):
    try:
        import whois
        w = whois.whois(domain)
        created = str(w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date)[:10] if w.creation_date else "N/A"
        expires = str(w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date)[:10] if w.expiration_date else "N/A"
        registrar = w.registrar or "N/A"
        
        lines = [
            f"## 🌐 Domain Info: {domain}",
            "---",
            f"| Info | Details |",
            f"|---|---|",
            f"| 🏢 **Registrar** | {registrar} |",
            f"| 📅 **Created** | {created} |",
            f"| ⏰ **Expires** | {expires} |",
            f"| 🔒 **Status** | {(w.status[0] if isinstance(w.status, list) else w.status) if w.status else 'N/A'} |",
            "---"
        ]
        return {"ui_msg": "\n".join(lines)}
    except Exception as e: raise HTTPException(400, f"❌ WHOIS error: {str(e)}")

@app.get("/dns-lookup", summary="🔎 DNS Lookup", description="Resolve DNS A records for any domain.", tags=["🌍 Network"], dependencies=[Depends(verify_api_key)])
async def dns_lookup(domain: str = Query(..., description="e.g. google.com")):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://dns.google/resolve?name={domain}&type=A")
        data = r.json()
    answers = data.get("Answer", [])
    ips = [a["data"] for a in answers if a.get("type") == 1]
    
    lines = [
        f"## 🔎 DNS Lookup: {domain}",
        "---",
        f"| # | IP Address | TTL |",
        f"|---|---|---|",
    ]
    for i, a in enumerate([a for a in answers if a.get("type")==1], 1):
        lines.append(f"| {i} | `{a['data']}` | {a.get('TTL','')}s |")
    
    if not ips: lines.append(f"| ❌ | No A records found | |")
    lines.extend(["", "---", "*🌐 Resolved via Google Public DNS*"])
    return {"ui_msg": "\n".join(lines), "ips": ips}

# ═══════════════════════════════════════════════════════════
# 📝 TEXT & DATA
# ═══════════════════════════════════════════════════════════

@app.get("/text-analyze", summary="📝 Text Analyzer", description="Word count, sentences, reading time, and top words.", tags=["📝 Text"], dependencies=[Depends(verify_api_key)])
def analyze_text(text: str = Query(..., description="Text to analyze")):
    words = len(re.findall(r'\b\w+\b', text))
    chars = len(text)
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    paragraphs = len([p for p in text.split('\n') if p.strip()])
    read_sec = round((words / 200) * 60)
    top = {}
    for w in re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()):
        top[w] = top.get(w, 0) + 1
    top5 = sorted(top.items(), key=lambda x: x[1], reverse=True)[:5]
    
    lines = [
        f"## 📝 Text Analysis",
        "---",
        f"| Metric | Value |",
        f"|---|---|",
        f"| 📊 **Words** | {words:,} |",
        f"| 🔤 **Characters** | {chars:,} |",
        f"| 📄 **Sentences** | {sentences:,} |",
        f"| 📑 **Paragraphs** | {paragraphs} |",
        f"| ⏱️ **Reading Time** | {read_sec//60}m {read_sec%60}s |",
        f"| 📏 **Avg Words/Sentence** | {round(words/sentences,1)} |",
        "",
        f"### 🏆 Top Words",
        f"| Word | Count |",
        f"|---|---|",
    ]
    for w, c in top5:
        bar = "█" * min(c, 10)
        lines.append(f"| `{w}` | {bar} {c} |")
    lines.append("---")
    return {"ui_msg": "\n".join(lines)}

@app.get("/define", summary="📖 Dictionary", description="English word definition, phonetics, and examples.", tags=["📝 Text"], dependencies=[Depends(verify_api_key)])
async def define_word(word: str = Query(..., description="English word, e.g. 'ephemeral'")):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}")
        if r.status_code == 404: raise HTTPException(404, f"❌ No definition found for '{word}'")
        data = r.json()
    entry = data[0]
    phonetic = entry.get("phonetic", "")
    
    lines = [
        f"## 📖 {word.capitalize()} {phonetic}",
        "---",
    ]
    for m in entry.get("meanings", [])[:3]:
        pos = m['partOfSpeech']
        lines.append(f"### 🏷️ *{pos}*")
        for i, d in enumerate(m.get("definitions", [])[:2], 1):
            lines.append(f"{i}. {d.get('definition','')}")
            if d.get('example'): lines.append(f"   > 💬 *\"{d['example']}\"*")
        if m.get('synonyms'): lines.append(f"   🔄 **Synonyms:** {', '.join(m['synonyms'][:5])}")
        lines.append("")
    
    audio = ""
    for p in entry.get("phonetics", []):
        if p.get("audio"): audio = p["audio"]; break
    if audio: lines.append(f"🔊 [Listen to pronunciation]({audio})")
    lines.append("---")
    return {"ui_msg": "\n".join(lines)}

# ═══════════════════════════════════════════════════════════
# 👤 TESTING
# ═══════════════════════════════════════════════════════════

@app.get("/fake-user", summary="👤 Fake User Profile", description="Random fake user profile for testing purposes.", tags=["🧪 Testing"], dependencies=[Depends(verify_api_key)])
async def fake_user():
    async with httpx.AsyncClient() as client:
        r = await client.get("https://randomuser.me/api/?nat=in,us,gb")
        data = r.json()
    u = data["results"][0]
    
    lines = [
        f"## 👤 Random User Profile",
        "---",
        f"![Avatar]({u['picture']['large']})",
        "",
        f"| Info | Details |",
        f"|---|---|",
        f"| 👤 **Name** | {u['name']['title']} {u['name']['first']} {u['name']['last']} |",
        f"| 📧 **Email** | {u['email']} |",
        f"| 📱 **Phone** | {u['phone']} |",
        f"| 🎂 **Age** | {u['dob']['age']} years old |",
        f"| 🎉 **Birthday** | {u['dob']['date'][:10]} |",
        f"| 📍 **Location** | {u['location']['city']}, {u['location']['state']}, {u['location']['country']} |",
        f"| 🔑 **Username** | `{u['login']['username']}` |",
        "---",
        f"*⚠️ This is a randomly generated fake profile for testing only*"
    ]
    return {"ui_msg": "\n".join(lines)}

# ═══════════════════════════════════════════════════════════

@app.get("/", include_in_schema=False)
def root():
    return {"name": "OpenWebUI Ultimate-Tool Server", "version": "6.0.0", "tools": 20, "author": "Mohan Ram", "docs": "/docs"}
