import os
import json
import base64
import re
import traceback
from flask import Flask, request, jsonify, render_template
from PIL import Image
import io

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_llm_provider():
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    google_key = os.environ.get("GOOGLE_API_KEY", "")

    # OpenAI keys always start with "sk-"
    if openai_key.startswith("sk-"):
        return "openai"
    # Google/Gemini keys always start with "AIza"
    if gemini_key.startswith("AIza"):
        return "gemini"
    if google_key.startswith("AIza"):
        return "google"
    # Fallback: use whichever is set
    if openai_key:
        return "openai"
    if gemini_key:
        return "gemini"
    return None


RECEIPT_PROMPT_SYSTEM = """You are a receipt data extraction API. Your sole job is to read receipt images and return structured JSON.

CRITICAL: You must respond with ONLY a raw JSON object. No markdown. No code fences. No ```json. No explanation. No text before or after the JSON. Just the JSON object itself, starting with { and ending with }.

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
- Your entire response must be valid JSON parseable by json.loads()"""

RECEIPT_PROMPT_USER = "Extract all data from this receipt image and return the JSON object."


def call_gemini(image_bytes, mime_type):
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=RECEIPT_PROMPT_SYSTEM,
    )
    image_part = {"mime_type": mime_type, "data": image_bytes}
    response = model.generate_content([RECEIPT_PROMPT_USER, image_part])
    raw = response.text
    print(f"[Gemini raw response]: {raw[:500]}")
    return raw


def call_openai(image_bytes, mime_type):
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Encode image as a proper base64 data URI
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64_image}"
    print(f"[OpenAI] Sending image: mime={mime_type}, b64_length={len(b64_image)}")

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},  # Force strict JSON output
        messages=[
            {
                "role": "system",
                "content": RECEIPT_PROMPT_SYSTEM,
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": RECEIPT_PROMPT_USER},
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url, "detail": "high"},
                    },
                ],
            },
        ],
        max_tokens=2000,
    )
    raw = response.choices[0].message.content
    print(f"[OpenAI raw response]: {raw[:500]}")
    return raw


def parse_llm_response(raw_text):
    text = raw_text.strip()
    # Strip any accidental markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()
    return json.loads(text)


@app.route("/")
def index():
    provider = get_llm_provider()
    return render_template("index.html", provider=provider)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not supported. Please upload a PNG, JPG, or WebP image."}), 400

    provider = get_llm_provider()
    if not provider:
        return jsonify({
            "error": "No AI API key configured. Please add GEMINI_API_KEY or OPENAI_API_KEY to your environment secrets."
        }), 500

    try:
        # Read the file once into bytes — do NOT call file.read() again after this
        image_bytes = file.read()
        print(f"[upload] Read {len(image_bytes)} bytes from upload, provider={provider}")

        if len(image_bytes) == 0:
            return jsonify({"error": "The uploaded file is empty. Please try again."}), 400

        # Validate it's actually an image using a BytesIO copy (does not touch image_bytes)
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
        except Exception as pil_err:
            print(f"[upload] PIL verify failed: {pil_err}")
            return jsonify({"error": "The uploaded file could not be read as an image. Please try a different file."}), 400

        ext = file.filename.rsplit(".", 1)[1].lower()
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        if provider in ("gemini", "google"):
            raw = call_gemini(image_bytes, mime_type)
        else:
            raw = call_openai(image_bytes, mime_type)

        data = parse_llm_response(raw)
        return jsonify({"success": True, "data": data})

    except json.JSONDecodeError as e:
        print(f"[upload] JSON parse error: {e}")
        return jsonify({"error": "The AI returned an unexpected format. Please try again."}), 500
    except Exception as e:
        error_msg = str(e)
        print(f"[upload] Exception: {error_msg}")
        traceback.print_exc()
        # Classify error for user-friendly messages
        lower = error_msg.lower()
        if "api_key" in lower or "api key" in lower or "authentication" in lower or "unauthorized" in lower:
            return jsonify({"error": "Invalid or missing API key. Please check your OPENAI_API_KEY secret."}), 500
        if "quota" in lower or "rate_limit" in lower or "rate limit" in lower or "429" in error_msg:
            return jsonify({"error": "API rate limit reached. Please wait a moment and try again."}), 429
        if "billing" in lower or "insufficient_quota" in lower:
            return jsonify({"error": "Your API account has no remaining credits. Please check your billing at platform.openai.com."}), 402
        return jsonify({"error": f"An unexpected error occurred. Check the server logs for details."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
