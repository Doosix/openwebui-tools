# � OpenWebUI Super-Tool Server V2

Now with **YouTube Transcripts**, **Advanced Scraping**, **Weather**, and **Security**!

---

## �️ V2 Improvement: Security (API Key)

To keep your server private, we've added API Key support.

### 1. Set the Key in Coolify
1. Go to your **Coolify App Settings** → **Environment Variables**.
2. Add a new variable:
   - **Key:** `API_KEY`
   - **Value:** `your-super-secret-password-here`
3. Click **Save** and **Redeploy**.

### 2. Configure OpenWebUI
In **OpenWebUI → External Tools → Connection Settings**:
1. Find the **"Headers"** or **"Auth"** section.
2. Set **Bearer Token** to your API key, or add a Header:
   - `Authorization: Bearer your-super-secret-password-here`

---

## � New Power Tools in V2

| Tool | What it does | Example Prompt |
|---|---|---|
| 📺 **YouTube** | Fetches the full text transcript of any video | *"Can you summarize this YouTube video: [URL]"* |
| 🕵️ **Scraper** | Extracts clean text/articles from any webpage | *"Read this article and tell me the main points: [URL]"* |
| 🌤️ **Weather** | Live weather and 3-day forecast | *"What is the weather in Bangalore?"* |

---

## � How to Update Your Deploy

Since your Coolify is linked to GitHub, just run these commands on your computer:

```bash
git add .
git commit -m "Upgrade to V2: Security, YouTube, Scraper, Weather"
git push origin main
```

Coolify will see the update and **automatically rebuild** your server! 🚀

---

## 🛠️ Local Setup

1. **Install new tools:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Create a `.env` file:**
   ```
   API_KEY=your_test_key
   ```
3. **Start:** `python main.py`

---

## 💬 Try These New Prompts!

- *"Summarize this YouTube video: https://www.youtube.com/watch?v=VIDEO_ID"*
- *"Read this news article and tell me what happened: https://thehindu.com/article/123"*
- *"What is the forecast for my location (Lat: 13, Lon: 77)?"*
- *"Convert 100 USD to INR"*
