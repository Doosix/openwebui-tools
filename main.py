from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import datetime
import hashlib
import math
import re
import json
import base64
import urllib.parse
from typing import Optional, List

app = FastAPI(
    title="OpenWebUI Multi-Tool Server",
    description="A collection of useful tools for OpenWebUI — currency, time, QR, text analysis, IP lookup, and more.",
    version="1.0.0",
    contact={"name": "Mohan Ram"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# 1. DATE & TIME TOOL
# ─────────────────────────────────────────────

@app.get(
    "/time",
    summary="Get current date and time",
    description="Returns the current UTC date, time, day of week, week number, and Unix timestamp.",
    tags=["Utilities"],
)
def get_current_time(
    timezone_offset: int = Query(default=330, description="Timezone offset in minutes from UTC (e.g. 330 for IST +5:30)")
):
    utc_now = datetime.datetime.utcnow()
    local_now = utc_now + datetime.timedelta(minutes=timezone_offset)
    return {
        "utc": utc_now.strftime("%Y-%m-%d %H:%M:%S"),
        "local": local_now.strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week": local_now.strftime("%A"),
        "week_number": local_now.isocalendar()[1],
        "unix_timestamp": int(utc_now.timestamp()),
        "timezone_offset_minutes": timezone_offset,
        "iso_8601": local_now.isoformat(),
    }


# ─────────────────────────────────────────────
# 2. CURRENCY EXCHANGE TOOL
# ─────────────────────────────────────────────

@app.get(
    "/currency",
    summary="Convert currency",
    description="Converts an amount from one currency to another using live exchange rates (open.er-api.com).",
    tags=["Finance"],
)
async def convert_currency(
    from_currency: str = Query(..., description="Source currency code, e.g. USD"),
    to_currency: str = Query(..., description="Target currency code, e.g. INR"),
    amount: float = Query(default=1.0, description="Amount to convert"),
):
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    url = f"https://open.er-api.com/v6/latest/{from_currency}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not fetch exchange rates.")
        data = resp.json()
    if data.get("result") != "success":
        raise HTTPException(status_code=400, detail=f"Invalid base currency: {from_currency}")
    rates = data.get("rates", {})
    if to_currency not in rates:
        raise HTTPException(status_code=400, detail=f"Unknown target currency: {to_currency}")
    rate = rates[to_currency]
    converted = round(amount * rate, 4)
    return {
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
        "rate": rate,
        "converted_amount": converted,
        "last_updated": data.get("time_last_update_utc", "N/A"),
    }


# ─────────────────────────────────────────────
# 3. IP LOOKUP TOOL
# ─────────────────────────────────────────────

@app.get(
    "/ip-lookup",
    summary="Look up IP address info",
    description="Returns geolocation information about a given IP address using ip-api.com.",
    tags=["Network"],
)
async def ip_lookup(
    ip: str = Query(..., description="IP address to look up, e.g. 8.8.8.8"),
):
    url = f"http://ip-api.com/json/{ip}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not reach ip-api.com")
        data = resp.json()
    if data.get("status") == "fail":
        raise HTTPException(status_code=400, detail=data.get("message", "Lookup failed"))
    return {
        "ip": data.get("query"),
        "country": data.get("country"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "zip": data.get("zip"),
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
        "isp": data.get("isp"),
        "org": data.get("org"),
        "timezone": data.get("timezone"),
    }


# ─────────────────────────────────────────────
# 4. TEXT ANALYZER TOOL
# ─────────────────────────────────────────────

@app.get(
    "/text-analyze",
    summary="Analyze text statistics",
    description="Counts words, sentences, characters, paragraphs, reading time, and detects language hints.",
    tags=["Text"],
)
def analyze_text(
    text: str = Query(..., description="The text to analyze"),
):
    words = len(re.findall(r'\b\w+\b', text))
    sentences = len(re.findall(r'[.!?]+', text)) or 1
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))
    paragraphs = len([p for p in text.split("\n\n") if p.strip()])
    reading_time_sec = round((words / 200) * 60, 1)  # avg 200 wpm
    top_words = {}
    for w in re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()):
        top_words[w] = top_words.get(w, 0) + 1
    top_5 = sorted(top_words.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "word_count": words,
        "sentence_count": sentences,
        "character_count": chars,
        "character_count_no_spaces": chars_no_space,
        "paragraph_count": paragraphs,
        "average_words_per_sentence": round(words / sentences, 1),
        "estimated_reading_time_seconds": reading_time_sec,
        "estimated_reading_time_human": f"{int(reading_time_sec // 60)}m {int(reading_time_sec % 60)}s",
        "top_5_words": [{"word": w, "count": c} for w, c in top_5],
    }


# ─────────────────────────────────────────────
# 5. QR CODE GENERATOR TOOL
# ─────────────────────────────────────────────

@app.get(
    "/qr-code",
    summary="Generate QR code URL",
    description="Returns a QR code image URL for any text or URL using the free qrserver.com API.",
    tags=["Utilities"],
)
def generate_qr(
    data: str = Query(..., description="Text or URL to encode in the QR code"),
    size: int = Query(default=200, description="Size in pixels (50–500)"),
    color: str = Query(default="000000", description="Foreground color hex (no #), e.g. 000000"),
    bg_color: str = Query(default="ffffff", description="Background color hex (no #), e.g. ffffff"),
):
    size = max(50, min(500, size))
    encoded = urllib.parse.quote(data)
    url = (
        f"https://api.qrserver.com/v1/create-qr-code/"
        f"?data={encoded}&size={size}x{size}&color={color}&bgcolor={bg_color}&format=png"
    )
    return {
        "qr_image_url": url,
        "data_encoded": data,
        "size_px": size,
        "tip": "Open the qr_image_url in a browser or embed it in an <img> tag.",
    }


# ─────────────────────────────────────────────
# 6. HASH GENERATOR TOOL
# ─────────────────────────────────────────────

@app.get(
    "/hash",
    summary="Generate hash of any text",
    description="Computes MD5, SHA1, SHA256, and SHA512 hashes of the provided input string.",
    tags=["Security"],
)
def generate_hash(
    text: str = Query(..., description="Text to hash"),
):
    encoded = text.encode("utf-8")
    return {
        "input": text,
        "md5": hashlib.md5(encoded).hexdigest(),
        "sha1": hashlib.sha1(encoded).hexdigest(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "sha512": hashlib.sha512(encoded).hexdigest(),
    }


# ─────────────────────────────────────────────
# 7. MATH CALCULATOR TOOL
# ─────────────────────────────────────────────

@app.get(
    "/math",
    summary="Perform math calculations",
    description="Evaluates safe mathematical expressions including sqrt, sin, cos, log, pi, etc.",
    tags=["Utilities"],
)
def calculate(
    expression: str = Query(..., description="Math expression, e.g. 'sqrt(144) + 2 ** 8'"),
):
    safe_globals = {
        "__builtins__": {},
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "abs": abs,
        "round": round,
        "pow": pow,
        "floor": math.floor,
        "ceil": math.ceil,
    }
    try:
        result = eval(expression, safe_globals)
        return {"expression": expression, "result": result}
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid expression: {str(ex)}")


# ─────────────────────────────────────────────
# 8. FAKE USER GENERATOR TOOL
# ─────────────────────────────────────────────

@app.get(
    "/fake-user",
    summary="Generate a fake user profile",
    description="Returns a randomized fake user profile for testing — name, email, address, job, avatar.",
    tags=["Testing"],
)
async def fake_user():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://randomuser.me/api/?nat=in,us,gb")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not reach randomuser.me")
        data = resp.json()
    user = data["results"][0]
    name = user["name"]
    loc = user["location"]
    return {
        "full_name": f"{name['first']} {name['last']}",
        "gender": user["gender"],
        "email": user["email"],
        "phone": user["phone"],
        "username": user["login"]["username"],
        "nationality": user["nat"],
        "age": user["dob"]["age"],
        "address": {
            "street": f"{loc['street']['number']} {loc['street']['name']}",
            "city": loc["city"],
            "state": loc["state"],
            "country": loc["country"],
            "postcode": loc["postcode"],
        },
        "avatar_url": user["picture"]["large"],
    }


# ─────────────────────────────────────────────
# 9. URL SHORTENER INFO TOOL
# ─────────────────────────────────────────────

@app.get(
    "/url-info",
    summary="Get meta info from a URL",
    description="Fetches and extracts title, description, and status from any public URL.",
    tags=["Network"],
)
async def url_info(
    url: str = Query(..., description="Full URL to inspect, e.g. https://example.com"),
):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    headers = {"User-Agent": "OpenWebUI-Tool/1.0"}
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
        except Exception as ex:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(ex)}")
    html = resp.text[:5000]  # only parse first 5kb
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)', html, re.IGNORECASE)
    if not desc_match:
        desc_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', html, re.IGNORECASE)
    return {
        "url": str(resp.url),
        "status_code": resp.status_code,
        "title": title_match.group(1).strip() if title_match else "N/A",
        "description": desc_match.group(1).strip() if desc_match else "N/A",
        "content_type": resp.headers.get("content-type", "unknown"),
        "server": resp.headers.get("server", "unknown"),
    }


# ─────────────────────────────────────────────
# 10. WORD DEFINITION TOOL
# ─────────────────────────────────────────────

@app.get(
    "/define",
    summary="Get English word definition",
    description="Returns the definition, phonetic, part of speech, and example for an English word.",
    tags=["Text"],
)
async def define_word(
    word: str = Query(..., description="English word to define, e.g. 'ephemeral'"),
):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail=f"No definition found for '{word}'")
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail="Dictionary API unavailable")
        data = resp.json()
    entry = data[0]
    meanings = []
    for m in entry.get("meanings", [])[:3]:
        defs = m.get("definitions", [])
        if defs:
            meanings.append({
                "part_of_speech": m.get("partOfSpeech"),
                "definition": defs[0].get("definition"),
                "example": defs[0].get("example"),
                "synonyms": defs[0].get("synonyms", [])[:5],
            })
    return {
        "word": entry.get("word"),
        "phonetic": entry.get("phonetic", "N/A"),
        "audio_url": next(
            (p.get("audio") for p in entry.get("phonetics", []) if p.get("audio")), "N/A"
        ),
        "meanings": meanings,
        "source_url": entry.get("sourceUrls", [""])[0],
    }


# ─────────────────────────────────────────────
# ROOT INFO
# ─────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "OpenWebUI Multi-Tool Server",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi_spec": "/openapi.json",
        "available_tools": [
            "/time", "/currency", "/ip-lookup", "/text-analyze",
            "/qr-code", "/hash", "/math", "/fake-user", "/url-info", "/define"
        ],
    }
