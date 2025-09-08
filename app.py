# app.py
from flask import Flask, jsonify, request
import os
import requests

app = Flask(__name__)

# Plaid API 설정
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
PLAID_SECRET = os.environ.get("PLAID_SECRET")
PLAID_ENV = os.environ.get("PLAID_ENV", "sandbox")
ACCESS_TOKEN = os.environ.get("PLAID_ACCESS_TOKEN")
PLAID_BASE_URL = f"https://{PLAID_ENV}.plaid.com"

PLAID_TO_APP_CATEGORIES = {
    "Food & Drink": "Restaurants",
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
        categorized.append({
            "name": tx.get("name"),
            "amount": tx.get("amount", 0),
            "date": tx.get("date"),
            "category": category
        })
    return categorized

@app.route("/analyze", methods=["POST"])
def analyze_transactions():
    transactions = request.json
    if not transactions:
        return jsonify({"topCategory": "None", "spendingByCategory": {}, "analysis_result": "No transactions"}), 200

    transactions = categorize_transactions(transactions)

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

    top_category = max(spending_by_category, key=lambda k: spending_by_category[k], default="None")

    if emotional_spending_count > 0:
        analysis_result = f"총 {emotional_spending_count}건의 감정 소비 패턴이 발견되었습니다. (총액: ${emotional_spending_total:.2f})"
    else:
        analysis_result = "최근 감정 소비 패턴이 보이지 않습니다."

    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": spending_by_category,
        "analysis_result": analysis_result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
