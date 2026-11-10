# Sales Insight AI 📈

**CSV 기반 매출 분석 + AI 인사이트 생성**을 제공하는 간단한 Streamlit 포트폴리오 프로젝트입니다.

## 주요 기능
- 주문 CSV 업로드 및 데이터 검증
- 기간별 매출, 주문 수, 판매 수량, 평균 주문 금액(KPI)
- 일별 매출 추이 및 상품별 매출 TOP 10
- 직전 판매일 대비 매출 변동률 40% 이상 알림 (단순 규칙 기반)
- OpenAI API를 활용한 매출 요약 및 개선 제안 (선택 기능)
- 분석 결과 CSV 다운로드

## 실행 방법

Python 3.10 이상을 권장합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 표시된 로컬 주소로 접속한 뒤 `sample_sales.csv`를 업로드하세요.

AI 기능은 화면에서 API 키를 입력하거나 `OPENAI_API_KEY` 환경변수로 설정하면 사용할 수 있습니다. **API 호출 요금이 발생할 수 있습니다.** API 키를 코드나 GitHub에 올리지 마세요.

## CSV 형식

| 컬럼 | 설명 | 예시 |
| --- | --- | --- |
| `order_id` | 주문 ID | ORD-001 |
| `order_date` | 주문일 | 2026-10-01 |
| `product` | 상품명 | T-Shirt |
| `quantity` | 수량 (0 이상) | 2 |
| `unit_price` | 판매 단가 (원, 0 이상) | 29000 |

한 행은 주문 내 상품 1개 항목을 나타냅니다. `order_id`는 중복 가능하며 주문 수는 고유 주문 ID로 집계합니다. 매출은 `quantity × unit_price`로 계산합니다. 취소·반품·할인·배송비·부가세 등은 MVP에서 별도 처리하지 않습니다.

## 기술 스택
- Python, Streamlit, pandas
- OpenAI API (`gpt-4.1-mini`, 선택 사항)

## 설계 의도
기본 KPI와 변동률은 **결정론적인 pandas 계산**으로 처리하고, 생성형 AI는 **집계 결과의 자연어 해석**에만 사용합니다. 수치 계산과 설명 생성을 분리해 재현성과 검증 가능성을 높였습니다.

## 한계 및 확장 아이디어
- 연속된 달력 날짜가 아닌 **데이터가 있는 직전 판매일** 대비 변동률을 계산합니다.
- AI 설명은 가설을 포함할 수 있으며, 실제 비즈니스 의사결정 전 검증이 필요합니다.
- 향후 반품/할인 처리, 채널별 분석, 전년 대비 비교, 테스트 코드, 배포 환경별 비밀키 관리 등을 추가할 수 있습니다.
