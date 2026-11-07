"""3회차 보고서·영상 빌드 (블랙 재구성): 지도, 서울 대비 고객 프로필, 경쟁, 월세 상한."""
import json, pathlib, sys, csv, base64, math
import pandas as pd
R=pathlib.Path(sys.argv[1]); r=json.load(open(R/"analysis/result.json",encoding="utf-8"))
man=json.load(open(R/"data/manifest.json",encoding="utf-8")); called=man["files"][0]["called"]
Q=r["quarters"]; REC=Q[:4]; ql=lambda q:f"{q[:4]}년 {q[4]}분기"; Q0,Q7,Q3=ql(Q[0]),ql(Q[-1]),ql(Q[3]); qa=r["qa"]; pk=r["pick"]; dec=r["decomp"]; t5=r["top5"]
SRC=lambda name,oa,per:f"서울시 상권분석서비스({name}) {oa} / {per} / 호출일 {called}"
S_SALES=SRC("추정매출-상권","OA-15572",f"{Q7}~{Q0}"); S_SALES4=SRC("추정매출-상권","OA-15572",f"{Q3}~{Q0} 4개 분기 합")
S_STORE=SRC("점포-상권","OA-15577",f"{Q7}~{Q0}"); S_FL=SRC("길단위인구-상권","OA-15568",f"{Q7}~{Q0}"); S_AREA=SRC("영역-상권","OA-15560","좌표·행정구역")
eok=lambda v:f"{v/1e8:,.1f}억 원"; man_=lambda v:f"{v/1e4:,.0f}만 원"; pct=lambda v:f"{v*100:+.1f}%"; pp=lambda v:f"{v*100:+.1f}%p"
s=pd.read_csv(R/"data/sales_trdar.csv",dtype={"TRDAR_CD":str,"STDR_YYQU_CD":str}); st=pd.read_csv(R/"data/store_trdar.csv",dtype={"TRDAR_CD":str,"STDR_YYQU_CD":str})
ar=pd.read_csv(R/"data/area.csv",dtype={"TRDAR_CD":str}); sc=pd.read_csv(R/"analysis/scored_trdar.csv",dtype={"TRDAR_CD":str})
x=s[s.STDR_YYQU_CD.isin(REC)]
GR={"time":[("06_11","06–11시"),("11_14","11–14시"),("14_17","14–17시"),("17_21","17–21시"),("21_24","21–24시")],
    "age":[("20","20대"),("30","30대"),("40","40대"),("50","50대"),("60_ABOVE","60대+")]}
def mix(df):
    o={}
    t={k:df[f"TMZON_{k}_SELNG_AMT"].sum() for k,_ in GR["time"]+[("00_06","")]}; T=sum(t.values()); o["time"]={k:t[k]/T for k,_ in GR["time"]}
    a={k:df[f"AGRDE_{k}_SELNG_AMT"].sum() for k,_ in GR["age"]+[("10","")]}; A=sum(a.values()); o["age"]={k:a[k]/A for k,_ in GR["age"]}
    o["weekend"]=(df.SAT_SELNG_AMT.sum()+df.SUN_SELNG_AMT.sum())/df[["MON_SELNG_AMT","TUES_SELNG_AMT","WED_SELNG_AMT","THUR_SELNG_AMT","FRI_SELNG_AMT","SAT_SELNG_AMT","SUN_SELNG_AMT"]].sum().sum()
    o["ticket"]=df.THSMON_SELNG_AMT.sum()/df.THSMON_SELNG_CO.sum(); return o
M,SE=mix(x[x.TRDAR_CD==pk["code"]]),mix(x)
aft=M["time"]["14_17"]+M["time"]["17_21"]; aftS=SE["time"]["14_17"]+SE["time"]["17_21"]
a34=M["age"]["30"]+M["age"]["40"]; a34S=SE["age"]["30"]+SE["age"]["40"]; tk=M["ticket"]/SE["ticket"]
y=st[st.STDR_YYQU_CD==Q[0]]; py=y[y.TRDAR_CD==pk["code"]].iloc[0]; frc=py.FRC_STOR_CO/py.SIMILR_INDUTY_STOR_CO; frcS=y.FRC_STOR_CO.sum()/y.SIMILR_INDUTY_STOR_CO.sum()
q=pk["quarterly"]; before=sum(q[:4])/4; after=sum(q[4:])/4; jump_q=ql(Q[3])
# 손익 (가정, 단일 모델): 영업이익 = 매출×(1−원가30%−기타10%) − 인건비(인원 기반) − 월세×12
COGS,OTH=0.30,0.10; HAIR=0.8                      # 신규점은 상권 점포당 평균의 80%를 3년차 상한으로 (평균은 대형점이 끌어올림)
FTE,WAGE=3.5,280e4                                 # 평일 2교대 각 1~2명 + 주말 보강 = 풀타임 환산 3.5명, 1인 월 인건비 총액 280만 원 (가정)
labor=FTE*WAGE*12; ramp=[0.7,0.9,1.0]
PY=20; INV={f"인테리어 ({PY}평 × 평당 300만 원)":PY*300e4,"장비·집기":5000e4,"오픈 비용·초기 재고":2000e4}; inv=sum(INV.values()); DEP=1.2e8
def model(sps_q,rent,scale=1.0):
    base=sps_q*4*HAIR; rows=[]; cum=0; pay=None
    for i,k in enumerate(ramp):
        rev=base*k*scale; op=rev*(1-COGS-OTH)-labor-rent*12; rows.append({"y":i+1,"k":k,"rev":rev,"op":op})
        if pay is None and op>0 and cum+op>=inv: pay=i+(inv-cum)/op
        cum+=op
    if pay is None:
        op=rows[-1]["op"]; pay=3+(inv-cum)/op if op>0 else None
    return base,rows,pay
def ceiling(sps_q,hair=None,fte=None,inv_=None):  # 3년 안에 투자를 회수하는 최대 월세 (같은 모델)
    h=HAIR if hair is None else hair; f=FTE if fte is None else fte; iv=inv if inv_ is None else inv_
    base=sps_q*4*h; return (sum(base*k for k in ramp)*(1-COGS-OTH)-3*f*WAGE*12-iv)/36
FORMATS=[("30평 라운지",4.5,30*300e4+6000e4+2500e4),("20평 컴팩트 라운지 (제안)",3.5,20*300e4+5000e4+2000e4),("15평 테이크아웃",2.5,15*300e4+3000e4+1500e4)]
rent_ceiling=ceiling(pk["sales_per_store_q"]); RENT=round(rent_ceiling*0.85/1e5)*1e5   # 기준 시나리오 월세 = 상한의 85%
base,pl,pay=model(pk["sales_per_store_q"],RENT); _,pl_lo,pay_lo=model(pk["sales_per_store_q"],RENT,0.8)
_,_,pay_at_ceil=model(pk["sales_per_store_q"],rent_ceiling)
STOP=base*ramp[0]/12*0.8   # 오픈 6개월 월매출이 1년차 계획의 80% 미만이면 철수 검토
eok2=lambda v:f"{v/1e8:,.2f}억 원"
def mw(v):
    m=round(v/1e4); e,r_=divmod(m,10000)
    return (f"{e}억 {r_:,}만 원" if r_ else f"{e}억 원") if e else f"{m:,}만 원"
def josa(w,a,b): c=w[-1]; return w+(a if ('가'<=c<='힣' and (ord(c)-0xAC00)%28) or c.isdigit() and c in "0136781" else b)
# ---------- 지도 ----------
X0,X1,Y0,Y1=ar.XCNTS_VALUE.min(),ar.XCNTS_VALUE.max(),ar.YDNTS_VALUE.min(),ar.YDNTS_VALUE.max(); W,H=800,int(800*(Y1-Y0)/(X1-X0))
px=lambda v:(v-X0)/(X1-X0)*W; py_=lambda v:H-(v-Y0)/(Y1-Y0)*H
coord=ar.set_index("TRDAR_CD")[["XCNTS_VALUE","YDNTS_VALUE"]]
allc=[c for c in s.TRDAR_CD.unique() if c in coord.index]; cand=set(sc.TRDAR_CD); top=[t["code"] for t in t5]
def dots(cls):
    out=[]
    for c in allc:
        k="pick" if c==pk["code"] else "top" if c in top else "cand" if c in cand else "all"
        X,Y=coord.loc[c]; rr={"pick":7,"top":4.5,"cand":3.2,"all":1.8}[k]
        out.append(f'<circle class="d {k}" cx="{px(X):.1f}" cy="{py_(Y):.1f}" r="{rr}"/>')
    return "".join(out)
DOTS=dots("")
pX,pY=px(coord.loc[pk["code"]].XCNTS_VALUE),py_(coord.loc[pk["code"]].YDNTS_VALUE)
labels="".join(f'<text class="lbl{" pk" if t["code"]==pk["code"] else ""}" x="{px(coord.loc[t["code"]].XCNTS_VALUE)+9:.0f}" y="{py_(coord.loc[t["code"]].YDNTS_VALUE)+4:.0f}">{t["name"]}</text>' for t in t5 if t["code"] in coord.index)
MAP=f'<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-label="서울 커피 상권 지도"><g class="mapg">{DOTS}{labels}</g></svg>'
# ---------- 차트 ----------
def line(vals,labels,hl_from=None,h=200,w=640):
    m=max(vals)*1.1; n=len(vals); xs=[40+i*(w-60)/(n-1) for i in range(n)]; ys=[h-30-(v/m)*(h-60) for v in vals]
    path=" ".join(f'{"M" if i==0 else "L"}{xs[i]:.0f},{ys[i]:.0f}' for i in range(n))
    av=f'<line x1="{xs[0]}" x2="{xs[3]}" y1="{h-30-(before/m)*(h-60):.0f}" y2="{h-30-(before/m)*(h-60):.0f}" class="avg"/><line x1="{xs[4]}" x2="{xs[7]}" y1="{h-30-(after/m)*(h-60):.0f}" y2="{h-30-(after/m)*(h-60):.0f}" class="avg"/>'
    pts="".join(f'<circle cx="{xs[i]:.0f}" cy="{ys[i]:.0f}" r="4" class="pt"/><text x="{xs[i]:.0f}" y="{ys[i]-10:.0f}" class="vl" text-anchor="middle">{vals[i]/1e8:.1f}</text><text x="{xs[i]:.0f}" y="{h-8}" class="ax" text-anchor="middle">{labels[i]}</text>' for i in range(n))
    return f'<svg viewBox="0 0 {w} {h}" role="img"><rect x="{(xs[3]+xs[4])/2:.0f}" y="10" width="{xs[7]-(xs[3]+xs[4])/2+20:.0f}" height="{h-40}" class="band"/>{av}<path d="{path}" class="ln"/>{pts}</svg>'
def diverge(items,h_row=34,w=720):
    cx,mb=330,150; rows="";mx=max(abs(a-b) for _,a,b in items) or 1
    for i,(lab,a,b) in enumerate(items):
        y=i*h_row+10; d=a-b; ww=abs(d)/mx*mb; x0=cx if d>=0 else cx-ww
        rows+=(f'<text x="0" y="{y+16}" class="ax">{lab}</text><rect x="{x0:.0f}" y="{y+4}" width="{max(ww,1):.0f}" height="16" class="{"pos" if d>=0 else "neg"}"/>'
               f'<text x="{(cx+ww+8) if d>=0 else (cx-ww-8):.0f}" y="{y+16}" class="vl" text-anchor="{"start" if d>=0 else "end"}">{d*100:+.1f}%p</text>'
               f'<text x="{w-2}" y="{y+16}" class="ax" text-anchor="end">{a*100:.0f}% / {b*100:.0f}%</text>')
    return f'<svg viewBox="0 0 {w} {len(items)*h_row+16}" role="img"><line x1="{cx}" x2="{cx}" y1="4" y2="{len(items)*h_row+12}" class="axis"/>{rows}</svg>'
qs=[f"{qq[2:4]}.{qq[4]}Q" for qq in Q[::-1]]
prof=[(l,M["time"][k],SE["time"][k]) for k,l in GR["time"]]+[("주말(토·일)",M["weekend"],SE["weekend"])]+[(l,M["age"][k],SE["age"][k]) for k,l in GR["age"]]
toprows="".join(f'<tr class="{"hl" if t["code"]==pk["code"] else ""}"><td>{i+1}</td><td>{t["name"]}<small>{t["gu"]} {t["dong"]}</small></td><td>{pct(t["growth"])}</td><td>{t["stores"]}</td><td>{eok(t["sales_per_store_q"])}</td><td>{t["net_open"]:+.1f}%p</td><td>{pct(t["flpop_growth"])}</td><td>{" · ".join(str(v) for v in t["ranks"].values())}</td></tr>' for i,t in enumerate(t5))
plrows="".join(f'<tr><td>{p["y"]}년차</td><td>{p["k"]*100:.0f}%</td><td>{eok(p["rev"])}</td><td>{eok(p["rev"]*(COGS+OTH))}</td><td>{eok(labor)}</td><td>{eok(RENT*12)}</td><td><b>{eok(p["op"])}</b></td></tr>' for p in pl)
invrows="".join(f'<tr><td>{k}</td><td>{mw(v)}</td></tr>' for k,v in INV.items())
sec_ceil=ceiling([t for t in t5 if t["code"]!=pk["code"]][0]["sales_per_store_q"])
scen=[(RENT*0.8,"월세 낮음"),(RENT,"기준"),(rent_ceiling,"상한")]
fmtrows="".join(f'<tr class="{"hl" if "제안" in n else ""}"><td>{n}</td><td>{f}명</td><td>{mw(iv)}</td><td>{mw(max(0,ceiling(pk["sales_per_store_q"],0.8,f,iv)))}</td><td>{mw(max(0,ceiling(pk["sales_per_store_q"],1.0,f,iv)))}</td></tr>' for n,f,iv in FORMATS)
scenrows="".join(f'<tr><td>{lab}</td><td>{mw(rv)}</td><td>{eok2(model(pk["sales_per_store_q"],rv)[1][0]["op"])}</td><td>{eok2(model(pk["sales_per_store_q"],rv)[1][2]["op"])}</td><td>{model(pk["sales_per_store_q"],rv)[2]:.1f}년</td></tr>' for rv,lab in scen)
second=[t for t in t5 if t["code"]!=pk["code"]][0]
# ---------- 영상 ----------
PH1="https://upload.wikimedia.org/wikipedia/commons/b/b7/Jazz_Cafe_%40_Otaru.jpg"; PH2="https://upload.wikimedia.org/wikipedia/commons/5/58/Lamps_in_Otaru-Station.jpg"
CREDIT='사진: "Jazz Cafe @ Otaru", MIKI Yoshihito, <a href="https://creativecommons.org/licenses/by/2.0/">CC BY 2.0</a>; "Lamps in Otaru-Station", snow rabbit, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC BY-SA 2.0</a>; via Wikimedia Commons'
SC=[("all",f"서울의 커피 상권 {qa['trdar_all8']:,}곳. 지난 1년 시장은 {r['seoul_growth']*100:.0f}% 성장했어요.",f"최근 4분기 매출 ÷ 직전 4분기 · 카드결제 기반 추정 · {Q7}~{Q0}"),
    ("cand",f"4분기 연속 성장하고, 수익성까지 받쳐 주는 곳은 {qa['screened']}곳이에요.",f"점포 5개 이상 · 점포당 매출 중앙값 이상 · 8분기 평균 순개업 0 이상"),
    ("pick","코엑스 상권은 작년 3분기에 한 단계 올라선 뒤, 그 수준을 지켰어요.",f"분기 평균 매출 {before/1e8:.1f}억 → {after/1e8:.1f}억 원 · 점포당 매출 {pct(dec['sps_growth'])} · 유동인구 {pct(dec['flpop_growth'])}"),
    ("prof",f"손님은 오후와 주말에 많고, 한 번에 {tk:.1f}배를 써요.",f"14–21시 {pp(aft-aftS)} · 주말 {pp(M['weekend']-SE['weekend'])} · 30대 {pp(M['age']['30']-SE['age']['30'])} · 40대 {pp(M['age']['40']-SE['age']['40'])} · 1회 결제 {M['ticket']:,.0f}원"),
    ("photo","그래서 오후에 머무는 20평 라운지를 제안해요.","4–6인 테이블 · 단체·선물 주문 카운터 · 주말 운영 강화 · 프랜차이즈 비중 높은 상권에서 체류 경험으로 차별화"),
    ("photo2",f"월세 {mw(rent_ceiling)} 이하면 3년 안에 투자를 회수해요.",f"투자 {mw(inv)} · 월세 {mw(RENT)}일 때 3년차 영업이익 {eok2(pl[2]['op'])}, 회수 {pay:.1f}년 · 모두 가정 기반")]
NAR=[a for _,a,_ in SC]
film_sc="".join(f'<div class="sc" data-t="{i*5}" data-mode="{m}"><p>{a}</p><small>{b}</small><audio class="nar" preload="auto" src="data:audio/mpeg;base64,{base64.b64encode((R/f"output/video/v{i+1}.mp3").read_bytes()).decode()}"></audio></div>' for i,(m,a,b) in enumerate(SC)) if all((R/f"output/video/v{i+1}.mp3").exists() for i in range(6)) else ""
mini=line(q,qs,h=170,w=560)
prof_svg=diverge([(l,a,b) for l,a,b in prof if l in ("14–17시","17–21시","06–11시")]+[("주말(토·일)",M["weekend"],SE["weekend"]),("30대",M["age"]["30"],SE["age"]["30"]),("40대",M["age"]["40"],SE["age"]["40"])])
FILM=f'''<div id="film" data-mode="all"><div class="ph p1" style="background-image:url('{PH1}')"></div><div class="ph p2" style="background-image:url('{PH2}')"></div>
<div class="fmap">{MAP}</div><div class="fchart c3">{mini}</div><div class="fchart c4">{prof_svg}</div>
<div class="loc">서울 커피 상권 분석 · 코엑스 상권</div>{film_sc}<div class="bar"><i></i></div><button id="play">▶ 재생</button></div>'''
CSS=open(R/"analysis/style3.css",encoding="utf-8").read(); JS=open(R/"analysis/film3.js",encoding="utf-8").read()
HEAD=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__T__</title><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"><style>{CSS}</style></head>'''
html=HEAD.replace("__T__","코엑스 상권 출점 전략")+f'''<body>
<header class="cover"><div class="wrap2"><div class="kicker">Seoul Coffee District Strategy · {Q0} 기준</div>
<h1>다음 매장은 코엑스 상권,<br>오후에 머무는 20평 라운지입니다</h1>
<p class="lede">서울 커피 상권 {qa['trdar_all8']:,}곳을 같은 규칙으로 걸러 한 곳을 골랐습니다. 이 상권의 손님은 서울 평균보다 오후와 주말에 오고, 한 번에 {tk:.1f}배를 씁니다.</p>
<div class="stats"><div><b>{pct(pk['growth'])}</b><span>최근 4분기 매출 성장 (서울 {pct(r['seoul_growth'])})<br>{jump_q[2:]} 한 단계 상승 후 유지</span></div><div><b>{tk:.1f}배</b><span>1회 결제 금액<br>{M['ticket']:,.0f}원 vs 서울 {SE['ticket']:,.0f}원</span></div><div><b>{eok2(pl[2]['op'])}</b><span>3년차 영업이익<br>(월세 {mw(RENT)} 가정)</span></div><div><b>{mw(rent_ceiling)}</b><span>출점 가능 월세 상한<br>(3년 회수 기준 Go/No-Go)</span></div></div>
<p class="source-caption">출처: {S_SALES}; {S_SALES4}. 매출은 카드결제 기반 추정치, 손익은 가정치.</p></div>
<div class="cover-map">{MAP}<p class="source-caption">점: 커피-음료 매출이 있는 상권 · 진한 점: 1단계 통과 {qa['screened']}곳 · 큰 점: 코엑스. 좌표: {S_AREA}</p></div></header>
<main>
<section><div class="sh"><div class="kicker">01 · 결론</div><h2>세 가지 판단</h2></div>
<ol class="three"><li><b>어디에</b><p>코엑스 상권(강남구 삼성1동). {qa['universe']}개 상권 중 지속성·수익성 조건을 통과한 {qa['screened']}곳에서, 가중치를 네 가지로 바꿔도 2위 밖으로 밀리지 않았습니다.</p></li>
<li><b>무엇을</b><p>오후·주말 체류형 20평 컴팩트 라운지. 손님은 14–21시({pp(aft-aftS)}), 주말({pp(M['weekend']-SE['weekend'])}), 30대({pp(M['age']['30']-SE['age']['30'])})·40대({pp(M['age']['40']-SE['age']['40'])})가 서울 평균보다 많고, 1회 결제는 {tk:.1f}배입니다.</p></li>
<li><b>얼마에</b><p>투자 {mw(inv)}(보증금 별도). 월세 {mw(RENT)}이면 3년차 영업이익 {eok2(pl[2]['op'])}, 회수 {pay:.1f}년. 월세가 {josa(mw(rent_ceiling),'을','를')} 넘으면 3년 안에 회수가 안 되므로 출점하지 않습니다.</p></li></ol></section>

<section><div class="sh"><div class="kicker">02 · 선정 방법</div><h2>규칙을 먼저 정하고, 그 규칙대로 골랐습니다</h2></div>
<div class="grid2"><div><div class="step"><em>1</em><div><b>걸러내기</b><p>8개 분기 매출이 모두 있고 점포 5개 이상. 최근 4개 분기가 모두 직전 4분기 평균보다 높고, 점포당 매출 중앙값({eok(qa['sps_median'])}) 이상, 8분기 평균 순개업 0 이상.</p></div></div>
<div class="step"><em>2</em><div><b>점수 매기기</b><p>성장률 40 · 유동인구 증가 15 · 점포당 매출 20 · 순개업 10 · 직장인구 15. 지표마다 상하위 5%를 잘라 표준화.</p></div></div>
<div class="step"><em>3</em><div><b>흔들어 보기</b><p>가중치 네 가지(기본·수요·수익·균등)의 평균 순위로 최종 결정. 동률이면 유동인구가 늘어난 곳.</p></div></div></div>
<div><table class="funnel"><tbody><tr><td>커피 매출이 있는 상권</td><td>{qa['trdar_any']:,}</td></tr><tr><td>8개 분기 모두 존재</td><td>{qa['trdar_all8']:,}</td></tr><tr><td>점포 5개+ · 인구 데이터 결합</td><td>{qa['universe']:,}</td></tr><tr><td>1단계 통과</td><td>{qa['screened']}</td></tr><tr><td>최종</td><td>1</td></tr></tbody></table>
<p class="note">코엑스와 {josa(second['name'],'은','는')} 평균 순위가 같아 동률 규칙(유동인구 증가)으로 코엑스가 남았습니다. 다만 이 근거는 약합니다. 길단위 유동인구는 도로 위 보행자를 세기 때문에 실내 몰이 큰 코엑스는 면적당 {pk['flpop']/145396:.2f}명으로 다른 후보(3~9명)보다 크게 적게 잡힙니다. 그래서 두 곳을 06절과 같은 손익 모델로 다시 비교했습니다. 코엑스는 월세 {mw(rent_ceiling)}까지 3년 회수가 되지만, {josa(second['name'],'은','는')} 점포당 매출({eok(second['sales_per_store_q'])}/분기)이 낮아 월세가 0원이어도 20평 매장을 3년 안에 회수할 수 없습니다.</p></div></div>
<div class="wrap"><table><thead><tr><th>#</th><th>상권</th><th>4Q 성장</th><th>점포</th><th>점포당 분기매출</th><th>순개업(8Q)</th><th>유동인구</th><th>순위 기본·수요·수익·균등</th></tr></thead><tbody>{toprows}</tbody></table></div>
<p class="source-caption">출처: {S_SALES}; {S_STORE}; {S_FL}; 서울시 상권분석서비스(직장인구-상권) OA-15569 / {Q0} / 호출일 {called}. 재현: analysis/analyze.py</p></section>

<section><div class="sh"><div class="kicker">03 · 성장의 성격</div><h2>꾸준히 오른 게 아니라, 한 단계 올라선 뒤 그 자리를 지켰습니다</h2></div>
<div class="grid2"><div>{line(q,qs)}<p class="source-caption">코엑스 상권 분기별 커피 매출(억 원, 추정). 점선은 전·후 4분기 평균. 출처: {S_SALES}</p></div>
<div><p>분기 평균 매출은 {before/1e8:.1f}억 원에서 {after/1e8:.1f}억 원으로 올랐고, {jump_q} 이후 네 분기 동안 이 수준이 유지됐습니다. 같은 분기 서울 상권의 변화 중앙값은 {pct(qa['market_qoq_median'][Q[3]])}여서 시장 전체의 현상은 아닙니다.</p>
<p>성장을 나누면 점포 수 {pct(dec['store_growth'])}, 점포당 매출 {pct(dec['sps_growth'])}, 유동인구 {pct(dec['flpop_growth'])}입니다. 점포는 {jump_q}에 13개에서 14개로 1곳 늘었을 뿐이어서 성장의 대부분은 점포당 매출에서 나왔습니다. 다만 새로 연 1곳이 대형 점포였는지는 이 데이터로 알 수 없습니다.</p>
<p>서울시 상권변화지표는 코엑스를 '{pk['ix']}'으로 분류합니다(운영·폐업 점포의 평균 영업기간 기준). 매출 수준은 올랐지만 점포 구성은 크게 바뀌지 않았다는 뜻이라 위 분해와 맞습니다.</p>
<p class="caution"><b>이 데이터로 알 수 없는 것.</b> 점포당 매출이 왜 올랐는지(대형 점포 입점, 전시·행사 증가 등)는 상권 단위 데이터로 가려낼 수 없습니다. 3년 성장을 그대로 늘려 잡지 않고, 손익은 현재 수준을 상한으로 두었습니다. 원인은 출점 전 실사의 첫 확인 항목입니다.</p></div></div></section>

<section><div class="sh"><div class="kicker">04 · 고객</div><h2>서울 평균보다 오후·주말에 오고, 한 번에 {tk:.1f}배를 씁니다</h2></div>
<div class="grid2"><div>{diverge(prof)}<p class="source-caption">코엑스 상권 비중 − 서울 전체 비중(%p). 오른쪽은 코엑스 / 서울. 출처: {S_SALES4}</p></div>
<div><ul class="facts"><li><b>{aft*100:.0f}%</b> 14–21시 매출 비중 (서울 {aftS*100:.0f}%)</li><li><b>{M['weekend']*100:.0f}%</b> 주말 매출 비중 (서울 {SE['weekend']*100:.0f}%)</li><li><b>{M['age']['30']*100:.0f}·{M['age']['40']*100:.0f}%</b> 30대·40대 비중 (서울 {SE['age']['30']*100:.0f}·{SE['age']['40']*100:.0f}%)</li><li><b>{M['ticket']:,.0f}원</b> 1회 결제 금액 (서울 {SE['ticket']:,.0f}원)</li><li><b>{frc*100:.0f}%</b> 커피 점포 중 프랜차이즈 비중 (서울 {frcS*100:.0f}%)</li></ul>
<p>오전 출근 수요는 오히려 서울 평균보다 적습니다({pp(M['time']['06_11']-SE['time']['06_11'])}). 전시·쇼핑으로 찾아와 오후에 머무는 30–40대, 여럿이 함께 결제하는 손님이 이 상권의 핵심입니다.</p></div></div>
<p class="source-caption">1회 결제 금액 = 매출 ÷ 결제 건수. 프랜차이즈 비중 출처: {S_STORE} ({Q0}, 유사업종 점포 기준)</p></section>

<section><div class="sh"><div class="kicker">05 · 매장</div><h2>오후에 머무는 20평 라운지</h2></div>
<div class="cards"><div><b>공간</b><p>20평에 4인 테이블 위주 약 28석, 콘센트 좌석과 짐 보관. 오후 체류에 맞춰 좌석에 면적을 쓰고, 오전 비중이 낮으므로 테이크아웃 라인은 작게.</p><small>근거: 14–21시 {pp(aft-aftS)}, 06–11시 {pp(M['time']['06_11']-SE['time']['06_11'])}</small></div>
<div><b>주문</b><p>단체·선물 주문 카운터와 4–8잔 캐리어, 원두·드립백 선물 세트. 높은 1회 결제 금액에 맞춥니다.</p><small>근거: 1회 결제 {tk:.1f}배</small></div>
<div><b>메뉴</b><p>시그니처 라떼와 싱글 오리진 핸드드립을 중심에 두고, 오후용 디카페인·콜드브루. 프랜차이즈 비중이 높아 표준 메뉴로는 가격 경쟁이 되기 쉬우므로, 원두 선택과 체류 경험으로 차이를 둡니다.</p><small>근거: 프랜차이즈 {frc*100:.0f}% (서울 {frcS*100:.0f}%)</small></div>
<div><b>운영</b><p>2교대(10–16시 / 15–21시) 각 1~2명, 주말 보강으로 풀타임 환산 {FTE}명. 1인 월 인건비 {mw(WAGE)} 가정, 연 {eok2(labor)}.</p><small>근거: 주말 {pp(M['weekend']-SE['weekend'])}, 11–21시 매출 {(M['time']['11_14']+aft)*100:.0f}%</small></div></div>
<div class="photo" style="background-image:url('{PH1}')"><span>공간 분위기 참고 이미지</span></div><p class="source-caption">{CREDIT}</p></section>

<section><div class="sh"><div class="kicker">06 · 숫자</div><h2>월세 {mw(rent_ceiling)} 이하면 출점합니다</h2></div>
<p>3년차 매출은 이 상권 점포당 연 추정매출({eok2(pk['sales_per_store_q']*4)})의 80%인 {eok2(base)}로 잡았습니다. 평균은 대형 프랜차이즈 점포가 끌어올리고, 03절처럼 성장 원인을 모르기 때문에 신규점에는 보수적으로 적용했습니다. 월세 하나만 바꿔 가며 같은 모델로 계산합니다.</p>
<div class="grid2"><div><table><tbody>{invrows}<tr><td><b>투자 합계 (보증금 {mw(DEP)} 별도)</b></td><td><b>{mw(inv)}</b></td></tr></tbody></table></div>
<div class="stats small"><div><b>{pay:.1f}년</b><span>회수 기간 (월세 {mw(RENT)})</span></div><div><b>{pay_lo:.1f}년</b><span>매출 −20%일 때</span></div><div><b>{mw(rent_ceiling)}</b><span>월세 상한 (3년 회수)</span></div></div></div>
<p><b>매장 크기는 손익으로 정했습니다.</b> 같은 매출 가정에서 매장이 클수록 인건비와 투자비가 늘어 감당할 수 있는 월세가 줄어듭니다. 30평 라운지는 매출이 상권 평균에 도달해야만 성립해, 체류형 컨셉을 유지하면서 회수가 되는 20평을 제안합니다.</p>
<div class="wrap"><table><thead><tr><th>형태</th><th>인원(풀타임 환산)</th><th>투자</th><th>월세 상한 (매출 = 평균의 80%)</th><th>월세 상한 (매출 = 평균)</th></tr></thead><tbody>{fmtrows}</tbody></table></div>
<div class="wrap"><table><thead><tr><th>월세 시나리오 (20평)</th><th>월세</th><th>1년차 영업이익</th><th>3년차 영업이익</th><th>회수</th></tr></thead><tbody>{scenrows}</tbody></table></div>
<div class="wrap"><table><thead><tr><th>연차</th><th>도달률</th><th>매출</th><th>변동비(40%)</th><th>인건비</th><th>임차료 (월 {mw(RENT)})</th><th>영업이익</th></tr></thead><tbody>{plrows}</tbody></table></div>
<p class="caution"><b>중단 규칙.</b> 오픈 후 6개월 평균 월매출이 {mw(STOP)}(1년차 계획의 80%) 미만이면 운영 방식을 바꾸거나 철수를 검토합니다. 매출이 계획보다 20% 낮은 상태가 이어지면 회수에 {pay_lo:.1f}년이 걸리기 때문입니다.</p>
<p class="source-caption">매출 기준값 출처: {S_SALES}. 계산식(모든 표 공통): 영업이익 = 매출 × (1 − 원가 30% − 기타 10%) − 인건비({FTE}명 × 월 {mw(WAGE)}) − 월세 × 12. 월세 상한 = 3년 누적 영업이익이 투자 합계와 같아지는 월세. 원가율·인건비·투자비·도달률은 <b>가정</b>.</p></section>

<section><div class="sh"><div class="kicker">07 · 반론</div><h2>예상 질문과 답</h2></div>
<dl class="qa"><dt>성장이 한 분기에 몰렸는데, 3년 뒤도 성장한다고 볼 수 있나?</dt><dd>그래서 성장을 늘려 잡지 않았습니다. 한 단계 올라선 수준이 네 분기 유지됐고 유동인구도 늘었다는 점까지만 근거로 쓰고, 손익은 현재 수준을 상한으로 계산했습니다.</dd>
<dt>규칙을 결과에 맞춰 정한 것 아닌가?</dt><dd>1·2단계만 쓰면 {josa(second['name'],'이','가')} 1위이고, 코엑스는 3단계 동률 규칙으로 남았습니다. 그래서 규칙과 별개로 사업성을 다시 따졌습니다. 같은 손익 모델에서 {josa(second['name'],'은','는')} 어떤 월세에서도 20평 매장을 3년 안에 회수할 수 없고, 코엑스는 월세 {mw(rent_ceiling)}까지 가능합니다. 선정 규칙을 통과하고 사업성까지 남는 곳은 코엑스뿐입니다.</dd>
<dt>프랜차이즈가 많은 상권에 들어가도 되나?</dt><dd>프랜차이즈 비중({frc*100:.0f}%)이 서울({frcS*100:.0f}%)보다 높아 표준 메뉴의 가격 경쟁은 치열할 수 있습니다. 포화 여부는 이 데이터로 단정할 수 없어, 같은 메뉴로 경쟁하기보다 체류형 라운지라는 다른 형태로 들어갑니다.</dd>
<dt>실사에서 무엇이 나오면 출점하지 않나?</dt><dd>① 월세 {josa(mw(rent_ceiling),'을','를')} 넘는 매물만 있을 때, ② 점포당 매출 상승이 대형 점포 1곳의 효과로 확인돼 일반 점포 매출은 그대로일 때, ③ 20평 이상 체류형 매장을 낼 수 있는 자리가 없을 때 출점하지 않습니다.</dd>
<dt>추정매출을 믿을 수 있나?</dt><dd>절대 금액보다 같은 데이터 안의 상대 비교(성장률·서울 대비 비중)로 판단했습니다. 한계는 08절에 정리했습니다.</dd></dl></section>

<section id="limits"><div class="sh"><div class="kicker">08 · 데이터</div><h2>데이터 한계 및 보정 방법</h2></div>
<div class="wrap"><table><thead><tr><th>한계</th><th class="l">내용</th><th class="l">보정</th></tr></thead><tbody>
<tr><td>추정치</td><td class="l">추정매출은 카드결제 기반이라 현금·일부 간편결제가 빠짐</td><td class="l">절대 금액 대신 성장률·서울 대비 비중으로 판단</td></tr>
<tr><td>레벨 점프</td><td class="l">코엑스 매출은 {jump_q}에 한 번 올라선 뒤 평탄</td><td class="l">성장을 외삽하지 않고 현재 수준을 손익 상한으로</td></tr>
<tr><td>원인 미상</td><td class="l">점포당 매출 상승 원인을 상권 단위로 구분 불가</td><td class="l">실사 첫 항목으로 지정</td></tr>
<tr><td>유동인구</td><td class="l">길단위 유동인구는 도로 위 보행자만 세어 실내 몰이 큰 코엑스는 크게 적게 잡힘(면적당 {pk['flpop']/145396:.2f}명, 다른 후보 3~9명)</td><td class="l">절대값은 쓰지 않고 증가율만 참고, 동률 판단은 06절 사업성 비교로 보완</td></tr>
<tr><td>매출 기준</td><td class="l">점포당 매출은 상권 평균이라 대형점이 끌어올림(점포별 분포 없음)</td><td class="l">신규점은 평균의 80%로 보수 적용, 월세 시나리오로 민감도 제시</td></tr>
<tr><td>상권 수 변동</td><td class="l">분기별 상권 {min(qa['trdar_per_q'].values()):,}~{max(qa['trdar_per_q'].values()):,}개</td><td class="l">8개 분기 모두 있는 {qa['trdar_all8']:,}개만 사용</td></tr>
<tr><td>소표본</td><td class="l">점포 1~4개 상권의 극단값</td><td class="l">점포 5개 이상, 지표별 상하위 5% 절단</td></tr>
<tr><td>분기 파라미터</td><td class="l">직장인구 API는 분기 지정이 무시됨</td><td class="l">기준분기 컬럼으로 {Q0}만 사용</td></tr>
<tr><td>코드 체계</td><td class="l">상권코드와 행정동코드가 다름</td><td class="l">계산은 상권코드, 행정구역은 영역-상권 매핑으로 표기만</td></tr>
<tr><td>없는 데이터</td><td class="l">임대료·인건비·객단가 원가는 API에 없음, 소득소비-상권 API 서버 오류</td><td class="l">가정으로 분리 표기, 월세 상한으로 실사 판단 기준화</td></tr>
</tbody></table></div><p class="source-caption">품질 점검: 추정매출 {qa['rows_sales']:,}행, 중복 {qa['dup_sales']}건, 결측 {qa['null_amt']}건, 실패 호출 0건, 원본 raw/ 보존. 출처: {S_SALES}</p></section>

<section><div class="sh"><div class="kicker">09 · 실행</div><h2>실행 로드맵</h2></div>
<ol class="road"><li><b>1분기</b> 삼성1동 매물 실사: 월세 {mw(rent_ceiling)} 이하 20평 매물 확보 여부, 점포당 매출 상승 원인 확인 → 07절 세 가지 No-Go 조건으로 판정</li><li><b>2분기</b> 계약, 20평 라운지 설계, 단체·선물 주문 채널 준비</li><li><b>3분기</b> 오픈, POS로 시간대·1회 결제 금액 검증, 손익 가정 갱신</li><li><b>4분기~</b> 같은 규칙으로 데이터를 갱신해 2호점 재평가 ({josa(second['name'],'은','는')} 소형 테이크아웃 형태로 별도 검토)</li></ol></section>

<section><div class="sh"><div class="kicker">10 · 영상</div><h2>30초 요약</h2></div>{FILM}
<p class="source-caption">영상 속 수치 출처: {S_SALES}; {S_STORE}; {S_FL}. {CREDIT}. 내레이션: 한국어 합성 음성(Microsoft SunHi). 음악: 브라우저 실시간 합성.</p></section>
</main><footer><p>서울 열린데이터광장 상권분석서비스 기반 · 호출일 {called} · 분석 코드 analysis/analyze.py</p></footer>
<script>{JS}</script></body></html>'''
(R/"output/report.html").write_text(html,encoding="utf-8")
video=HEAD.replace("__T__","코엑스 상권 30초")+f'<body class="solo"><main>{FILM}<p class="source-caption">출처: {S_SALES}; {S_STORE}; {S_FL}. {CREDIT}. 내레이션: 한국어 합성 음성(Microsoft SunHi).</p></main><script>{JS}</script></body></html>'
(R/"output/video/intro.html").write_text(video,encoding="utf-8")
(R/"output/video/narration.txt").write_text("\n".join(NAR),encoding="utf-8")
w=lambda n,t:(R/n).write_text(t,encoding="utf-8")
w("final_solution.md",f"# 베스트 솔루션 (실버+블랙, 4회차)\n\n- 입지: {pk['gu']} {pk['dong']} {pk['name']}\n- 컨셉: 오후·주말 체류형 20평 컴팩트 라운지 (14–21시 {pp(aft-aftS)}, 주말 {pp(M['weekend']-SE['weekend'])}, 30–40대 {pp(a34-a34S)}, 1회 결제 {tk:.1f}배)\n- 투자 {mw(inv)}, 월세 {mw(RENT)} 기준 3년차 영업이익 {eok2(pl[2]['op'])}, 회수 {pay:.1f}년(−20% 시 {pay_lo:.1f}년), 월세 상한 {mw(rent_ceiling)}(3년 회수), 중단 규칙: 6개월 월매출 {mw(STOP)} 미만\n- 성장은 외삽하지 않음(레벨 점프 후 유지)\n")
print("ok",f"ceil {rent_ceiling/1e4:.0f} rent {RENT/1e4:.0f} sec_ceil {sec_ceil/1e4:.0f}",round(tk,2),round(aft-aftS,3),f"pay {pay:.2f}/{pay_lo:.2f}",f"rent {rent_ceiling/1e4:.0f}만",f"inv {inv/1e8:.2f}",f"op3 {pl[2]['op']/1e8:.2f}")
