import sys, json, csv, pathlib, datetime
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, r"C:\Users\user\.claude\skills\seoul-coffee-district\scripts")
import fetch_district as f
root=pathlib.Path(sys.argv[1]); key=f.load_key(root); called=datetime.date.today().isoformat()
Q=json.load(open(root/"data/manifest.json",encoding="utf-8"))["quarters"]
SETS=[("store_trdar","VwsmTrdarStorQq",True,"서울시 상권분석서비스(점포-상권) OA-15577"),("flpop_trdar","VwsmTrdarFlpopQq",False,"서울시 상권분석서비스(길단위인구-상권) OA-15568")]
jobs=[]
for name,svc,ind,src in SETS:
    for q in Q:
        t=(f.get(key,svc,1,1,q).get(svc) or {}).get("list_total_count",0)
        jobs+= [(name,svc,ind,src,q,s) for s in range(1,t+1,1000)]
def run(j):
    name,svc,ind,src,q,s=j; res=f.get(key,svc,s,s+999,q)
    (root/"raw"/f"{svc}_{q}_{s:07d}.json").write_text(json.dumps(res,ensure_ascii=False),encoding="utf-8")
    return name,src,[r for r in (res.get(svc) or {}).get("row",[]) if (not ind or r.get("SVC_INDUTY_CD")=="CS100010") and r.get("STDR_YYQU_CD")==q]
out={}
with ThreadPoolExecutor(24) as ex:
    for name,src,rows in ex.map(run,jobs): out.setdefault(name,(src,[]))[1].extend(rows)
man=json.load(open(root/"data/manifest.json",encoding="utf-8"))
for name,(src,rows) in out.items():
    with open(root/"data"/f"{name}.csv","w",newline="",encoding="utf-8-sig") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())+["_source","_called"]); w.writeheader()
        for r in rows: w.writerow({**r,"_source":src,"_called":called})
    for m in man["files"]:
        if m["file"]==f"data/{name}.csv": m["rows"]=len(rows)
    print(name,len(rows))
# 직장·상주인구는 분기 파라미터가 무시되므로 기준분기 컬럼으로 분기별 행 수 확인
json.dump(man,open(root/"data/manifest.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
