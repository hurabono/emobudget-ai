from flask import Flask, jsonify, request
import os
import pandas as pd
import joblib
from datetime import datetime, timedelta

app = Flask(__name__)

CORS(app)  # 모든 도메인 허용 (개발용)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    

    amount = data.get('amount', 0)
    is_emotional = amount > 100  # 단순 예시
    probability = min(amount / 500, 1)

    result = {
        "is_emotional": is_emotional,
        "probability": probability
    }
    return jsonify(result)

# -------------------------
# 1. 학습된 모델 불러오기
# -------------------------
MODEL_PATH = "emotional_model.pkl"
try:
    model = joblib.load(MODEL_PATH)
    print("✅ Emotional spending model loaded successfully.")
except Exception as e:
    print("⚠️ Model not found or failed to load:", e)
    model = None

# -------------------------
# 2. 카테고리 매핑
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
# 3. 유틸 함수
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
# 4. 감정 소비 예측 API
# -------------------------
@app.route("/predict_emotion", methods=["POST"])
def predict_emotion():
    """
    단일 거래를 받아 감정소비 여부와 확률을 반환합니다.
    예시 입력:
    {
      "amount": 20,
      "hour": 23,
      "day_of_week": 5,
      "category": "Shopping"
    }
    """
    if not model:
        return jsonify({"error": "Model not available"}), 500

    tx = request.json
    if not tx:
        return jsonify({"error": "No transaction data provided"}), 400

    # DataFrame 변환
    df = pd.DataFrame([tx])

    # 카테고리 원핫 인코딩 (훈련 시 사용한 컬럼과 맞추기)
    df = pd.get_dummies(df)
    for col in model.feature_names_in_:
        if col not in df:
            df[col] = 0
    df = df[model.feature_names_in_]

    # 예측
    prob = model.predict_proba(df)[0][1]  # 감정소비 확률
    pred = model.predict(df)[0]

    return jsonify({
        "is_emotional": int(pred),
        "probability": round(prob, 3)  # 소수점 3자리 (예: 0.823 → 82.3%)
    })

# -------------------------
# 5. 전체 거래 분석 API (기존 분석)
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze_transactions_endpoint():
    """
    거래 내역 리스트를 받아 카테고리별 집계 및 간단한 인사이트를 반환합니다.
    """
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

    # 카테고리별 총 지출
    spending_by_category = df[df['amount'] > 0].groupby('category')['amount'].sum().to_dict()
    top_category = max(spending_by_category, key=spending_by_category.get, default="None")

    insights = ["간단한 분석 예시: 이번 달 {} 지출이 많습니다.".format(top_category)]

    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": {k: round(v, 2) for k, v in spending_by_category.items()},
        "analysis_insights": insights
    })

# -------------------------
# 6. 서버 실행
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
