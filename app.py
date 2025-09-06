from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# Plaid API 설정
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
PLAID_SECRET = os.environ.get("PLAID_SECRET")
PLAID_ENV = os.environ.get("PLAID_ENV", "sandbox")  # sandbox / development / production
ACCESS_TOKEN = os.environ.get("PLAID_ACCESS_TOKEN")
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

# Plaid 카테고리를 앱 기준 카테고리로 매핑
PLAID_TO_APP_CATEGORIES = {
    "Food & Drink": "Restaurants",
    "Restaurants": "Restaurants",
    "Travel": "Travel",
    "Shops": "Shopping",
    "Groceries": "Shopping",
}

# Sandbox 이름 기반 fallback (optional, for testing)
PLAID_NAME_TO_CATEGORY = {
    "Walmart": "Shopping",
    "Starbucks": "Restaurants",
    "Uber": "Travel",
    "McDonald's": "Restaurants",
    "Target": "Shopping",
}

def get_transactions_from_plaid():
    """Plaid API에서 실제 트랜잭션 가져오기"""
    url = f"{PLAID_BASE_URL}/transactions/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": ACCESS_TOKEN,
        "start_date": "2025-08-01",  # 필요에 맞게 설정
        "end_date": "2025-09-05",
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    transactions = data.get("transactions", [])

    # 로그 확인용
    print("=== Plaid Transactions ===")
    for t in transactions:
        print(t)

    return transactions

@app.route("/api/analysis/spending-pattern")
def analyze_spending():
    plaid_transactions = get_transactions_from_plaid()

    if not plaid_transactions:
        return jsonify({
            "topCategory": "Uncategorized",
            "spendingByCategory": {},
            "analysis_result": "거래 내역이 없습니다."
        })

    spending_by_category = {}
    emotional_spending_total = 0
    emotional_spending_count = 0

    for tx in plaid_transactions:
        # Plaid category 배열 가져오기
        plaid_category = tx.get("category")
        if plaid_category:
            category = PLAID_TO_APP_CATEGORIES.get(plaid_category[0], "Uncategorized")
        else:
            # Sandbox fallback by name
            category = PLAID_NAME_TO_CATEGORY.get(tx.get("name", ""), "Uncategorized")

        amount = tx.get("amount", 0)

        # 카테고리 합계
        spending_by_category[category] = spending_by_category.get(category, 0) + amount

        # 감정 소비 조건 (Shopping, Restaurants, amount >= 100)
        if category in ["Shopping", "Restaurants"] and amount >= 100:
            emotional_spending_total += amount
            emotional_spending_count += 1

    top_category = max(spending_by_category, key=lambda k: spending_by_category[k]) if spending_by_category else "Uncategorized"

    if emotional_spending_count > 0:
        analysis_result = f"총 {emotional_spending_count}건의 감정 소비 패턴이 발견되었어요. (총액: ${emotional_spending_total:.2f})"
    else:
        analysis_result = "최근 감정 소비 패턴이 보이지 않아요. 잘하고 있어요!"

    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": spending_by_category,
        "analysis_result": analysis_result
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
