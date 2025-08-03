from flask import Flask, request, jsonify
import joblib
import re,json, logging
import pandas as pd
from sentence_transformers import SentenceTransformer
from urllib.parse import urlparse
from scipy.sparse import csr_matrix, hstack
import numpy as np
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

print("🔄 Loading models...")
email_model = joblib.load("phishing_model.joblib")
url_model = joblib.load("url_phishing_model.joblib")
embedder = joblib.load("sentence_embedder.joblib")
sender_columns = joblib.load("sender_columns.joblib")
scaler = StandardScaler()  # used later for URL features
print("✅ Models loaded successfully.")

# === Helper Functions ===
def preprocess_text(text):
    if isinstance(text, str):
        text = text.lower()
        return ''.join(c for c in text if c.isalnum() or c == ' ')
    return ''

def extract_domain(sender):
    try:
        email = re.search(r'<(.+?)>', sender)
        domain = email.group(1).split('@')[-1] if email else ''
        return domain.lower()
    except:
        return ''

def extract_url_features(url):
    try:
        parsed = urlparse("http://" + str(url))
        domain = parsed.netloc.lower()
    except:
        domain = ''
    return [
        len(str(url)),
        sum(c.isdigit() for c in str(url)),
        sum(str(url).count(c) for c in ['-', '@', '?', '&', '=', '_', '%', '/']),
        1 if re.search(r'\d+\.\d+\.\d+\.\d+', str(url)) else 0,
        len(domain.split('.')[-1]) if '.' in domain else 0
    ]

def log_prediction(data, prediction):
    try:
        log_data = {
            "sender": data.get("sender", ""),
            "receiver": data.get("receiver", ""),
            "subject": data.get("subject", ""),
            "body": data.get("body", "")[:100],
            "label": prediction.get("email_prediction", 0),
        }

        with open("all_predictions_log.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data) + "\n")

        logging.info("📥 Email logged successfully.")
    except Exception as e:
        logging.warning("⚠️ Failed to log prediction: %s", str(e))

# === Main Prediction Route ===
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        print("\n📩 Received email for phishing check.")
        print(f"📨 Subject: {data.get('subject')}")
        print(f"🧾 Sender: {data.get('sender')}")
        print(f"🔗 URLs: {data.get('urls', [])}")

        subject = data.get("subject", "")
        body = data.get("body", "")
        sender = data.get("sender", "")
        urls = data.get("urls", [])
        attachments = data.get("attachments", [])

        # --- Email Classification ---
        full_text = (subject or "") + " " + (body or "")
        cleaned = preprocess_text(full_text)
        print(f"🧹 Cleaned text: {cleaned[:80]}...")

        text_embed = embedder.encode([cleaned])
        text_sparse = csr_matrix(text_embed)

        sender_domain = extract_domain(sender)
        print(f"📧 Extracted domain: {sender_domain}")

        sender_vector = [1 if col == sender_domain else 0 for col in sender_columns]
        sender_sparse = csr_matrix([sender_vector])

        combined_features = hstack([text_sparse, sender_sparse])
        email_pred = int(email_model.predict(combined_features)[0])
        email_conf = float(email_model.predict_proba(combined_features)[0][email_pred])

        print(f"📊 Email prediction: {'Phishing' if email_pred == 1 else 'Safe'} ({email_conf:.4f})")

        # --- URL Classification ---
        url_results = []
        for url in urls:
            features = extract_url_features(url)
            features_scaled = scaler.fit_transform([features])
            pred = int(url_model.predict(features_scaled)[0])
            conf = float(url_model.predict_proba(features_scaled)[0][pred])
            print(f"🔍 URL: {url} ➜ {'Phishing' if pred == 1 else 'Safe'} ({conf:.4f})")
            url_results.append({
                "url": url,
                "prediction": pred,
                "confidence": round(conf, 4)
            })

        result = {
            "email_prediction": email_pred,
            "email_confidence": round(email_conf, 4),
            "url_results": url_results
        }
        log_prediction(data, result)


        print("✅ Prediction complete.\n")
        return jsonify(result)

    except Exception as e:
        print(f"❌ Error during prediction: {str(e)}\n")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Starting phishing detection API on port 5000...")
    app.run(debug=True, port=5000)
