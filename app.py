import io
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Sales Insight AI', page_icon='📈', layout='wide')
st.title('📈 Sales Insight AI')
st.caption('주문 CSV로 매출 현황을 분석하고 AI로 인사이트를 요약합니다.')

REQUIRED = {'order_id', 'order_date', 'product', 'quantity', 'unit_price'}

@st.cache_data
def load_csv(data: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(data), encoding='utf-8-sig')
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError('필수 컬럼 누락: ' + ', '.join(sorted(missing)))
    df = df.copy()
    df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
    if df[['order_date', 'quantity', 'unit_price']].isna().any().any():
        raise ValueError('날짜 또는 수량/단가에 변환할 수 없는 값이 있습니다.')
    if (df[['quantity', 'unit_price']] < 0).any().any():
        raise ValueError('음수 수량 또는 단가는 지원하지 않습니다.')
    if df.empty:
        raise ValueError('CSV 데이터가 비어 있습니다.')
    df['revenue'] = df['quantity'] * df['unit_price']
    return df

uploaded = st.file_uploader('매출 CSV 업로드', type=['csv'])
if uploaded is None:
    st.info('sample_sales.csv 파일을 업로드해 기능을 확인해 보세요.')
    st.code('order_id,order_date,product,quantity,unit_price', language='text')
    st.stop()

try:
    df = load_csv(uploaded.getvalue())
except Exception as exc:
    st.error(f'파일을 읽을 수 없습니다: {exc}')
    st.stop()

min_date, max_date = df['order_date'].min().date(), df['order_date'].max().date()
period = st.date_input('분석 기간', value=(min_date, max_date), min_value=min_date, max_value=max_date)
if not isinstance(period, (tuple, list)) or len(period) != 2:
    st.info('시작일과 종료일을 모두 선택해 주세요.')
    st.stop()
start, end = period
filtered = df[df['order_date'].dt.date.between(start, end)].copy()
if filtered.empty:
    st.warning('선택한 기간에 데이터가 없습니다.')
    st.stop()

orders = filtered['order_id'].nunique()
revenue = float(filtered['revenue'].sum())
units = int(filtered['quantity'].sum())
aov = revenue / orders if orders else 0
c1, c2, c3, c4 = st.columns(4)
c1.metric('총매출', f'₩{revenue:,.0f}')
c2.metric('주문 수', f'{orders:,}')
c3.metric('판매 수량', f'{units:,}')
c4.metric('주문당 평균 매출', f'₩{aov:,.0f}')

daily = filtered.groupby(filtered['order_date'].dt.date)['revenue'].sum().sort_index()
products = filtered.groupby('product').agg(revenue=('revenue', 'sum'), units=('quantity', 'sum')).sort_values('revenue', ascending=False)
left, right = st.columns(2)
with left:
    st.subheader('일별 매출')
    st.line_chart(daily)
with right:
    st.subheader('상품별 매출 TOP 10')
    st.bar_chart(products['revenue'].head(10))

st.subheader('상품별 상세')
st.dataframe(products.rename(columns={'revenue': '매출', 'units': '판매 수량'}), use_container_width=True)

# 전일 대비 매출 변동이 큰 날 탐지 (0원 기준일은 제외)
daily_df = daily.rename('revenue').to_frame()
daily_df['previous'] = daily_df['revenue'].shift(1)
daily_df['change_pct'] = (daily_df['revenue'] / daily_df['previous'] - 1) * 100
anomalies = daily_df[(daily_df['previous'] > 0) & (daily_df['change_pct'].abs() >= 40)]
st.subheader('매출 변동 알림')
st.caption('데이터에 존재하는 직전 판매일 대비 매출 변동률 40% 이상인 날짜를 표시합니다. 통계적 이상탐지는 아닙니다.')
if anomalies.empty:
    st.success('기준에 해당하는 큰 변동이 없습니다.')
else:
    st.dataframe(anomalies[['revenue', 'change_pct']].rename(columns={'revenue': '매출', 'change_pct': '직전 판매일 대비 변동률(%)'}).round(1), use_container_width=True)

summary = (
    f'분석 기간: {start} ~ {end}\n총매출: {revenue:,.0f}원\n'
    f'주문 수: {orders}건\n판매 수량: {units}개\n평균 주문 금액: {aov:,.0f}원\n'
    f'상품별 매출 TOP 10:\n{products.head(10).to_string()}\n'
    f'큰 매출 변동일:\n{anomalies.head(10).to_string()}'
)
st.subheader('AI 매출 인사이트')
with st.expander('AI에 전달되는 집계 데이터 보기'):
    st.text(summary)
api_key = st.text_input('OpenAI API Key (선택)', type='password', help='입력한 키는 이 앱에서만 API 호출에 사용하며 저장하지 않습니다.')
if st.button('AI 분석 생성', type='primary'):
    key = api_key or os.getenv('OPENAI_API_KEY', '')
    if not key:
        st.warning('OpenAI API Key를 입력하거나 OPENAI_API_KEY 환경변수를 설정해 주세요.')
    else:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            with st.spinner('AI가 매출을 분석하고 있습니다...'):
                response = client.responses.create(
                    model='gpt-4.1-mini',
                    instructions=(
                        '당신은 커머스 매출 분석가입니다. 주어진 집계 수치에만 근거하여 한국어로 '
                        '1) 핵심 요약 2) 관찰된 변화 3) 실행 가능한 개선 제안 3가지를 작성하세요. '
                        '원인이나 미래 결과를 단정하지 말고 가설임을 명시하세요.'
                    ),
                    input=summary,
                )
            st.markdown(response.output_text)
        except Exception as exc:
            st.error(f'AI 호출 실패: {exc}')

st.download_button('필터된 매출 데이터 다운로드', filtered.to_csv(index=False).encode('utf-8-sig'), 'filtered_sales.csv', 'text/csv')
