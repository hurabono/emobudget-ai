from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# ----------------------------
# Plaid API Configuration
# ----------------------------
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
PLAID_SECRET = os.environ.get("PLAID_SECRET")
PLAID_ENV = os.environ.get("PLAID_ENV", "sandbox")  # sandbox / development / production
ACCESS_TOKEN = os.environ.get("PLAID_ACCESS_TOKEN")

PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

# Plaid category mapping to your app categories
PLAID_TO_APP_CATEGORIES = {
    "Food & Drink": "Dining",
    "Restaurants": "Dining",
    "Shops": "Shopping",
    "Groceries": "Shopping",
    "Travel": "Travel",
    # add more as needed
}

# Sandbox fallback for testing
PLAID_NAME_TO_CATEGORY = {
    "Walmart": "Shopping",
    "Target": "Shopping",
    "Starbucks": "Dining",
    "McDonald's": "Dining",
    "Uber": "Travel",
}


# ----------------------------
# Helper: Fetch transactions from Plaid
# ----------------------------
def get_transactions_from_plaid(start_date="2025-08-01", end_date="2025-09-05"):
    url = f"{PLAID_BASE_URL}/transactions/get"
    headers = {"Content-Type": "application/json"}
    payload = {
        "client_id": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "access_token": ACCESS_TOKEN,
        "start_date": start_date,
        "end_date": end_date,
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    transactions = data.get("transactions", [])

    # Debug log
    print("=== Plaid Transactions ===")
    for t in transactions:
        print(t)

    return transactions


# ----------------------------
# Helper: Map categories and filter out Uncategorized
# ----------------------------
def categorize_transactions(transactions):
    categorized = []
    for tx in transactions:
        category_list = tx.get("category")
        if category_list:
            category = PLAID_TO_APP_CATEGORIES.get(category_list[0], "Uncategorized")
        else:
            category = PLAID_NAME_TO_CATEGORY.get(tx.get("name", ""), "Uncategorized")

        if category != "Uncategorized":
            categorized.append({
                "name": tx.get("name"),
                "amount": tx.get("amount", 0),
                "date": tx.get("date"),
                "category": category
            })
    return categorized


# ----------------------------
# API: Spending Analysis
# ----------------------------
@app.route("/api/analysis/spending-pattern")
def analyze_spending():
    transactions = get_transactions_from_plaid()
    categorized_transactions = categorize_transactions(transactions)

    if not categorized_transactions:
        return jsonify({
            "topCategory": None,
            "spendingByCategory": {},
            "analysis_result": "거래 내역이 없습니다."
        })

    # Calculate spending per category
    spending_by_category = {}
    for tx in categorized_transactions:
        cat = tx["category"]
        spending_by_category[cat] = spending_by_category.get(cat, 0) + tx["amount"]

    top_category = max(spending_by_category, key=spending_by_category.get)

    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": spending_by_category,
        "analysis_result": f"이번 달 가장 많이 지출한 카테고리는 '{top_category}' 입니다."
    })


# ----------------------------
# Run Flask
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
