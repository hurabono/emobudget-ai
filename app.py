from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze_spending():
    transactions_json = request.get_json()
    df = pd.DataFrame(transactions_json)
    if df.empty:
        return jsonify({"analysis_result": "분석할 거래 내역이 없습니다."})
    
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
    
    return jsonify({"analysis_result": analysis_result})

# Render 배포용
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
