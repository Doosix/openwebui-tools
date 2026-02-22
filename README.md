# 🚀 OpenWebUI Ultimate-Tool Server

> **20+ AI-powered tools** for OpenWebUI — Search, Stocks, Crypto, News, Translate, YouTube, Weather, and more. Built with FastAPI, deployed on Coolify.

[![Version](https://img.shields.io/badge/Version-5.0.0-blue)](https://github.com/Doosix/openwebui-tools)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🛠️ What Is This?

A self-hosted **OpenAPI-compatible tool server** that gives your AI real-time superpowers inside **OpenWebUI**. Your AI can search the web, check stocks, translate languages, get weather, read YouTube videos, and much more — all in one chat!

---

## ⚡ Quickstart

```bash
git clone https://github.com/Doosix/openwebui-tools.git
cd openwebui-tools
pip install -r requirements.txt
echo API_KEY=your_secret > .env
python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload
```

📄 Docs: `http://localhost:8765/docs` | OpenAPI Spec: `http://localhost:8765/openapi.json`

---

## ☁️ Deploy on Coolify

1. Push to GitHub → Connect repo in Coolify
2. Build Pack: `Dockerfile` | Port: `8765`
3. Add env var: `API_KEY` = your secret
4. Deploy ✅

---

## 🔌 Connect to OpenWebUI

| Field | Value |
|---|---|
| **URL** | `https://your-domain.com` |
| **OpenAPI Spec** | `https://your-domain.com/openapi.json` |
| **Headers** | `{"Authorization": "Bearer your_api_key"}` |

---

## 🔧 All 20+ Tools

### 🔍 Search & Web
| Tool | Endpoint | What It Does |
|---|---|---|
| Web Search | `/search` | Live DuckDuckGo search |
| Latest News | `/news` | Headlines on any topic |
| Web Scraper | `/scrape` | Clean text from any URL |
| Wikipedia | `/wiki` | Wikipedia summaries |

### 💰 Finance
| Tool | Endpoint | What It Does |
|---|---|---|
| Currency | `/currency` | Live exchange rates (₹$€£) |
| Crypto | `/crypto` | Bitcoin, ETH, DOGE prices |
| Stock Price | `/stock` | Live stock prices + changes |

### 🎬 Media
| Tool | Endpoint | What It Does |
|---|---|---|
| YouTube Transcript | `/youtube/transcript` | Full text from any video |

### 🌦️ Utilities
| Tool | Endpoint | What It Does |
|---|---|---|
| Weather | `/weather` | Current + 3-day forecast |
| Date & Time | `/time` | Any timezone |
| Unit Converter | `/convert/units` | km/mi, kg/lb, °C/°F, L/gal |
| QR Code | `/qr-code` | Generate QR for text/URL |
| Math Calculator | `/math` | Safe expression evaluator |
| Translate | `/translate` | 50+ languages via MyMemory |

### 🔐 Security
| Tool | Endpoint | What It Does |
|---|---|---|
| Password | `/password` | Secure random passwords |
| Hash | `/hash` | MD5, SHA1, SHA256, SHA512 |

### 🌍 Network
| Tool | Endpoint | What It Does |
|---|---|---|
| IP Lookup | `/ip-lookup` | Geolocation + ISP |
| Domain Info | `/domain-info` | WHOIS registration details |
| DNS Lookup | `/dns-lookup` | Resolve domain to IPs |

### 📝 Text & Data
| Tool | Endpoint | What It Does |
|---|---|---|
| Text Analyzer | `/text-analyze` | Word count, reading time |
| Dictionary | `/define` | Definitions + phonetics |
| Fake User | `/fake-user` | Random test profile |

---

## 💬 Example Prompts

```
🔍 "Search the web for latest AI news"
📰 "What are the latest news headlines about India?"
📊 "What is Apple stock price right now?" (AAPL)
� "Get Reliance stock price" (RELIANCE.NS)
🪙 "What is Bitcoin price in INR?"
💱 "Convert 1000 USD to INR"
� "Translate 'hello world' to Tamil"
📺 "Summarize this YouTube video: [URL]"
🌤️ "Weather in Mumbai (lat: 19.07, lon: 72.87)"
📐 "Convert 100°F to Celsius"
🔑 "Generate a 24-character password"
📚 "Wikipedia: Elon Musk"
🌍 "Where is IP 1.1.1.1?"
� "DNS lookup for github.com"
🌐 "Domain info for google.com"
📖 "Define 'serendipity'"
```

---

## 🗂️ Project Structure

```
openwebui-tools/
├── main.py              ← FastAPI app (20+ tools)
├── requirements.txt     ← Python dependencies
├── Dockerfile           ← Docker / Coolify deploy
├── docker-compose.yml   ← Local Docker testing
├── .env.example         ← Environment template
├── start.bat            ← Windows quick start
└── README.md            ← This file
```

---

## 🙏 Made by **Mohan Ram** — Built with ❤️ using FastAPI

📄 License: MIT
