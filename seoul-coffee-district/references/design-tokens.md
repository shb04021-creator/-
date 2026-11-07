# 공통 디자인 토큰 (깔끔한 에디토리얼 · 커피 웜톤)

옐로우·오렌지·화이트가 같은 값을 쓴다. 손글씨 서체, 일본어 문구, 과한 감성 카피는 쓰지 않는다(담백하게).

```css
:root{--paper:#F6F4F0;--ink:#24221F;--mute:#86807A;--line:#E2DDD6;--accent:#7A5A44;--warm:#C9A27E;--card:#FFFFFF;
--sans:'Pretendard Variable',Pretendard,system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root{--paper:#18191B;--ink:#ECE8E2;--mute:#8F8A84;--line:#2C2E31;--card:#1F2022;--accent:#D4B49A}}
```

- 서체: Pretendard 하나. 제목 600, 큰 숫자 200~300, 본문 400. 숫자는 tabular-nums.
- 1px 얇은 선, 각진 카드(radius 4px), 넉넉한 여백(섹션 72px). Material Design 3는 컴포넌트 구조(카드·표·칩)로만 사용.
- 차트: 주 시리즈 accent, 나머지 line 회색. 차트마다 `.source-caption`.
- 영상(화이트): 16:9, 30초, 장면 6개 × 5초. 배경은 램프 조명의 오타루 카페 실사 사진(라이선스 확인된 Wikimedia Commons, 출처 표기), 어둡게 처리하고 아주 느린 드리프트.
  상단 위치 태그(📍 지역 · 상권), 가운데 대화체 자막 한 줄(Gowun Dodum, 흰 글씨+그림자) + 아래 작은 근거 수치 한 줄.
  한국어 설명 내레이션(edge-tts ko-KR-SunHiNeural, 약간 느리게·낮게), 장면 시작마다 해당 문장 재생. 잔잔한 피아노 BGM은 음성보다 작게.
  장면: 시장 → 후보 압축 → 선정 상권 → 고객 → 인테리어 → 제안(메뉴·투자·손익).
