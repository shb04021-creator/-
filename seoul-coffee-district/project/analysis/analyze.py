"""블루·그린·브라운 2회차 분석. 같은 data/ 입력이면 같은 결과를 낸다.
선정 규칙: 1단계 스크리닝 → 2단계 성장 중심 종합점수(가중치 4종) → 3단계 4종 평균 순위 최소, 동률 시 유동인구 증가.
2회차에 3단계를 추가함. 동률의 사업성 보완 비교는 build3.py 손익 모델에서 수행."""
import pandas as pd, numpy as np, json, pathlib, sys
R=pathlib.Path(sys.argv[1]); D=R/"data"; A=R/"analysis"
Q=json.load(open(D/"manifest.json",encoding="utf-8"))["quarters"]; Q0=Q[0]; REC,PRI=Q[:4],Q[4:]
rd=lambda n:pd.read_csv(D/n,dtype={"TRDAR_CD":str,"STDR_YYQU_CD":str,"ADSTRD_CD":str})
s,st,fl,wr,ix,ar=rd("sales_trdar.csv"),rd("store_trdar.csv"),rd("flpop_trdar.csv"),rd("wrcpop_trdar.csv"),rd("ix_trdar.csv"),rd("area.csv")
qa={"rows_sales":len(s),"dup_sales":int(s.duplicated(["STDR_YYQU_CD","TRDAR_CD"]).sum()),"null_amt":int(s.THSMON_SELNG_AMT.isna().sum()),
    "trdar_per_q":s.groupby("STDR_YYQU_CD").TRDAR_CD.nunique().to_dict(),"store_q":sorted(st.STDR_YYQU_CD.unique().tolist()),"flpop_q":sorted(fl.STDR_YYQU_CD.unique().tolist()),
    "wrc_q_used":Q0,"wrc_q_available":int(wr.STDR_YYQU_CD.nunique())}
P=s.pivot_table(index="TRDAR_CD",columns="STDR_YYQU_CD",values="THSMON_SELNG_AMT",aggfunc="sum")
full=P.dropna(); qa["trdar_any"]=len(P); qa["trdar_all8"]=len(full)
SP=st.pivot_table(index="TRDAR_CD",columns="STDR_YYQU_CD",values="STOR_CO",aggfunc="sum")
FP=fl.pivot_table(index="TRDAR_CD",columns="STDR_YYQU_CD",values="TOT_FLPOP_CO",aggfunc="sum")
OP=st.pivot_table(index="TRDAR_CD",columns="STDR_YYQU_CD",values="OPBIZ_RT"); CL=st.pivot_table(index="TRDAR_CD",columns="STDR_YYQU_CD",values="CLSBIZ_RT")
g=pd.DataFrame(index=full.index)
g["sales_recent4q"]=full[REC].sum(1); g["sales_prior4q"]=full[PRI].sum(1); g["growth"]=g.sales_recent4q/g.sales_prior4q-1
g["sustain"]=(full[REC].gt(full[PRI].mean(1),axis=0)).sum(1)          # 최근 4개 분기 중 직전 4분기 평균을 넘은 분기 수
g["stores"]=SP[Q0]; g["store_growth"]=SP[REC].mean(1)/SP[PRI].mean(1)-1
g["sales_per_store_q"]=full[REC].mean(1)/SP[REC].mean(1)                # 최근 4분기 평균 분기매출 ÷ 평균 점포수
g["net_open"]=(OP[Q]-CL[Q]).mean(1)                                     # 8분기 평균 개업률−폐업률 (%p)
g["flpop"]=FP[REC].mean(1); g["flpop_growth"]=FP[REC].mean(1)/FP[PRI].mean(1)-1
g["wrcpop"]=wr[wr.STDR_YYQU_CD==Q0].set_index("TRDAR_CD").TOT_WRC_POPLTN_CO
g["ix"]=ix.set_index("TRDAR_CD").TRDAR_CHNGE_IX_NM
g=g.join(ar.set_index("TRDAR_CD")[["TRDAR_CD_NM","TRDAR_SE_CD_NM","SIGNGU_CD_NM","ADSTRD_CD_NM"]])
u=g.dropna(subset=["stores","sales_per_store_q","net_open","flpop","flpop_growth","wrcpop"]); u=u[u.stores>=5].copy(); qa["universe"]=len(u)
# 1단계 스크리닝 (사전 선언): 성장 지속(4/4) · 점포당 매출 중앙값 이상 · 순개업 ≥ 0
med=u.sales_per_store_q.median(); qa["sps_median"]=float(med)
sc=u[(u.sustain==4)&(u.sales_per_store_q>=med)&(u.net_open>=0)].copy(); qa["screened"]=len(sc)
# 2단계 성장 중심 종합점수 (z, 윈저라이즈 5~95%)
def z(df,c):
    x=df[c].clip(df[c].quantile(.05),df[c].quantile(.95)); return (x-x.mean())/x.std()
sc["log_wrc"]=np.log1p(sc.wrcpop)
WS={"base":{"growth":.40,"flpop_growth":.15,"sales_per_store_q":.20,"net_open":.10,"log_wrc":.15},
    "alt_demand":{"growth":.30,"flpop_growth":.20,"sales_per_store_q":.20,"net_open":.10,"log_wrc":.20},
    "alt_profit":{"growth":.30,"flpop_growth":.10,"sales_per_store_q":.35,"net_open":.10,"log_wrc":.15},
    "equal":{"growth":.20,"flpop_growth":.20,"sales_per_store_q":.20,"net_open":.20,"log_wrc":.20}}
for k,W in WS.items(): sc["score_"+k]=sum(z(sc,c)*w for c,w in W.items()); sc["rank_"+k]=sc["score_"+k].rank(ascending=False).astype(int)
sc["avg_rank"]=sc[["rank_"+k for k in WS]].mean(1)
# 3단계 강건성 (사전 선언): 가중치 4종 평균 순위 최소, 동률이면 유동인구 증가(수요 뒷받침)가 큰 쪽
sc=sc.sort_values(["avg_rank","flpop_growth"],ascending=[True,False]); top=sc.head(5)
pick=top.index[0]
# 매출 성장 분해: 매출 = 점포수 × 점포당 매출
pk=g.loc[pick]; dec={"store_growth":float(pk.store_growth),"sps_growth":float((full.loc[pick,REC].mean()/SP.loc[pick,REC].mean())/(full.loc[pick,PRI].mean()/SP.loc[pick,PRI].mean())-1),"flpop_growth":float(pk.flpop_growth)}
gu=s.merge(ar[["TRDAR_CD","SIGNGU_CD_NM"]],on="TRDAR_CD").pivot_table(index="SIGNGU_CD_NM",columns="STDR_YYQU_CD",values="THSMON_SELNG_AMT",aggfunc="sum")
gu["growth"]=gu[REC].sum(1)/gu[PRI].sum(1)-1; gu=gu.sort_values("growth",ascending=False)
qoq=full.pct_change(axis=1)  # 시장 전체 분기 변화 중앙값 (레벨 점프가 시장 공통인지)
qa["market_qoq_median"]={q:round(float(qoq[q].median()),4) for q in Q[::-1][1:]}
qa["seoul_total_by_q"]={q:float(full[q].sum()) for q in Q[::-1]}
sc.to_csv(A/"scored_trdar.csv",encoding="utf-8-sig"); gu.to_csv(A/"signgu_growth.csv",encoding="utf-8-sig")
row=lambda i,x:{"code":i,"name":x.TRDAR_CD_NM,"gu":x.SIGNGU_CD_NM,"dong":x.ADSTRD_CD_NM,"growth":float(x.growth),"sustain":int(x.sustain),"stores":int(x.stores),
   "sales_recent4q":float(x.sales_recent4q),"sales_per_store_q":float(x.sales_per_store_q),"net_open":float(x.net_open),"flpop":float(x.flpop),"flpop_growth":float(x.flpop_growth),
   "wrcpop":float(x.wrcpop),"ix":x.ix,"ranks":{k:int(x["rank_"+k]) for k in WS},"quarterly":[float(v) for v in full.loc[i,Q[::-1]]],"stores_q":[float(v) for v in SP.loc[i,Q[::-1]]],"flpop_q":[float(v) for v in FP.loc[i,Q[::-1]]]}
out={"quarters":Q,"qa":qa,"weights":WS,"top5":[row(i,x) for i,x in top.iterrows()],"pick":row(pick,sc.loc[pick]),"decomp":dec,
 "excluded_examples":[{"name":g.loc[i].TRDAR_CD_NM,"growth":float(g.loc[i].growth),"sustain":int(g.loc[i].sustain),"sps":float(g.loc[i].sales_per_store_q) if pd.notna(g.loc[i].sales_per_store_q) else None,"net_open":float(g.loc[i].net_open) if pd.notna(g.loc[i].net_open) else None} for i in u.sort_values("growth",ascending=False).head(15).index if i not in sc.index][:3],
 "gu_top5":[{"gu":k,"growth":float(v)} for k,v in gu.growth.head(5).items()],"gu_bottom3":[{"gu":k,"growth":float(v)} for k,v in gu.growth.tail(3).items()],
 "seoul_growth":float(full[REC].sum().sum()/full[PRI].sum().sum()-1),"pick_rank_all_weights":{k:int(sc.loc[pick,"rank_"+k]) for k in WS}}
json.dump(out,open(A/"result.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(json.dumps({k:out[k] for k in ["qa","decomp","pick_rank_all_weights","seoul_growth"]},ensure_ascii=False)[:1500])
for t in out["top5"]: print(t["name"],t["gu"],t["dong"],round(t["growth"],3),t["sustain"],t["stores"],round(t["sales_per_store_q"]/1e8,2),round(t["net_open"],2),round(t["flpop_growth"],3),t["ranks"])
print("excluded",out["excluded_examples"])
