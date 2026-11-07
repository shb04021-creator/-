# 데이터 소스 — 서울 열린데이터광장 상권분석서비스

호출 형식: `http://openapi.seoul.go.kr:8088/{KEY}/json/{서비스명}/{시작}/{끝}/{기준분기}/` (한 번에 최대 1,000행, 기준분기 예 `20262` = 2026년 2분기). 2026-11 확인 기준 최신 분기는 20262.

| 파일 | 서비스명 | 데이터셋 (ID) | 업종 필터 | 비고 |
|---|---|---|---|---|
| sales_trdar | VwsmTrdarSelngQq | 추정매출-상권 (OA-15572) | CS100010 | 분기 전체 약 2.1만 행. 요일·시간대·성별·연령대별 매출 |
| sales_adstrd | VwsmAdstrdSelngW | 추정매출-행정동 (OA-22175) | CS100010 | |
| sales_signgu | VwsmSignguSelngW | 추정매출-자치구 (OA-22176) | CS100010 | |
| store_trdar | VwsmTrdarStorQq | 점포-상권 (OA-15577) | CS100010 | 점포수, 개업률, 폐업률, 프랜차이즈 점포수 |
| store_adstrd | VwsmAdstrdStorW | 점포-행정동 (OA-22172) | CS100010 | |
| flpop_trdar | VwsmTrdarFlpopQq | 길단위인구-상권 (OA-15568) | - | 시간대·요일·성별·연령 |
| repop_trdar | VwsmTrdarRepopQq | 상주인구-상권 (OA-15584) | - | |
| wrcpop_trdar | VwsmTrdarWrcPopltnQq | 직장인구-상권 (OA-15569) | - | |
| ix_trdar | VwsmTrdarIxQq | 상권변화지표-상권 (OA-15576) | - | LL/LH/HL/HH, 운영·폐업 영업개월 |
| fclty_trdar | VwsmTrdarFcltyQq | 집객시설-상권 (OA-15580) | - | |
| cnsmp_trdar | VwsmTrdarNcmCnsmpQq | 소득소비-상권 (OA-21278) | - | 2026-11 확인 시 서버 오류 응답. 실패하면 행정동/자치구판(OA-22166/22167)으로 대체하고 data_quality.md에 기록 |
| (영역) | TbgisTrdarRelm | 영역-상권 (OA-15560) | - | 상권코드 ↔ 자치구·행정동 매핑, 좌표 |

## 알려진 한계 (보고서 '데이터 한계 및 보정 방법'의 출발점)

- 추정매출은 카드사 결제 데이터 기반 추정치다. 현금·일부 간편결제가 빠져 실제보다 낮을 수 있다.
- 상권 경계는 서울시가 정한 약 1,650개 영역이다. 실제 상권과 다를 수 있고, 상권 밖 점포는 빠진다.
- 점포수는 인허가·사업자 기반이라 휴업 점포가 포함될 수 있다.
- 분기마다 행 수가 다를 수 있다(신규·소멸 상권). 8분기 모두 있는 상권만 추세 분석에 쓰는 것이 안전하다.
- 임대료는 이 API에 없다. 한국부동산원 상업용부동산 임대동향 등 외부 출처를 쓰고 출처를 분리 표기한다.
