from flask import Flask, request, jsonify
import pandas as pd

# Flask 앱 생성
app = Flask(__name__)

# 헬스체크용 루트
@app.route("/")
def hello():
    return "AI 서버가 정상적으로 작동 중입니다!"

# POST /analyze 엔드포인트
@app.route("/analyze", methods=["POST"])
def analyze_spending():
    # JSON 데이터 가져오기
    transactions_json = request.get_json()

    # Pandas DataFrame으로 변환
    df = pd.DataFrame(transactions_json)

    # 데이터가 비어있으면 바로 리턴
    if df.empty:
        return jsonify({"analysis_result": "분석할 거래 내역이 없습니다."})

    # 간단한 감정 소비 분석
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

    # 결과 JSON 반환
    return jsonify({"analysis_result": analysis_result})

# 로컬 테스트용
if __name__ == "__main__":
    app.run(debug=True)
