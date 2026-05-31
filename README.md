# Receipt to Spreadsheet

An AI-powered web app that turns any receipt photo into a clean, structured spreadsheet in seconds. Upload a PNG, JPG, or WebP receipt image — the app uses OpenAI GPT-4o Vision (or Google Gemini) to extract every line item, quantity, price, subtotal, tax, and total, then displays it in a formatted table you can copy as CSV, download as `.xlsx`, or browse from a persistent scan history sidebar.

---

## Project Overview & Tech Stack

### What it does

1. User drags and drops (or browses for) a receipt image.
2. The Flask backend reads the image, base64-encodes it, and sends it to the Vision LLM with a strict system prompt that forces clean JSON output.
3. The LLM returns a structured object: vendor, date, line items (name, qty, unit price), subtotal, tax, total, and currency.
4. The frontend renders the data in a styled table with three export options: **Copy CSV**, **Download Excel** (SheetJS, browser-side), and **Scan History** (localStorage, persists across sessions).

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3 |
| AI Vision | OpenAI GPT-4o (primary) · Google Gemini 1.5 Flash (fallback) |
| Frontend | Vanilla HTML5 + Tailwind CSS (CDN) + Vanilla JavaScript |
| Excel Export | SheetJS `xlsx` (CDN — runs in the browser, zero server round-trip) |
| Persistence | Browser `localStorage` — up to 25 receipts, multi-sheet bulk export |
| Image Validation | Pillow |

No database. No build step. No frontend framework. Starts with a single Python command.

---

## Quick Start

### Option A — Run on Replit (under 2 minutes)

1. **Fork** this Repl or open it directly in Replit.
2. Click the **Secrets** tab (🔒 in the left sidebar) and add one of:
   - `OPENAI_API_KEY` — get one free at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - `GEMINI_API_KEY` — get one free at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) (no credit card)
3. Click **Run** — Flask starts automatically on port 5000.
4. Open the **Webview** tab and upload a receipt photo.

> **Tip:** The app auto-detects which key you've added by its format (`sk-…` = OpenAI, `AIza…` = Gemini), so you can't accidentally mix them up.

---

### Option B — Run Locally (under 5 minutes)

**Requirements:** Python 3.10 or higher.

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd <repo-folder>

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r artifacts/receipt-to-spreadsheet/requirements.txt

# 4. Export your API key
export OPENAI_API_KEY="sk-..."    # or: export GEMINI_API_KEY="AIza..."
# Windows: set OPENAI_API_KEY=sk-...

# 5. Start the server
cd artifacts/receipt-to-spreadsheet
python app.py
```

6. Open [http://localhost:5000](http://localhost:5000) in your browser.
7. Drop a receipt image on the upload area and click **Analyze Receipt**.

The server logs will print the raw LLM response and any errors to the terminal, so you can debug directly without guessing.

---

## Prompts Used

This section documents the exact prompts that drove the development of this app, showing the full human–AI conversation used to build it from scratch.

---

### Prompt 1 — Initial build

> Build a full-stack web application called "Receipt to Spreadsheet".
>
> **Stack Requirements:**
> - Backend: Python (Flask)
> - Frontend: Modern HTML, Tailwind CSS, and vanilla JavaScript. No heavy frontend frameworks like React to keep deployment instant and fast to load.
>
> **Core Features to Build:**
> 1. A clean web page with a drag-and-drop file upload area for receipt images (PNG, JPG).
> 2. A backend route that receives the image and sends it to a Vision LLM API (like Google Gemini or OpenAI GPT-4o) using official SDKs.
> 3. The prompt to the Vision LLM must strictly request a structured JSON response containing: vendor, date, line_items (an array of objects with item_name, quantity, and price), total, and currency.
> 4. Parse this JSON on the backend and return it to the frontend.
> 5. Display the parsed data on the web page in a beautifully styled, highly readable Tailwind CSS table.
>
> **UX Requirements:**
> - Include an empty state showing a placeholder graphic before any receipt is uploaded.
> - Show a smooth, animated loading spinner with text (e.g., "Analyzing your receipt...") while waiting for the API response.
> - Gracefully catch any API failures or unreadable images and display a friendly error message to the user instead of letting the app crash.

---

### Prompt 2 — Excel export + first README

> Yes, add the "Download as Excel" button.
>
> Once that is implemented, please completely write (or update) the README.md file for this project. To make sure it passes the assignment review filters, the README must include:
> 1. Project Overview: A brief explanation of what the app does and the tech stack used.
> 2. Quick Start: Clear, step-by-step instructions on how someone can clone this repo and run it locally or on Replit in under 5 minutes.
> 3. The Prompts Used: A dedicated section where you paste the exact prompts we used to build this app from scratch.
> 4. Future Roadmap: A thoughtful section outlining 3 things we would build next if we had more time.

---

### Prompt 3 — API key fix

> The key I sent you was an OpenAI API key — fix that.

*(The GEMINI_API_KEY secret had been populated with an OpenAI key by mistake. The fix: detect key format by prefix — `sk-…` routes to OpenAI, `AIza…` routes to Gemini — so the app self-corrects regardless of which secret name is used.)*

---

### Prompt 4 — Debugging the image pipeline

> It says this error: "The AI could not read this receipt. Please try a clearer image."
>
> 1. Verify how the image is being encoded and sent to the OpenAI Vision API. Ensure it uses the correct format (e.g., base64 data URI structure for GPT-4o).
> 2. Check the raw response from OpenAI. If it's an API authentication error, a rate limit, or an unexpected JSON parsing error, print the exact error to the console logs so we can see it.
> 3. Make sure the system prompt explicitly forces the model to strictly output clean JSON without any markdown formatting (like \`\`\`json ... \`\`\` blocks), which often breaks standard JSON parsers. Fix the underlying error.

*(Root cause: a second `file.read()` call after the stream was already exhausted was replacing valid image bytes with empty `b""`. OpenAI received a blank image. Fix: read once, validate with a `BytesIO` copy, never re-read the stream.)*

---

### Prompt 5 — Scan history sidebar + this README

> Yes, add the scan history sidebar using localStorage.
>
> Once that feature is live, write a comprehensive README.md file for this project. To ensure it passes the Solution25 review filters, the README must include:
> 1. Project Overview & Tech Stack: A quick summary of what the app does.
> 2. Quick Start: Clear, idiot-proof instructions on how a reviewer can clone/fork this repo and run it locally or on Replit in under 5 minutes.
> 3. Prompts Used: A dedicated section where you list the exact core prompts we used to build this app from scratch to show our work.
> 4. Future Roadmap: A list of 3 things we would add with more time.

---

### Vision LLM System Prompt (sent to GPT-4o / Gemini at runtime)

```
You are a receipt data extraction API. Your sole job is to read receipt images
and return structured JSON.

CRITICAL: You must respond with ONLY a raw JSON object. No markdown. No code
fences. No ```json. No explanation. No text before or after the JSON. Just the
JSON object itself, starting with { and ending with }.

The JSON must have exactly this structure:
{
  "vendor": "string — store or restaurant name",
  "date": "string — date on receipt in YYYY-MM-DD format if possible, else as printed",
  "line_items": [
    {
      "item_name": "string",
      "quantity": number,
      "price": number
    }
  ],
  "subtotal": number or null,
  "tax": number or null,
  "total": number,
  "currency": "string — ISO 4217 code (USD, EUR, GBP, JPY, etc.) or best guess from symbol"
}

Rules:
- All numeric values must be plain numbers, never strings (4.99 not "$4.99")
- If quantity is not shown for an item, default to 1
- If a field cannot be determined, use null
- Include every line item visible on the receipt
- Your entire response must be valid JSON parseable by json.loads()
```

---

## Future Roadmap

With more time, these are the three highest-impact features we'd build next:

### 1. Automated Multi-Currency Conversion

Receipts come in dozens of currencies. We'd integrate a live exchange-rate API (e.g., the free ECB daily feed or Open Exchange Rates) so every amount is shown in both its original currency and the user's chosen home currency. A sticky settings bar would let users pick their base currency, and all totals across the history sidebar would roll up into a single unified figure — turning the app into a complete travel-expense tracker without any manual entry.

### 2. User Accounts & Cloud Sync (Replit Auth + PostgreSQL)

Right now, history lives in `localStorage` — it's device-specific and lost if the browser cache is cleared. Adding Replit Auth (one-click OAuth) plus a PostgreSQL database would let users access their full receipt history from any device. The schema is simple: a `users` table, a `scans` table with the extracted JSON blob, and an index on `user_id + scanned_at`. The scan history sidebar would load from the API instead of `localStorage`, with offline-first caching as a progressive enhancement.

### 3. Direct Google Sheets Integration

A one-click **"Send to Google Sheets"** button would use the Google Sheets API (OAuth 2.0) to append every line item to a designated spreadsheet — one tab per receipt, named by vendor and date. Power users could connect a Google Drive folder so the app watches for new receipt images and processes them automatically, enabling fully hands-free bookkeeping. This pairs naturally with feature 2 (user accounts) to store each user's connected Sheets ID securely server-side.
