# 🚀 OpenWebUI Ultimate-Tool Server

> **15+ AI-powered tools** for OpenWebUI — Search, Crypto, YouTube, Weather, and more. Built with FastAPI and deployed on Coolify in minutes.

[![Version](https://img.shields.io/badge/Version-4.0.0-blue)](https://github.com/Doosix/openwebui-tools)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🛠️ What Is This?

This is a self-hosted **OpenAPI-compatible tool server** that gives your AI (e.g. Gemini, Llama) real-time superpowers inside **OpenWebUI**. When connected, your AI can search the web, convert currency, get crypto prices, read YouTube videos, check the weather, and much more — all in one chat!

---

## ⚡ Quickstart (Local)

**1. Clone and Install:**
```bash
git clone https://github.com/Doosix/openwebui-tools.git
cd openwebui-tools
pip install -r requirements.txt
```

**2. Create a `.env` file:**
```
API_KEY=your_secret_key_here
```

**3. Start the server:**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload
```

Or on Windows, just double-click `start.bat`

- **Docs:** http://localhost:8765/docs
- **OpenAPI Spec:** http://localhost:8765/openapi.json

---

## ☁️ Deploy on Coolify

**1. Push to GitHub:**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

**2. In Coolify Dashboard:**
- **New Resource** → **Application** → **Public Repository**
- **URL:** `https://github.com/Doosix/openwebui-tools`
- **Build Pack:** `Dockerfile` (auto-detected)
- **Port:** `8765`
- Click **Deploy** ✅

**3. Set Environment Variable in Coolify:**
- Go to your app → **Environment Variables** → **+ Add**
- `API_KEY` = `your_secret_key_here`
- Click **Save** → **Redeploy**

**4. Enable Auto-Deploy (Webhooks):**
- Coolify app → **Webhooks** → Copy the **GitHub Webhook URL**
- GitHub repo → **Settings** → **Webhooks** → **Add webhook**
- Paste URL, set Content-Type: `application/json` → **Save**

---

## 🔌 Connect to OpenWebUI

1. Go to **OpenWebUI → Admin Panel → Settings → External Tools**
2. Click **`+`** to add a new connection
3. Fill in:

| Field | Value |
|---|---|
| **URL** | `https://your-coolify-domain.com` |
| **OpenAPI Spec URL** | `https://your-coolify-domain.com/openapi.json` |
| **Auth** | Bearer Token |
| **Token / Headers** | `{"Authorization": "Bearer your_secret_key_here"}` |

4. Click **Save** — Done! 🎉

---

## 🔧 All 15+ Tools

### 🔍 Search & Web
| Tool | Endpoint | Description |
|---|---|---|
| Web Search | `GET /search` | Live DuckDuckGo search results |
| Web Scraper | `GET /scrape` | Extract clean article text from any URL |
| URL Info | `GET /url-info` | Title, description, server info |
| Wikipedia | `GET /wiki` | Wikipedia summary for any topic |

### 💰 Finance
| Tool | Endpoint | Description |
|---|---|---|
| Currency | `GET /currency` | Live exchange rates (₹, $, €, £ etc.) |
| Crypto | `GET /crypto` | Bitcoin, Ethereum, Dogecoin prices in USD/INR |

### 🎬 Media
| Tool | Endpoint | Description |
|---|---|---|
| YouTube Transcript | `GET /youtube/transcript` | Full text from any YouTube video |

### 🌦️ Utilities
| Tool | Endpoint | Description |
|---|---|---|
| Weather | `GET /weather` | Real-time weather + 3-day forecast |
| Date & Time | `GET /time` | Current time with timezone support |
| Unit Converter | `GET /convert/units` | km/miles, kg/lbs, °C/°F, m/ft |
| Math Calculator | `GET /math` | Safe expression evaluator |
| QR Code | `GET /qr-code` | Generate QR code for any text/URL |

### 🔐 Security
| Tool | Endpoint | Description |
|---|---|---|
| Password Generator | `GET /password` | Cryptographically secure passwords |
| Hash Generator | `GET /hash` | MD5, SHA1, SHA256, SHA512 hashes |

### 🌍 Network
| Tool | Endpoint | Description |
|---|---|---|
| IP Lookup | `GET /ip-lookup` | Geolocation, ISP, city, country |

### 📝 Text & Data
| Tool | Endpoint | Description |
|---|---|---|
| Text Analyzer | `GET /text-analyze` | Word count, reading time, top words |
| Word Definition | `GET /define` | English dictionary with audio |
| Fake User | `GET /fake-user` | Random user profile for testing |

---

## 💬 Example Prompts

Once connected to OpenWebUI, ask your AI naturally:

```
🔍 "Search the web for latest AI news"
🪙 "What is Bitcoin's price in Indian Rupees right now?"
📺 "Summarize this YouTube video: [URL]"
💱 "Convert 100 USD to INR"
🌤️ "What's the weather in Mumbai? (lat: 19.07, lon: 72.87)"
📐 "Convert 37 Celsius to Fahrenheit"
📚 "Tell me about Elon Musk from Wikipedia"
🔑 "Generate a strong 20-character password"
🌍 "Where is the IP address 8.8.8.8?"
📖 "Define the word 'serendipity'"
🔢 "What is sqrt(144) + 2^10?"
```

---

## �️ Project Structure

```
openwebui-tools/
├── main.py              ← FastAPI app (15+ tools)
├── requirements.txt     ← Python dependencies
├── Dockerfile           ← For Coolify / Docker deploy
├── docker-compose.yml   ← Local Docker testing
├── .env.example         ← Environment template
├── start.bat            ← One-click Windows starter
└── README.md            ← This file
```

---

## � Local Docker Test

```bash
docker-compose up --build
```

---

## 🔐 Security

The server uses **API Key authentication**. Set the `API_KEY` environment variable in Coolify, and add it as a Bearer token in your OpenWebUI Tool connection.

If `API_KEY` is empty, authentication is **disabled** (not recommended for public servers).

---

## 🙏 Made by

**Mohan Ram** — Built with ❤️ using FastAPI, hosted on Coolify.

---

## 📄 License

MIT — Feel free to fork and customize for your own OpenWebUI setup!
