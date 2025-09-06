from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# Plaid API 설정
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
PLAID_SECRET = os.environ.get("PLAID_SECRET")
PLAID_ENV = "sandbox"  # 또는 "development", "production"
ACCESS_TOKEN = os.environ.get("PLAID_ACCESS_TOKEN")

PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

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

    # Plaid 트랜잭션 리스트 반환
    return data.get("transactions", [])

@app.route("/api/analysis/spending-pattern")
def analyze_spending():
    plaid_transactions = get_transactions_from_plaid()

    spending_by_category = {}
    for tx in plaid_transactions:
        # Plaid는 category 배열 반환, 없으면 'Uncategorized'
        category = tx.get("category", ["Uncategorized"])[0]
        amount = tx.get("amount", 0)
        spending_by_category[category] = spending_by_category.get(category, 0) + amount

    top_category = max(spending_by_category, key=lambda k: spending_by_category[k]) if spending_by_category else "Uncategorized"

    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": spending_by_category
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
