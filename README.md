# 🔧 OpenWebUI Multi-Tool Server

A powerful OpenAPI-compatible tool server with **10 useful tools** — connects directly to **OpenWebUI → External Tools**.

---

## 🚀 Deploy on Coolify (Recommended)

### Step 1 — Push code to GitHub

Your project folder needs to be a GitHub repo. Run these commands once:

```bash
git init
git add .
git commit -m "Initial: OpenWebUI Multi-Tool Server"
git remote add origin https://github.com/YOUR_USERNAME/openwebui-tools.git
git push -u origin main
```

---

### Step 2 — Create a new Resource in Coolify

1. Open your **Coolify dashboard**
2. Go to **Projects → Your Project → + New Resource**
3. Select **"Application"**
4. Choose your **GitHub** as the source and select the `openwebui-tools` repo
5. Set build pack to **"Dockerfile"** (Coolify auto-detects it)

---

### Step 3 — Configure the Service

In the Coolify app settings:

| Setting | Value |
|---|---|
| **Branch** | `main` |
| **Build Pack** | Dockerfile |
| **Port** | `8765` |
| **Exposed Port** | `8765` (or any port you like) |
| **Healthcheck Path** | `/` |

Click **"Deploy"** — Coolify builds and starts your container automatically! ✅

---

### Step 4 — Set Up a Domain (Optional but Recommended)

1. In Coolify app settings → **Domains**
2. Add: `tools.yourdomain.com`
3. Enable **"HTTPS"** (Coolify handles Let's Encrypt automatically)
4. Click **Save & Redeploy**

Your tool server will be live at:
```
https://tools.yourdomain.com
```

---

### Step 5 — Connect to OpenWebUI

In **OpenWebUI → Admin → Settings → External Tools → + Add Connection**:

| Field | Value |
|---|---|
| **URL** | `https://tools.yourdomain.com` |
| **OpenAPI Spec URL** | `https://tools.yourdomain.com/openapi.json` |
| **Auth** | None |
| **Name** | `Multi-Tool Server` |

Click **Save** — done! 🎉

---

## 🖥️ Local Development (Windows)

```bash
# Install deps
pip install -r requirements.txt

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8765 --reload
```

Or just double-click `start.bat`

**Docs:** http://localhost:8765/docs  
**Spec:** http://localhost:8765/openapi.json

---

## 🐳 Test Docker Locally

```bash
docker-compose up --build
```

---

## 🛠️ Available Tools

| Endpoint | Tool | Description |
|---|---|---|
| `GET /time` | 🕐 Date & Time | Current time in any timezone |
| `GET /currency` | 💱 Currency Converter | Live exchange rates (USD → INR etc.) |
| `GET /ip-lookup` | 🌍 IP Lookup | Geolocation + ISP for any IP |
| `GET /text-analyze` | 📝 Text Analyzer | Word count, reading time, top words |
| `GET /qr-code` | 📱 QR Generator | Returns QR code image URL |
| `GET /hash` | 🔑 Hash Generator | MD5, SHA1, SHA256, SHA512 |
| `GET /math` | 🔢 Calculator | Safe math expression evaluator |
| `GET /fake-user` | 👤 Fake User | Random user profile for testing |
| `GET /url-info` | 🔗 URL Inspector | Title + meta info from any URL |
| `GET /define` | 📖 Dictionary | English word definitions + audio |

---

## � File Structure

```
openwebui-tools/
├── main.py              ← FastAPI app (all 10 tools)
├── requirements.txt     ← Python dependencies
├── Dockerfile           ← For Coolify / Docker deploy
├── docker-compose.yml   ← Local Docker testing
├── start.bat            ← One-click Windows starter
├── .gitignore
└── README.md
```

---

## 💬 Example Prompts After Connecting

- *"What time is it in IST right now?"*
- *"Convert 500 USD to INR"*
- *"Where is IP address 8.8.8.8 located?"*
- *"Generate a QR code for https://google.com"*
- *"What's the SHA256 of 'hello world'?"*
- *"Calculate sqrt(144) + 2^10"*
- *"Define the word 'ephemeral'"*
- *"Analyze this paragraph: [paste text]"*
