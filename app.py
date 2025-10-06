from flask import Flask, jsonify, request
from datetime import datetime
import os

app = Flask(__name__)

# 감정 소비로 간주될 수 있는 카테고리 목록 (USD 기준)
EMOTIONAL_SPENDING_CATEGORIES = [
    "FOOD_AND_DRINK",
    "SHOPS", 
    "TRAVEL", 
    "ENTERTAINMENT", 
]

def analyze_transactions(transactions):
    if not transactions:
        return {
            "topCategory": "None",
            "spendingByCategory": {},
            "emotionalSpendingPattern": "No transactions available for analysis. "
        }

    spending_by_category = {}
    emotional_spending_events = []

    for tx in transactions:
        category = tx.get("category", "Uncategorized")
        amount = tx.get("amount", 0)
        if amount > 0:
            spending_by_category[category] = spending_by_category.get(category, 0) + amount

        tx_time_str = tx.get("transactionTime")
        tx_time = datetime.fromisoformat(tx_time_str) if tx_time_str else None

        if tx_time:
            # Rule 1: Late-night spending
            is_late_night = 22 <= tx_time.hour or tx_time.hour < 2
            is_delivery_or_taxi = "FOOD_AND_DRINK" in category or "TRAVEL" in category
            if is_late_night and is_delivery_or_taxi and amount > 15:
                emotional_spending_events.append(
                    f"{tx_time.strftime('%m/%d %H:%M')} — {tx.get('name')} ${amount:,.2f} (late-night spending)"
                )

            # 규칙 2: 주말 쇼핑
            is_weekend = tx_time.weekday() >= 5
            is_shopping = "SHOPS" in category
            if is_weekend and is_shopping and amount >= 50:
                emotional_spending_events.append(
                    f"{tx_time.strftime('%m/%d')} — {tx.get('name')} ${amount:,.2f} (weekend impulse purchase suspected)"
                )

    # --- for문 끝난 뒤 결과 정리 ---
    top_category = max(spending_by_category, key=spending_by_category.get, default="None")

    if emotional_spending_events:
        analysis_result = f"Detected {len(emotional_spending_events)} emotional-spending pattern(s).\n"
        analysis_result += "\n".join(f"- {event}" for event in emotional_spending_events)
    else:
        analysis_result = "No emotional-spending patterns detected. You’re maintaining healthy spending habits!"

    return {
        "topCategory": top_category,
        "spendingByCategory": spending_by_category,
        "emotionalSpendingPattern": analysis_result
    }

# ✅ 함수 밖에서 라우트 정의
@app.route("/analyze", methods=["POST"])
def handle_analyze_request():
    transactions = request.json
    analysis_result = analyze_transactions(transactions)
    return jsonify(analysis_result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
