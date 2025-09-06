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
    "Entertainment": "Entertainment",
    "Health & Fitness": "Health",
}

# Sandbox 이름 기반 fallback
PLAID_NAME_TO_CATEGORY = {
    "Walmart": "Shopping",
    "Starbucks": "Restaurants",
    "Uber": "Travel",
    "McDonald's": "Restaurants",
    "Target": "Shopping",
}

def get_transactions_from_plaid():
    """Plaid API에서 트랜잭션 가져오기"""
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
    return transactions

def categorize_transactions(transactions):
    categorized = []
    for tx in transactions:
        category_list = tx.get("category", [])
        category = "Other"  # 기본값

        # 카테고리 배열 전체 확인
        for cat in category_list:
            if cat in PLAID_TO_APP_CATEGORIES:
                category = PLAID_TO_APP_CATEGORIES[cat]
                break

        # 이름 기반 fallback
        if category == "Other":
            category = PLAID_NAME_TO_CATEGORY.get(tx.get("name", ""), "Other")

        categorized.append({
            "name": tx.get("name"),
            "amount": tx.get("amount", 0),
            "date": tx.get("date"),
            "category": category
        })
    return categorized

@app.route("/api/analysis/spending-pattern")
def analyze_spending():
    plaid_transactions = get_transactions_from_plaid()
    transactions = categorize_transactions(plaid_transactions)

    if not transactions:
        return jsonify({
            "topCategory": "Other",
            "spendingByCategory": {},
            "analysis_result": "거래 내역이 없습니다."
        })

    spending_by_category = {}
    emotional_spending_total = 0
    emotional_spending_count = 0

    for tx in transactions:
        category = tx["category"]
        amount = tx["amount"]

        spending_by_category[category] = spending_by_category.get(category, 0) + amount

        if category in ["Shopping", "Restaurants"] and amount >= 100:
            emotional_spending_total += amount
            emotional_spending_count += 1

    top_category = max(spending_by_category, key=lambda k: spending_by_category[k])

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
