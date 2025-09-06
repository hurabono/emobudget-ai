from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Plaid 카테고리를 앱 기준 카테고리로 매핑
PLAID_TO_APP_CATEGORIES = {
    "Food & Drink": "Restaurants",
    "Restaurants": "Restaurants",
    "Travel": "Travel",
    "Shops": "Shopping",
    "Groceries": "Shopping",
    # 필요한 항목 추가
}

@app.route("/analyze", methods=["POST"])
def analyze_spending():
    # Plaid 거래 데이터 받기
    transactions_json = request.get_json()
    df = pd.DataFrame(transactions_json)

    if df.empty:
        return jsonify({"analysis_result": "분석할 거래 내역이 없습니다."})

    # Plaid 카테고리를 앱 기준 카테고리로 변환
    df['category'] = df['category'].map(PLAID_TO_APP_CATEGORIES).fillna('Uncategorized')

    # 감정 소비 분석 (Shopping, Restaurants, 금액 >= 100)
    emotional_spending = df[
        (df['category'].isin(['Shopping', 'Restaurants'])) &
        (df['amount'] >= 100.0)
    ]

    if not emotional_spending.empty:
        count = len(emotional_spending)
        total_amount = emotional_spending['amount'].sum()
        analysis_result = f"총 {count}건의 감정 소비 패턴이 발견되었어요. (총액: ${total_amount:.2f})"
    else:
        analysis_result = "최근 감정 소비 패턴이 보이지 않아요. 잘하고 있어요!"

    # 전체 카테고리 통계도 함께 보내기 (프론트엔드용)
    category_summary = df.groupby('category')['amount'].sum().reset_index().to_dict(orient='records')

    return jsonify({
        "analysis_result": analysis_result,
        "category_summary": category_summary
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
