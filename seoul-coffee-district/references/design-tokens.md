# 공통 디자인 토큰 (Material Design 3 · 커피 브라운)

옐로우·오렌지·화이트가 같은 값을 쓴다. CSS 변수로 `:root`에 선언하고 다크 모드도 정의한다.

```css
:root {
  --md-primary: #6F4E37;        /* coffee brown */
  --md-on-primary: #FFFFFF;
  --md-primary-container: #F3DFD2;
  --md-on-primary-container: #2A1709;
  --md-secondary: #8C6A4F;
  --md-tertiary: #3E6B5A;       /* 강조·긍정 지표 */
  --md-error: #B3261E;          /* 리스크·하락 */
  --md-surface: #FFF8F4;
  --md-surface-container: #F5EBE4;
  --md-on-surface: #1F1A17;
  --md-outline: #85736A;
  --radius-card: 16px; --radius-chip: 8px;
  --elev-1: 0 1px 3px rgba(0,0,0,.12);
  --font: 'Pretendard Variable', Pretendard, system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root { --md-primary:#E0BFA6; --md-on-primary:#3F2716; --md-surface:#17120F; --md-surface-container:#231C18; --md-on-surface:#ECE0DA; --md-primary-container:#573A26; --md-on-primary-container:#FBDCC8; }
}
```

- 폰트: Pretendard (`https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css`)
- 타이포: Display 44/52 bold, Headline 28/36 semibold, Title 20/28 semibold, Body 16/24, Label 13/18 medium, 숫자는 `font-variant-numeric: tabular-nums`.
- 차트: 주 시리즈 primary, 비교 시리즈 outline 회색, 강조 1개만 tertiary. 축 라벨에 단위. 차트 아래 `.source-caption`(Label, outline 색).
- 레이아웃: 최대 폭 1200px, 12컬럼, 모바일(<768px) 1컬럼·좌우 16px.
- 영상(16:9, 1920×1080): 같은 색·폰트, 장면 전환 300ms ease, 자막 하단 중앙 Title 크기.
