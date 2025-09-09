# app.py
from flask import Flask, jsonify, request
from datetime import datetime
import os

app = Flask(__name__)

# 09092025 감정 소비로 간주될 수 있는 카테고리 목록
EMOTIONAL_SPENDING_CATEGORIES = [
    "FOOD_AND_DRINK",
    "SHOPS", 
    "TRAVEL", 
    "ENTERTAINMENT", 
]

def analyze_transactions(transactions):
    """
    거래 내역 리스트를 받아 감정 소비 패턴을 분석하는 함수.
    사용자의 계획에 따라 규칙 기반 모델을 적용합니다.
    """
    if not transactions:
        return {
            "topCategory": "None",
            "spendingByCategory": {},
            "emotionalSpendingPattern": "분석할 거래 내역이 없습니다."
        }

    spending_by_category = {}
    emotional_spending_events = [] 

    # --- 1. 변수 설정 및 데이터 전처리 ---
    for tx in transactions:
        # 카테고리별 지출 합계 계산
        category = tx.get("category", "Uncategorized")
        amount = tx.get("amount", 0)
        if amount > 0: # 수입은 제외
            spending_by_category[category] = spending_by_category.get(category, 0) + amount

        # transactionTime을 datetime 객체로 변환
        tx_time_str = tx.get("transactionTime")
        tx_time = datetime.fromisoformat(tx_time_str) if tx_time_str else None

        # --- 2. 규칙 기반 모델 적용 ---
        if tx_time:
            # 규칙 1: '늦은 밤(22시~02시)'에 '배달 음식' 또는 '택시' 이용
            is_late_night = 22 <= tx_time.hour or tx_time.hour < 2
            is_delivery_or_taxi = "FOOD_AND_DRINK" in category or "TRAVEL" in category
            if is_late_night and is_delivery_or_taxi and amount > 15: # 최소 금액 조건 추가
                event_desc = f"{tx_time.strftime('%m/%d %H:%M')}에 {tx.get('name')}에서 {amount:,.0f}원 결제 (늦은 밤 소비)"
                emotional_spending_events.append(event_desc)

            # 규칙 2: '주말'에 '온라인 쇼핑'에서 5만원 이상 결제
            is_weekend = tx_time.weekday() >= 5 # 토(5), 일(6)
            is_shopping = "SHOPS" in category
            if is_weekend and is_shopping and amount >= 50000:
                event_desc = f"{tx_time.strftime('%m/%d')} 주말에 {tx.get('name')}에서 {amount:,.0f}원 결제 (주말 충동구매 의심)"
                emotional_spending_events.append(event_desc)


    # --- 3. 결과 분석 및 시사점 도출 ---
    top_category = max(spending_by_category, key=spending_by_category.get, default="None")
    
    analysis_result = ""
    if emotional_spending_events:
        # 감정 소비 이벤트가 발견된 경우
        total_events = len(emotional_spending_events)
        analysis_result = f"총 {total_events}건의 감정 소비 패턴이 발견되었습니다.\n"
        analysis_result += "\n".join(f"- {event}" for event in emotional_spending_events)
    else:
        # 발견되지 않은 경우
        analysis_result = "최근 감정 소비로 의심되는 패턴이 발견되지 않았습니다. 건강한 소비 습관을 유지하고 계시네요!"

    return {
        "topCategory": top_category,
        "spendingByCategory": spending_by_category,
        "emotionalSpendingPattern": analysis_result
    }


@app.route("/analyze", methods=["POST"])
def handle_analyze_request():
    transactions = request.json
    analysis_result = analyze_transactions(transactions)
    # --- 09092025 Spring Boot DTO 필드명에 맞춰 JSON key를 반환합니다.
    return jsonify(analysis_result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))