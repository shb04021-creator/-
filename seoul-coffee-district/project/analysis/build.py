import json, pathlib, sys, csv, base64
R=pathlib.Path(sys.argv[1]); r=json.load(open(R/"analysis/result.json",encoding="utf-8"))
man=json.load(open(R/"data/manifest.json",encoding="utf-8")); called=man["files"][0]["called"]
Q=r["quarters"]; ql=lambda q:f"{q[:4]}년 {q[4]}분기"; Q0,Q7=ql(Q[0]),ql(Q[-1]); qa=r["qa"]
S_SALES=f"서울시 상권분석서비스(추정매출-상권) OA-15572 / {Q7}~{Q0} / 호출일 {called}"
S_STORE=f"서울시 상권분석서비스(점포-상권) OA-15577 / {Q7}~{Q0} / 호출일 {called}"
S_FLPOP=f"서울시 상권분석서비스(길단위인구-상권) OA-15568 / {Q7}~{Q0} / 호출일 {called}"
S_WRC=f"서울시 상권분석서비스(직장인구-상권) OA-15569 / {Q0} / 호출일 {called}"
S_IX=f"서울시 상권분석서비스(상권변화지표-상권) OA-15576 / 최신 / 호출일 {called}"
S_AREA=f"서울시 상권분석서비스(영역-상권) OA-15560 / 호출일 {called}"
PHOTO="https://upload.wikimedia.org/wikipedia/commons/b/b7/Jazz_Cafe_%40_Otaru.jpg"
PHOTO2="https://upload.wikimedia.org/wikipedia/commons/5/58/Lamps_in_Otaru-Station.jpg"
PHOTO_CREDIT='사진: "Jazz Cafe @ Otaru", MIKI Yoshihito, <a href="https://creativecommons.org/licenses/by/2.0/">CC BY 2.0</a>; "Lamps in Otaru-Station", snow rabbit, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC BY-SA 2.0</a>; via Wikimedia Commons'
t=r["top5"]; pk=r["pick"]; dec=r["decomp"]
eok=lambda v:f"{v/1e8:,.1f}억 원"; pct=lambda v:f"{v*100:+.1f}%"
# 선정 상권 고객 구성 (최신 분기)
row=[x for x in csv.DictReader(open(R/"data/sales_trdar.csv",encoding="utf-8-sig")) if x["TRDAR_CD"]==pk["code"] and x["STDR_YYQU_CD"]==Q[0]][0]
TM=["06_11","11_14","14_17","17_21","21_24"]; tm={k:float(row[f"TMZON_{k}_SELNG_AMT"]) for k in TM}; tot=sum(tm.values())
ag={k:float(row[f"AGRDE_{k}_SELNG_AMT"]) for k in ["20","30","40","50","60_ABOVE"]}; ags=sum(ag.values())
male=float(row["ML_SELNG_AMT"])/(float(row["ML_SELNG_AMT"])+float(row["FML_SELNG_AMT"]))
wk=float(row["MDWK_SELNG_AMT"])/(float(row["MDWK_SELNG_AMT"])+float(row["WKEND_SELNG_AMT"]))
am=(tm["06_11"]+tm["11_14"])/tot; a3040=(ag["30"]+ag["40"])/ags
# 손익 (가정) — 한 가지 계산식만 사용: 영업이익 = 매출×(1−원가율−기타변동비율) − 고정비
base=pk["sales_per_store_q"]*4                     # 상권 점포당 연 추정매출 = 신규점 3년차 목표
COGS,OTH=0.30,0.10; FIX=base*0.40                  # 고정비(인건비 25%+임차 15%)는 3년차 매출 기준 금액으로 고정
ramp=[0.7,0.9,1.0]; pl=[]
for i,k in enumerate(ramp):
    rev=base*k; pl.append({"y":i+1,"k":k,"rev":rev,"op":rev*(1-COGS-OTH)-FIX})
INV={"인테리어 (25평 × 평당 300만 원)":0.75e8,"장비·집기":0.60e8,"오픈 비용·초기 재고":0.25e8}; DEP=1.0e8
inv=sum(INV.values()); cum=0; pay=None
for p in pl:
    if pay is None and cum+p["op"]>=inv: pay=p["y"]-1+(inv-cum)/p["op"]
    cum+=p["op"]
sens=[(k,base*(1+k),base*(1+k)*(1-COGS-OTH)-FIX) for k in (-0.2,0,0.2)]
def bars(vals,labels,fmt,hl=None,h=150,w=560):
    m=max(vals); bw=w/len(vals)
    return '<svg viewBox="0 0 %d %d" role="img">%s</svg>'%(w,h,"".join(
     f'<rect x="{i*bw+bw*.25:.0f}" y="{h-22-(v/m)*(h-46):.0f}" width="{bw*.5:.0f}" height="{(v/m)*(h-46):.0f}" fill="{"var(--accent)" if hl is None or i in hl else "var(--line)"}"/>'
     f'<text x="{i*bw+bw/2:.0f}" y="{h-6}" text-anchor="middle" class="ax">{labels[i]}</text><text x="{i*bw+bw/2:.0f}" y="{h-28-(v/m)*(h-46):.0f}" text-anchor="middle" class="vl">{fmt(v)}</text>' for i,v in enumerate(vals)))
qs=[f"{q[2:4]}.{q[4]}Q" for q in Q[::-1]]
toprows="".join(f'<tr class="{"hl" if x["code"]==pk["code"] else ""}"><td>{i+1}</td><td>{x["name"]}<small>{x["gu"]} {x["dong"]}</small></td><td>{pct(x["growth"])}</td><td>{x["stores"]}</td><td>{eok(x["sales_per_store_q"])}</td><td>{x["net_open"]:+.1f}%p</td><td>{pct(x["flpop_growth"])}</td><td>{" / ".join(str(v) for v in x["ranks"].values())}</td></tr>' for i,x in enumerate(t))
gurows="".join(f'<tr><td></td><td>{g["gu"]}</td><td>{pct(g["growth"])}</td></tr>' for g in r["gu_top5"])
excl="".join(f'<li>{e["name"]}: 성장 {pct(e["growth"])}였지만 {"점포당 매출이 중앙값 미만" if (e["sps"] or 0)<qa["sps_median"] else "순개업이 마이너스"}</li>' for e in r["excluded_examples"])
plrows="".join(f'<tr><td>{p["y"]}년차</td><td>{p["k"]*100:.0f}%</td><td>{eok(p["rev"])}</td><td>{eok(p["rev"]*(COGS+OTH))}</td><td>{eok(FIX)}</td><td>{eok(p["op"])}</td></tr>' for p in pl)
invrows="".join(f'<tr><td></td><td>{k}</td><td>{eok(v)}</td></tr>' for k,v in INV.items())
sensrows="".join(f'<tr><td>매출 {k:+.0%}</td><td>{eok(rv)}</td><td>{eok(op)}</td></tr>' for k,rv,op in sens)
mq=qa["market_qoq_median"]
scenes=[("서울 커피 시장은 지난 1년, %.0f%% 성장했어요"%(r["seoul_growth"]*100),
         f"최근 4분기 매출 ÷ 직전 4분기 · 8개 분기 모두 있는 {qa['trdar_all8']:,}개 상권 · 카드결제 기반 추정"),
        (f"{qa['universe']}개 상권 중 조건을 통과한 곳은 {qa['screened']}곳이에요",
         f"4분기 연속 성장 · 점포당 매출 중앙값({eok(qa['sps_median'])}) 이상 · 8분기 순개업 0 이상"),
        (f"그중 코엑스 상권은 매출이 {pk['growth']*100:.0f}% 늘었어요",
         f"점포 수 {pct(dec['store_growth'])} · 점포당 매출 {pct(dec['sps_growth'])} · 유동인구 {pct(dec['flpop_growth'])} · 가중치 4종 모두 2위 이내"),
        (f"손님 {am*100:.0f}%는 오후 2시 전에 와요",
         f"평일 매출 {wk*100:.0f}% · 30~40대 {a3040*100:.0f}% · 남성 {male*100:.0f}% ({Q0})"),
        ("입구엔 픽업 카운터, 안쪽엔 차분한 소회의석을 둬요",
         "모바일 주문 전용 라인 · 2~4인 소회의석 · 목재와 간접 조명 · 좌석보다 회전 동선에 면적 배분"),
        ("평일 아침을 위한 25평 매장을 제안해요",
         f"메뉴: 배치 브루·시그니처 라떼·핸드드립 · 투자 {eok(inv)} · 3년차 영업이익 {eok(pl[2]['op'])} · 회수 약 {pay:.1f}년 (가정)")]
film="".join(f'<div class="sc" data-t="{i*5}"><p>{s[0]}</p><small>{s[1]}</small><audio class="nar" preload="auto" src="data:audio/mpeg;base64,{base64.b64encode((R/f"output/video/n{i+1}.mp3").read_bytes()).decode()}"></audio></div>' for i,s in enumerate(scenes))
CSS=open(R/"analysis/style.css",encoding="utf-8").read(); JS=open(R/"analysis/film.js",encoding="utf-8").read()
html=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>서울 커피 출점 전략</title>
<link href="https://fonts.googleapis.com/css2?family=Gowun+Dodum&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>{CSS}</style></head><body><main>
<header class="hero"><div class="kicker">Seoul Coffee District · {Q0} 기준</div>
<h1>다음 매장은 코엑스 상권입니다</h1><p class="lede">강남구 삼성1동. 서울 커피 시장이 정체한 1년 동안, 매출이 꾸준히 늘었고 그 성장이 한 분기의 우연이 아니라는 점을 데이터로 확인했습니다.</p>
<div class="answer"><b>결론.</b> 신규 출점지는 <b>{pk['gu']} {pk['dong']} · {pk['name']}</b> 상권입니다. 서울 커피 매출이 {pct(r['seoul_growth'])} 늘 때 이 상권은 <b>{pct(pk['growth'])}</b> 늘었습니다. 성장의 대부분은 점포 수가 아니라 <b>점포당 매출({pct(dec['sps_growth'])})</b>에서 나왔고, 유동인구도 {pct(dec['flpop_growth'])} 늘었습니다. 평일 오전 수요에 맞춘 <b>25평 테이크아웃 중심 매장</b>을 제안합니다. 투자 {eok(inv)}(보증금 별도), 3년차 영업이익 {eok(pl[2]['op'])}, 회수 약 {pay:.1f}년(모두 가정 기반)입니다.
<div class="kpis"><div class="kpi"><div class="v">{pct(pk['growth'])}</div><div class="l">최근 4분기 매출 ÷ 직전 4분기</div></div><div class="kpi"><div class="v">{eok(pk['sales_per_store_q'])}</div><div class="l">점포당 분기 매출 (추정)</div></div><div class="kpi"><div class="v">{am*100:.0f}%</div><div class="l">06~14시 매출 비중</div></div><div class="kpi"><div class="v">{pay:.1f}년</div><div class="l">투자 회수 (가정)</div></div></div>
<p class="source-caption">출처: {S_SALES}; {S_STORE}; {S_FLPOP}. 매출은 카드결제 기반 추정치, 투자·비용은 가정치.</p></div></header>

<section><div class="kicker">01 · Framework</div><h2>세 단계로, 규칙을 먼저 정하고 골랐습니다</h2>
<div class="grid2"><div><p><span class="tag">1단계 걸러내기</span>8개 분기 매출이 모두 있고, 점포 5개 이상, 최근 4개 분기가 모두 직전 4분기 평균보다 높고(성장 지속), 점포당 매출이 중앙값({eok(qa['sps_median'])}) 이상, 8분기 평균 순개업(개업률−폐업률) 0 이상.</p>
<p><span class="tag">2단계 점수</span>성장률 40 · 유동인구 증가 15 · 점포당 매출 20 · 순개업 10 · 직장인구 15. 지표마다 상하위 5%를 잘라 표준화(z).</p>
<p><span class="tag">3단계 강건성</span>가중치 네 가지(기본·수요 중시·수익 중시·균등)의 평균 순위가 가장 높은 곳. 동률이면 유동인구 증가가 큰 곳.</p></div>
<div><p><b>깔때기</b></p><table><tbody><tr><td></td><td>커피 매출이 있는 상권</td><td>{qa['trdar_any']:,}</td></tr><tr><td></td><td>8개 분기 모두 존재</td><td>{qa['trdar_all8']:,}</td></tr><tr><td></td><td>점포 5개 이상 · 인구 데이터 결합</td><td>{qa['universe']:,}</td></tr><tr><td></td><td>1단계 통과</td><td>{qa['screened']}</td></tr><tr><td></td><td>최종 선정</td><td>1</td></tr></tbody></table>
<p class="note">걸러진 고성장 상권 예시</p><ul class="note">{excl}</ul></div></div>
<p class="source-caption">출처: {S_SALES}; {S_STORE}; {S_FLPOP}; {S_WRC}. 재현: analysis/analyze.py (같은 data/ 입력이면 같은 결과).</p></section>

<section><div class="kicker">02 · Location</div><h2>후보 다섯 곳과 선정 이유</h2>
<div class="wrap"><table><thead><tr><th>#</th><th>상권</th><th>4Q 성장</th><th>점포</th><th>점포당 분기매출</th><th>순개업(8Q 평균)</th><th>유동인구 증가</th><th>순위 (기본/수요/수익/균등)</th></tr></thead><tbody>{toprows}</tbody></table></div>
<p class="source-caption">출처: {S_SALES}; {S_STORE}; {S_FLPOP}; {S_WRC}. 행정동·자치구 표기는 {S_AREA} 매핑.</p>
<p>원남동사거리는 기본 가중치 1위이고 성장률(+156.7%)도 더 높습니다. 하지만 점포당 매출이 코엑스의 약 40% 수준이고 유동인구는 줄었습니다. 두 곳의 평균 순위가 같아 3단계 규칙(유동인구 증가)에 따라 코엑스를 골랐습니다. 수요가 늘어나는 곳의 성장이 3년 뒤에도 이어질 가능성이 높다고 봤기 때문입니다.</p>
<div class="grid2"><div><p>코엑스 상권 분기별 커피 매출 (억 원, 추정)</p>{bars(pk['quarterly'],qs,lambda v:f"{v/1e8:.0f}",hl=[4,5,6,7])}<p class="source-caption">출처: {S_SALES}</p></div>
<div><p>매출이 성장 자치구 상위 5곳</p><table><tbody>{gurows}</tbody></table><p class="source-caption">출처: {S_SALES}; {S_AREA}</p></div></div></section>

<section><div class="kicker">03 · Why it grew</div><h2>2025년 3분기 이후의 성장은 일시적이지 않습니다</h2>
<p>성장이 한 분기에 몰렸다면 기저효과일 수 있습니다. 세 가지로 확인했습니다.</p>
<ul><li><b>시장 공통 현상이 아닙니다.</b> 같은 분기 서울 커피 상권의 매출 변화 중앙값은 {pct(mq['20253'])}였습니다.</li>
<li><b>새 수준이 유지됐습니다.</b> 최근 4개 분기가 모두 직전 4분기 평균보다 높습니다(1단계 조건).</li>
<li><b>점포를 늘려서 오른 것이 아닙니다.</b> 매출 = 점포 수 × 점포당 매출로 나누면 점포 수 {pct(dec['store_growth'])}, 점포당 매출 {pct(dec['sps_growth'])}입니다. 같은 기간 유동인구는 {pct(dec['flpop_growth'])}입니다.</li></ul>
<div class="grid2"><div><p>점포 수 (개)</p>{bars(pk['stores_q'],qs,lambda v:f"{v:.0f}")}<p class="source-caption">출처: {S_STORE}</p></div><div><p>유동인구 (만 명, 분기)</p>{bars(pk['flpop_q'],qs,lambda v:f"{v/1e4:.0f}")}<p class="source-caption">출처: {S_FLPOP}</p></div></div>
<p class="note">점포당 매출이 오른 이유(대형 행사, 새 오피스 입주 등)는 이 데이터로는 알 수 없습니다. 출점 전 현장 실사에서 확인할 항목으로 남깁니다.</p></section>

<section><div class="kicker">04 · Interior</div><h2>짧게 머무는 손님을 위한 공간</h2>
<p>최신 분기 기준 매출의 {am*100:.0f}%가 06~14시, {wk*100:.0f}%가 평일, 남성 {male*100:.0f}%, 30~40대 {a3040*100:.0f}%입니다.</p>
<div>{bars([tm[k] for k in TM],["06–11","11–14","14–17","17–21","21–24"],lambda v:f"{v/tot*100:.0f}%",hl=[0,1])}<p class="source-caption">출처: 서울시 상권분석서비스(추정매출-상권) OA-15572 / {Q0} / 호출일 {called} — 코엑스 상권 시간대별 매출 비중</p></div>
<ul><li>입구 쪽 픽업 카운터와 모바일 주문 전용 라인: 오전 피크의 대기 시간을 줄입니다.</li><li>2~4인 소회의 좌석 위주, 차분한 목재와 간접 조명: 회의 전후 10~20분 체류에 맞춥니다.</li><li>저녁 매출이 적으므로 좌석 수보다 회전 동선에 면적을 씁니다.</li></ul></section>

<section><div class="kicker">05 · Menu</div><h2>커피에 집중한 메뉴</h2>
<ul><li><b>오전</b>: 배치 브루와 아메리카노 빠른 라인, 출근 세트</li><li><b>점심</b>: 시그니처 라떼 2종, 회의용 4~8잔 단체 주문</li><li><b>오후</b>: 싱글 오리진 핸드드립, 디카페인</li><li>객단가는 API에 없어 가정하지 않았습니다. 오픈 후 POS로 측정해 손익 가정을 갱신합니다.</li></ul></section>

<section><div class="kicker">06 · P&amp;L</div><h2>투자와 3년 손익</h2>
<p>3년차 목표 매출은 이 상권 점포당 연 추정매출({eok(base)} = 분기 {eok(pk['sales_per_store_q'])} × 4)과 같다고 두고, 1년차 70%, 2년차 90%에 도달한다고 가정했습니다.</p>
<div class="grid2"><div><p>초기 투자 (가정)</p><table><tbody>{invrows}<tr><td></td><td><b>합계 (보증금 {eok(DEP)} 별도)</b></td><td><b>{eok(inv)}</b></td></tr></tbody></table></div>
<div><p>회수 기간</p><div class="kpi"><div class="v">약 {pay:.1f}년</div><div class="l">누적 영업이익이 투자 합계를 넘는 시점</div></div></div></div>
<div class="wrap"><table><thead><tr><th>연차</th><th>도달률</th><th>매출</th><th>변동비 (원가 30%+기타 10%)</th><th>고정비 (인건비+임차)</th><th>영업이익</th></tr></thead><tbody>{plrows}</tbody></table></div>
<div class="wrap"><table><thead><tr><th>3년차 민감도</th><th>매출</th><th>영업이익</th></tr></thead><tbody>{sensrows}</tbody></table></div>
<p class="source-caption">매출 기준값 출처: {S_SALES}. 계산식(모든 표 공통): 영업이익 = 매출 × (1 − 0.30 − 0.10) − 고정비, 고정비 = 3년차 매출 × 40%. 원가율·고정비율·투자비는 <b>가정</b>이며 실사로 갱신합니다.</p></section>

<section><div class="kicker">07 · Counter-arguments</div><h2>예상 반론과 답</h2>
<ul><li><b>"성장이 한 분기에 몰렸다."</b> 03절처럼 시장 공통 현상이 아니고, 네 분기 연속 새 수준이 유지됐으며, 유동인구도 늘었습니다.</li>
<li><b>"가중치를 바꾸면 결과가 바뀐다."</b> 네 가지 가중치에서 모두 2위 이내입니다.</li>
<li><b>"이미 점포가 {pk['stores']}개다."</b> 8분기 평균 순개업이 {pk['net_open']:+.1f}%p로 포화로 인한 이탈이 없고, 점포당 매출은 후보 중 가장 높습니다.</li>
<li><b>"추정매출을 믿을 수 있나."</b> 절대 금액이 아니라 같은 데이터 안의 성장률과 상대 순위로 판단했습니다. 08절에 한계를 정리했습니다.</li></ul></section>

<section id="limits"><div class="kicker">08 · Data</div><h2>데이터 한계 및 보정 방법</h2>
<div class="wrap"><table><thead><tr><th>한계</th><th style="text-align:left">내용</th><th style="text-align:left">보정</th></tr></thead><tbody>
<tr><td>추정치</td><td style="text-align:left">추정매출은 카드결제 기반이라 현금·일부 간편결제가 빠짐</td><td style="text-align:left">절대 금액 대신 성장률·상대 순위로 판단</td></tr>
<tr><td>상권 수 변동</td><td style="text-align:left">분기별 상권 수 {min(qa['trdar_per_q'].values()):,}~{max(qa['trdar_per_q'].values()):,}개</td><td style="text-align:left">8개 분기가 모두 있는 {qa['trdar_all8']:,}개만 사용</td></tr>
<tr><td>소표본</td><td style="text-align:left">점포 1~4개 상권은 성장률이 극단적</td><td style="text-align:left">점포 5개 이상 + 지표별 상하위 5% 절단</td></tr>
<tr><td>계절성</td><td style="text-align:left">분기 단독 비교는 계절 영향을 받음</td><td style="text-align:left">4개 분기 합끼리 비교</td></tr>
<tr><td>레벨 점프</td><td style="text-align:left">일부 상권은 한 분기에 매출이 크게 뜀</td><td style="text-align:left">4분기 연속 유지 조건, 시장 중앙값 대비 확인, 점포 수·점포당 매출 분해</td></tr>
<tr><td>분기 파라미터</td><td style="text-align:left">직장·상주인구 API는 분기 지정이 무시되고 전 분기가 내려옴</td><td style="text-align:left">기준분기 컬럼으로 {Q0}만 골라 사용</td></tr>
<tr><td>1회차 결함</td><td style="text-align:left">점포 데이터를 3개 분기만 수집했음</td><td style="text-align:left">2회차에 8개 분기 전량 재수집</td></tr>
<tr><td>코드 체계</td><td style="text-align:left">상권코드와 행정동코드는 다른 체계</td><td style="text-align:left">계산은 상권코드로만, 행정동·자치구는 영역-상권 매핑으로 표기만</td></tr>
<tr><td>없는 데이터</td><td style="text-align:left">임대료·객단가는 API에 없고, 소득소비-상권 API는 서버 오류</td><td style="text-align:left">비용·투자는 가정으로 분리 표기, 실사로 대체</td></tr>
</tbody></table></div><p class="source-caption">품질 점검: 추정매출 {qa['rows_sales']:,}행, (분기·상권) 중복 {qa['dup_sales']}건, 매출 결측 {qa['null_amt']}건, 실패 호출 0건. 원본은 raw/에 그대로 보존. 출처: {S_SALES}</p></section>

<section><div class="kicker">09 · Roadmap</div><h2>실행 로드맵</h2>
<ul><li><b>1분기</b>: 삼성1동 매물 실사, 임대료·보증금 확인, 점포당 매출이 오른 원인 현장 확인, 손익 가정 갱신</li><li><b>2분기</b>: 계약, 인테리어, 모바일 주문 연동</li><li><b>3분기</b>: 오픈, POS로 객단가와 시간대 매출 측정</li><li><b>4분기 이후</b>: 같은 3단계 규칙으로 데이터를 갱신해 2호점(원남동사거리·방학역 2번 등) 재평가</li></ul></section>

<section><div class="kicker">10 · Film</div><h2>30초 요약</h2>
<div id="film"><div class="bg b1" style="background-image:url('{PHOTO}')"></div><div class="bg b2" style="background-image:url('{PHOTO2}')"></div><div class="loc">📍 서울 강남구 삼성1동 · 코엑스 상권</div>{film}<button id="play">▶</button></div>
<p class="source-caption">영상 속 수치 출처: {S_SALES}; {S_STORE}; {S_FLPOP}. {PHOTO_CREDIT}. 내레이션: 한국어 합성 음성(Microsoft SunHi). 음악은 브라우저에서 실시간 합성.</p></section>

<section><div class="kicker">Sources</div><ul class="note"><li>{S_SALES}</li><li>{S_STORE}</li><li>{S_FLPOP}</li><li>{S_WRC}</li><li>{S_IX}</li><li>{S_AREA}</li><li>{PHOTO_CREDIT}</li></ul></section>
</main><script>{JS}</script></body></html>'''
(R/"output/report.html").write_text(html,encoding="utf-8"); (R/"output/video/intro.html").write_text(html,encoding="utf-8")
w=lambda n,s:(R/n).write_text(s,encoding="utf-8")
w("data_quality.md",f"# 데이터 품질 (레드, 2회차)\n\n수집 분기: {', '.join(Q)} · 호출일 {called} · 실패 호출 0건\n\n| 파일 | 데이터셋 | 행 수 |\n|---|---|---|\n"+"".join(f"| {f['file']} | {f['dataset']} | {f['rows']:,} |\n" for f in man['files'])+f"\n- 추정매출 (분기·상권) 중복 {qa['dup_sales']}건, 매출 결측 {qa['null_amt']}건\n- 분기별 상권 수: {qa['trdar_per_q']}\n- 8분기 모두 존재 {qa['trdar_all8']}/{qa['trdar_any']}개\n- 점포·유동인구: 2회차에 8개 분기 전량 재수집 ({qa['store_q']})\n- 직장·상주인구: 분기 파라미터 무시 → 기준분기 {Q[0]}만 사용 (가용 분기 {qa['wrc_q_available']}개)\n- 소득소비-상권 API 서버 오류로 미수집\n")
w("hypotheses.md",f"# 가설 (블루, 2회차)\n\n| 가설 | 검증 방법 | 결과 | 근거 데이터 | 채택 |\n|---|---|---|---|---|\n| H1 서울 커피 시장은 정체 | 8분기 전체 합 성장률 | {pct(r['seoul_growth'])} | sales_trdar.csv | 채택 |\n| H2 고성장 상권 다수는 지속성·수익성이 약하다 | 1단계 스크리닝 통과율 | {qa['universe']}곳 중 {qa['screened']}곳 통과 | scored_trdar.csv | 채택 |\n| H3 25Q3 레벨 점프는 시장 공통 | 시장 QoQ 중앙값 | {pct(mq['20253'])} | sales_trdar.csv | 기각 |\n| H4 코엑스 성장은 점포 증가 때문 | 매출 분해 | 점포 {pct(dec['store_growth'])}, 점포당 {pct(dec['sps_growth'])} | store_trdar.csv | 기각 |\n| H5 선정 결과는 가중치에 민감 | 4종 가중치 순위 | {r['pick_rank_all_weights']} | scored_trdar.csv | 기각 |\n| H6 수요는 평일 오전 중심 | 시간대·요일 비중 | 06~14시 {am*100:.0f}%, 평일 {wk*100:.0f}% | sales_trdar.csv | 채택 |\n")
w("risks.md","# 리스크 (그린, 2회차)\n\n| ID | 유형 | 내용 | 심각도 | 상태 |\n|---|---|---|---|---|\n| R1 | 오류 | 소표본 상권의 극단 성장률 | 상 | 해결(점포 5개+, 절단) |\n| R2 | 가드레일 | 추정매출을 실매출로 오인 | 상 | 해결(표기, 상대지표) |\n| R3 | 오류 | 25Q3 레벨 점프(기저효과) | 상 | 해결(지속성 조건, 시장 대비, 분해) |\n| R4 | 가드레일 | 사후 컷오프(20%) | 상 | 해결(3단계 사전 규칙) |\n| R5 | 오류 | 손익·민감도 계산식 불일치 | 중 | 해결(단일 식) |\n| R6 | 병목 | 점포 3개 분기만 수집 | 중 | 해결(8분기 재수집) |\n| R7 | 오류 | 직장인구 분기 필터 무시 | 중 | 해결(기준분기 필터) |\n| R8 | 병목 | 임대료·객단가 부재 | 중 | 남은 한계(가정+실사) |\n| R9 | 병목 | 점포당 매출 상승 원인 미상 | 중 | 남은 한계(실사 항목) |\n")
w("solutions.md","# 솔루션 (브라운, 2회차)\n\nR3·R4: 1단계(지속성 4/4, 점포당 매출 중앙값 이상, 순개업 ≥ 0) → 2단계(성장 중심 z 가중합) → 3단계(가중치 4종 평균 순위, 동률 시 유동인구 증가)로 규칙을 먼저 선언. R5: 영업이익 = 매출×0.6 − 고정비(3년차 매출×40%) 단일 식. R6·R7: 재수집·기준분기 필터.\n")
w("final_solution.md",f"# 베스트 솔루션 (실버+블랙, 2회차)\n\n- 입지: {pk['gu']} {pk['dong']} {pk['name']} (성장 {pct(pk['growth'])}, 가중치 4종 순위 {r['pick_rank_all_weights']})\n- 컨셉: 평일 오전 테이크아웃 중심 25평, 소회의 좌석\n- 메뉴: 배치 브루·시그니처 라떼·핸드드립\n- 투자 {eok(inv)}(보증금 별도), 3년차 매출 {eok(base)}, 영업이익 {eok(pl[2]['op'])}, 회수 약 {pay:.1f}년 (가정)\n")
w("design_spec.md",f"# 디자인 (옐로우, 2회차)\n\n깔끔한 에디토리얼: 손글씨·일본어 제거, Pretendard 단일 서체(제목 600, 숫자 200~300). 종이색 #F6F4F0, 잉크 #24221F, 커피 #7A5A44, 얇은 1px 선, 각진 카드(4px). 영상: 오타루 카페 실사 사진 배경(Ken Burns 확대, 어둡게), 장면당 6초 페이드, 큰 숫자 + 한 줄 설명, 성우 없음, 잔잔한 합성 피아노. {PHOTO_CREDIT}\n")
print("built", pk["name"], f"payback {pay:.1f}")
