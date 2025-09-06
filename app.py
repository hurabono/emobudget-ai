from flask import Flask, request, jsonify
import pandas as pd

# Flask 앱 생성
app = Flask(__name__)

# POST /analyze 엔드포인트 정의
@app.route("/analyze", methods=["POST"])
def analyze_spending():
    # Java 서버로부터 받은 거래 내역 JSON 데이터를 가져옵니다.
    transactions_json = request.get_json()
    
    # JSON 데이터를 Pandas DataFrame으로 변환 (데이터 분석에 매우 용이)
    df = pd.DataFrame(transactions_json)
    
    # 데이터가 비어있는 경우 처리
    if df.empty:
        return jsonify({"analysis_result": "분석할 거래 내역이 없습니다."})

    # --- 🤖 여기에 실제 AI/ML 모델 분석 로직 구현 ---
    # 예시: 간단한 규칙 기반으로 '감정 소비' 패턴 분석
    # 1. '쇼핑' 또는 '식당' 카테고리에서
    # 2. 100달러 이상 결제한 경우를 '감정 소비'로 간주
    
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
    # ----------------------------------------------------

    # 분석 결과를 JSON 형태로 Java 서버에 반환
    return jsonify(analysis_result)

# 서버 실행 (기본 포트: 5000)
if __name__ == "__main__":
    app.run(debug=True)