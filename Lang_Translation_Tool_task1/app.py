from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# MyMemory Translation API (Free, no API key required)
MYMEMORY_URL = "https://api.mymemory.translated.net/get"

LANGUAGES = {
    "auto": "Auto Detect",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese (Simplified)",
    "ar": "Arabic",
    "hi": "Hindi",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "uk": "Ukrainian",
    "bn": "Bengali",
    "ms": "Malay",
}


@app.route("/languages", methods=["GET"])
def get_languages():
    return jsonify(LANGUAGES)


@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    text = data.get("text", "").strip()
    source_lang = data.get("source_lang", "en")
    target_lang = data.get("target_lang", "es")

    if not text:
        return jsonify({"error": "Text cannot be empty"}), 400

    if source_lang == target_lang and source_lang != "auto":
        return jsonify({"error": "Source and target languages must be different"}), 400

    if len(text) > 5000:
        return jsonify({"error": "Text exceeds 5000 character limit"}), 400

    try:
        # Build language pair for MyMemory
        if source_lang == "auto":
            lang_pair = f"en|{target_lang}"
        else:
            lang_pair = f"{source_lang}|{target_lang}"

        params = {
            "q": text,
            "langpair": lang_pair,
        }

        response = requests.get(MYMEMORY_URL, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("responseStatus") == 200:
            translated_text = result["responseData"]["translatedText"]
            detected_lang = None

            # Try to get detected language from matches if auto
            if source_lang == "auto":
                matches = result.get("matches", [])
                for match in matches:
                    if match.get("source"):
                        detected_lang = match["source"]
                        break

            return jsonify({
                "translated_text": translated_text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "detected_lang": detected_lang,
                "char_count": len(text),
            })
        else:
            return jsonify({"error": "Translation service returned an error. Please try again."}), 502

    except requests.exceptions.Timeout:
        return jsonify({"error": "Translation request timed out. Please try again."}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to translation service. Check your internet connection."}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)