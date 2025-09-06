from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# Plaid API 설정
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
PLAID_SECRET = os.environ.get("PLAID_SECRET")
PLAID_ENV = os.environ.get("PLAID_ENV", "sandbox")
ACCESS_TOKEN = os.environ.get("PLAID_ACCESS_TOKEN")
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

# Plaid → 앱 카테고리 매핑
PLAID_TO_APP_CATEGORIES = {
    "Food & Drink": "Restaurants",
    "Restaurants": "Restaurants",
    "Travel": "Travel",
    "Shops": "Shopping",
    "Groceries": "Shopping",
}

# Sandbox 이름 → 카테고리 매핑 (필수)
PLAID_NAME_TO_CATEGORY = {
    "Walmart": "Shopping",
    "Starbucks": "Restaurants",
    "Uber": "Travel",
    "McDonald's": "Restaurants",
    "Target": "Shopping",
}

def get_transactions_from_plaid():
    url = f"{PLAID_BASE_URL}/transactions/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": ACCESS_TOKEN,
        "start_date": "2025-08-01",
        "end_date": "2025-09-05",
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    transactions = data.get("transactions", [])

    print("=== Plaid Transactions ===")
    for t in transactions:
        print(t)

    return transactions

@app.route("/api/analysis/spending-pattern")
def analyze_spending():
    transactions = get_transactions_from_plaid()
    if not transactions:
        return jsonify({
            "topCategory": "Uncategorized",
            "spendingByCategory": {},
            "analysis_result": "거래 내역이 없습니다."
        })

    spending_by_category = {}
    emotional_total = 0
    emotional_count = 0

    for tx in transactions:
        name = tx.get("name", "")
        amount = tx.get("amount", 0)

        # Plaid category 있으면 매핑, 없으면 이름 기반 fallback, 없으면 Uncategorized
        if tx.get("category"):
            category = PLAID_TO_APP_CATEGORIES.get(tx["category"][0], "Uncategorized")
        elif name in PLAID_NAME_TO_CATEGORY:
            category = PLAID_NAME_TO_CATEGORY[name]
        else:
            category = "Uncategorized"

        # 카테고리별 합계
        spending_by_category[category] = spending_by_category.get(category, 0) + amount

        # 감정 소비
        if category in ["Shopping", "Restaurants"] and amount >= 100:
            emotional_total += amount
            emotional_count += 1

    # 가장 많이 쓴 카테고리
    top_category = max(spending_by_category, key=spending_by_category.get) if spending_by_category else "Uncategorized"

    analysis_result = (
        f"총 {emotional_count}건의 감정 소비 패턴이 발견되었어요. (총액: ${emotional_total:.2f})"
        if emotional_count > 0 else
        "최근 감정 소비 패턴이 보이지 않아요. 잘하고 있어요!"
    )

    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": spending_by_category,
        "analysis_result": analysis_result
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
