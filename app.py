from flask import Flask, jsonify, request
from flask_cors import CORS  # ✅ Must import CORS
import os
import pandas as pd
import joblib
from datetime import datetime

# -------------------------
# 0. Flask app setup
# -------------------------
app = Flask(__name__)
CORS(app)  # Allow all domains (dev only)

# -------------------------
# 1. Load trained model
# -------------------------
MODEL_PATH = "emotional_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
    print("✅ Emotional spending model loaded successfully.")
except Exception as e:
    print("⚠️ Model not found or failed to load:", e)
    model = None

# -------------------------
# 2. Category mapping
# -------------------------
PLAID_TO_APP_CATEGORIES = {
    "Food and Drink": "Restaurants",
    "Restaurants": "Restaurants",
    "Travel": "Travel",
    "Shops": "Shopping",
    "Groceries": "Shopping",
    "Entertainment": "Entertainment",
    "Health & Fitness": "Health",
}

PLAID_NAME_TO_CATEGORY = {
    "Walmart": "Shopping",
    "Starbucks": "Restaurants",
    "Uber": "Travel",
    "McDonald's": "Restaurants",
    "Target": "Shopping",
}

# -------------------------
# 3. Helper function
# -------------------------
def categorize_transactions(transactions):
    categorized = []
    for tx in transactions:
        category_list = tx.get("category", [])
        category = "Other"
        for cat in category_list:
            if cat in PLAID_TO_APP_CATEGORIES:
                category = PLAID_TO_APP_CATEGORIES[cat]
                break
        if category == "Other":
            category = PLAID_NAME_TO_CATEGORY.get(tx.get("name", ""), "Other")
        dt_object = datetime.fromisoformat(tx.get("date") + "T12:00:00")
        categorized.append({
            "name": tx.get("name"),
            "amount": tx.get("amount", 0),
            "date": tx.get("date"),
            "datetime": dt_object,
            "category": category
        })
    return categorized

# -------------------------
# 4. Predict single transaction emotion
# -------------------------
@app.route("/predict_emotion", methods=["POST"])
def predict_emotion():
    if not model:
        return jsonify({"error": "Model not available"}), 500

    tx = request.json
    if not tx:
        return jsonify({"error": "No transaction data provided"}), 400

    # Convert to DataFrame
    df = pd.DataFrame([tx])

    # One-hot encoding (match training columns)
    df = pd.get_dummies(df)
    for col in model.feature_names_in_:
        if col not in df:
            df[col] = 0
    df = df[model.feature_names_in_]

    # Prediction
    prob = model.predict_proba(df)[0][1]
    pred = model.predict(df)[0]

    return jsonify({
        "is_emotional": int(pred),
        "probability": round(prob, 3)
    })

# -------------------------
# 5. Analyze multiple transactions
# -------------------------
@app.route("/analyze_transactions", methods=["POST"])
def analyze_transactions_endpoint():
    transactions_json = request.json
    if not transactions_json:
        return jsonify({
            "topCategory": "None",
            "spendingByCategory": {},
            "analysis_insights": ["거래 내역이 없습니다."]
        }), 200

    transactions = categorize_transactions(transactions_json)
    df = pd.DataFrame(transactions)
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Total spending by category
    spending_by_category = df[df['amount'] > 0].groupby('category')['amount'].sum().to_dict()
    top_category = max(spending_by_category, key=spending_by_category.get, default="None")

    insights = ["간단한 분석 예시: 이번 달 {} 지출이 많습니다.".format(top_category)]

    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": {k: round(v, 2) for k, v in spending_by_category.items()},
        "analysis_insights": insights
    })

# -------------------------
# 6. Simple test endpoint
# -------------------------
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})

# -------------------------
# 7. Run server
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
