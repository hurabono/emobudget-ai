# app.py
from flask import Flask, jsonify, request
import os
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

# --- 카테고리 매핑 설정 ---
# Plaid의 기본 카테고리를 앱에서 사용할 카테고리로 변환합니다.
PLAID_TO_APP_CATEGORIES = {
    "Food and Drink": "Restaurants",
    "Restaurants": "Restaurants",
    "Travel": "Travel",
    "Shops": "Shopping",
    "Groceries": "Shopping",
    "Entertainment": "Entertainment",
    "Health & Fitness": "Health",
}

# 거래 이름(상점명)을 기반으로 카테고리를 추정합니다.
PLAID_NAME_TO_CATEGORY = {
    "Walmart": "Shopping",
    "Starbucks": "Restaurants",
    "Uber": "Travel",
    "McDonald's": "Restaurants",
    "Target": "Shopping",
}

# --- 데이터 처리 및 분석 함수 ---

def categorize_transactions(transactions):
    """
    Plaid로부터 받은 거래 내역 리스트를 순회하며 각 거래에 카테고리를 할당합니다.
    Plaid가 제공하는 시간 정보가 있다면 datetime 객체로 변환합니다.
    """
    categorized = []
    for tx in transactions:
        # Plaid의 카테고리 리스트에서 매핑된 카테고리를 찾습니다.
        category_list = tx.get("category", [])
        category = "Other"
        for cat in category_list:
            if cat in PLAID_TO_APP_CATEGORIES:
                category = PLAID_TO_APP_CATEGORIES[cat]
                break
        
        # Plaid 카테고리가 없으면, 상점명을 기반으로 추정합니다.
        if category == "Other":
            category = PLAID_NAME_TO_CATEGORY.get(tx.get("name", ""), "Other")

        # 날짜와 시간 처리 (시간 정보가 없으면 정오로 설정)
        dt_object = datetime.fromisoformat(tx.get("date") + "T12:00:00")
        
        categorized.append({
            "name": tx.get("name"),
            "amount": tx.get("amount", 0),
            "date": tx.get("date"),
            "datetime": dt_object,
            "category": category
        })
    return categorized

def detect_consecutive_payments(df):
    """
    5회 이상 연속적인 결제가 있는지 감지합니다. (Pandas 활용)
    결제(amount > 0)만 필터링하고 날짜 순으로 정렬한 뒤, 시간 차이를 계산합니다.
    """
    payments = df[df['amount'] > 0].sort_values(by='datetime')
    if len(payments) < 5:
        return None

    # 결제 사이의 시간 차이를 계산합니다.
    time_diffs = payments['datetime'].diff().dt.total_seconds() / 3600 # 시간 단위로 변환

    consecutive_count = 0
    # 1시간 이내의 연속 결제를 카운트합니다.
    for diff in time_diffs[1:]: # 첫번째는 NaN이므로 제외
        if diff < 1.0:
            consecutive_count += 1
            if consecutive_count >= 4: # 5회 연속 결제 (차이는 4번 발생)
                return "주의: 단기간에 5회 이상의 연속적인 결제가 발생했습니다. 카드 도용 가능성을 확인해보세요."
        else:
            consecutive_count = 0
    return None

def compare_monthly_spending(df, category="Restaurants"):
    """
    특정 카테고리의 이번 달과 지난달 지출을 비교합니다. (Pandas 활용)
    """
    today = datetime.now()
    this_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = this_month_start - timedelta(microseconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Pandas의 날짜 인덱싱을 사용하여 각 월의 데이터 필터링
    this_month_spending = df[(df['datetime'] >= this_month_start) & (df['category'] == category) & (df['amount'] > 0)]['amount'].sum()
    last_month_spending = df[(df['datetime'] >= last_month_start) & (df['datetime'] <= last_month_end) & (df['category'] == category) & (df['amount'] > 0)]['amount'].sum()

    if this_month_spending == 0:
        return f"이번 달에는 아직 '{category}' 카테고리 지출이 없습니다."

    if last_month_spending == 0:
        return f"이번 달 '{category}' 카테고리 지출은 총 ${this_month_spending:.2f}입니다."

    # 퍼센트 변화율 계산
    percentage_change = ((this_month_spending - last_month_spending) / last_month_spending) * 100
    
    if percentage_change > 0:
        return f"지난달 대비 이번 달 '{category}' 지출이 {percentage_change:.0f}% 늘었어요!"
    elif percentage_change < 0:
        return f"지난달 대비 이번 달 '{category}' 지출이 {abs(percentage_change):.0f}% 줄었어요! 잘하고 있어요."
    else:
        return f"지난달과 이번 달의 '{category}' 지출이 동일합니다."


def analyze_emotional_spending(df):
    """
    '쇼핑', '식비' 카테고리에서 늦은 밤 결제나 빈번한 결제를 감정 소비로 분석합니다.
    """
    emotional_categories = ["Shopping", "Restaurants"]
    emotional_txs = df[df['category'].isin(emotional_categories) & (df['amount'] > 0)]

    if emotional_txs.empty:
        return "최근 감정 소비 패턴이 보이지 않습니다."

    # 늦은 밤(오후 10시 이후) 결제 건수
    late_night_spending_count = emotional_txs[emotional_txs['datetime'].dt.hour >= 22].shape[0]
    
    # 카테고리별 결제 빈도
    spending_frequency = emotional_txs['category'].value_counts()
    most_frequent_category = spending_frequency.idxmax()
    frequency_count = spending_frequency.max()

    analysis_parts = []
    if late_night_spending_count > 2:
        analysis_parts.append(f"최근 늦은 밤(오후 10시 이후)에 {late_night_spending_count}건의 결제가 있었어요.")
    
    if frequency_count > 5:
        analysis_parts.append(f"특히 '{most_frequent_category}' 카테고리에서 {frequency_count}회로 가장 잦은 소비가 있었습니다.")

    if not analysis_parts:
        return "최근 감정 소비 패턴이 보이지 않습니다."
    else:
        return " ".join(analysis_parts)

# --- Flask API 엔드포인트 ---

@app.route("/analyze", methods=["POST"])
def analyze_transactions_endpoint():
    """
    프론트엔드로부터 거래 내역을 받아 각종 분석을 수행하고 결과를 반환합니다.
    """
    transactions_json = request.json
    if not transactions_json:
        return jsonify({"topCategory": "None", "spendingByCategory": {}, "analysis_insights": ["거래 내역이 없습니다."]}), 200

    # 1. 데이터 카테고리화 및 Pandas DataFrame으로 변환
    transactions = categorize_transactions(transactions_json)
    df = pd.DataFrame(transactions)
    df['datetime'] = pd.to_datetime(df['datetime']) # datetime 타입으로 변환

    # 2. 각종 분석 수행
    consecutive_warning = detect_consecutive_payments(df)
    monthly_comparison = compare_monthly_spending(df)
    emotional_analysis = analyze_emotional_spending(df)

    # 3. 분석 결과들을 리스트로 취합
    insights = []
    if consecutive_warning:
        insights.append(consecutive_warning)
    if monthly_comparison:
        insights.append(monthly_comparison)
    if emotional_analysis:
        insights.append(emotional_analysis)
    
    # 4. 기존 분석: 카테고리별 총 지출 및 최고 지출 카테고리 계산
    spending_by_category = df[df['amount'] > 0].groupby('category')['amount'].sum().to_dict()
    top_category = max(spending_by_category, key=spending_by_category.get, default="None")

    # 5. 최종 결과 JSON으로 반환
    return jsonify({
        "topCategory": top_category,
        "spendingByCategory": {k: round(v, 2) for k, v in spending_by_category.items()},
        "analysis_insights": insights  # 프론트엔드에서 사용할 새로운 분석 결과 필드
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
