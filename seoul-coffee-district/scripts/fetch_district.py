#!/usr/bin/env python3
"""레드 전용 수집 스크립트. 서울 상권분석서비스 원본을 raw/에 그대로 저장하고 커피-음료(CS100010)만 data/*.csv로 뽑는다.

사용: python fetch_district.py <프로젝트폴더> [--quarters 8]
키: 환경변수 SEOUL_API_KEY 또는 <프로젝트폴더>/.env 의 SEOUL_API_KEY=... (값은 어디에도 출력하지 않는다)
"""
import csv, json, os, sys, time, urllib.request, urllib.parse, datetime, pathlib
sys.stdout.reconfigure(encoding="utf-8")

INDUSTRY = "CS100010"  # 커피-음료
# (파일명, 서비스명, 데이터셋명, 업종필터 여부, 단위 메모)
DATASETS = [
    ("sales_trdar", "VwsmTrdarSelngQq", "서울시 상권분석서비스(추정매출-상권) OA-15572", True, "원/분기 (카드결제 기반 추정)"),
    ("sales_adstrd", "VwsmAdstrdSelngW", "서울시 상권분석서비스(추정매출-행정동) OA-22175", True, "원/분기 (카드결제 기반 추정)"),
    ("sales_signgu", "VwsmSignguSelngW", "서울시 상권분석서비스(추정매출-자치구) OA-22176", True, "원/분기 (카드결제 기반 추정)"),
    ("store_trdar", "VwsmTrdarStorQq", "서울시 상권분석서비스(점포-상권) OA-15577", True, "개 (점포수·개업률·폐업률 %)"),
    ("store_adstrd", "VwsmAdstrdStorW", "서울시 상권분석서비스(점포-행정동) OA-22172", True, "개"),
    ("flpop_trdar", "VwsmTrdarFlpopQq", "서울시 상권분석서비스(길단위인구-상권) OA-15568", False, "명 (분기 합계, 일평균 환산 시 일수로 나눔)"),
    ("repop_trdar", "VwsmTrdarRepopQq", "서울시 상권분석서비스(상주인구-상권) OA-15584", False, "명"),
    ("wrcpop_trdar", "VwsmTrdarWrcPopltnQq", "서울시 상권분석서비스(직장인구-상권) OA-15569", False, "명"),
    ("ix_trdar", "VwsmTrdarIxQq", "서울시 상권분석서비스(상권변화지표-상권) OA-15576", False, "지표(LL/LH/HL/HH)"),
    ("fclty_trdar", "VwsmTrdarFcltyQq", "서울시 상권분석서비스(집객시설-상권) OA-15580", False, "개"),
    ("cnsmp_trdar", "VwsmTrdarNcmCnsmpQq", "서울시 상권분석서비스(소득소비-상권) OA-21278", False, "원"),
]
BASE = "http://openapi.seoul.go.kr:8088"

def load_key(root):
    k = os.environ.get("SEOUL_API_KEY", "").strip()
    env = pathlib.Path(root) / ".env"
    if not k and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("SEOUL_API_KEY="): k = line.split("=", 1)[1].strip()
    if not k: sys.exit("SEOUL_API_KEY가 없습니다. 환경변수나 <프로젝트>/.env 에 넣어 주세요.")
    return k

def get(key, svc, start, end, *args, tries=3):
    path = "/".join([key, "json", svc, str(start), str(end)] + [urllib.parse.quote(a) for a in args])
    for i in range(tries):
        try:
            with urllib.request.urlopen(f"{BASE}/{path}/", timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    return {"RESULT": {"CODE": "CLIENT-ERR", "MESSAGE": type(err).__name__}}  # 키가 들어간 URL은 남기지 않는다

def latest_quarters(key, n):
    y, q = datetime.date.today().year, (datetime.date.today().month - 1) // 3 + 1
    out = []
    while len(out) < n and y > 2018:
        cd = f"{y}{q}"
        res = get(key, "VwsmTrdarSelngQq", 1, 1, cd).get("VwsmTrdarSelngQq", {})
        if res.get("list_total_count"): out.append(cd)
        q -= 1
        if q == 0: y, q = y - 1, 4
    return out

def main():
    root = pathlib.Path(sys.argv[1]); n = int(sys.argv[sys.argv.index("--quarters") + 1]) if "--quarters" in sys.argv else 8
    key = load_key(root); called = datetime.date.today().isoformat()
    (root / "raw").mkdir(parents=True, exist_ok=True); (root / "data").mkdir(exist_ok=True)
    quarters = latest_quarters(key, n)
    print("분기:", quarters)
    manifest = []
    for fname, svc, dsname, by_ind, unit in DATASETS:
        rows, log = [], []
        for qc in quarters:
            start, total = 1, None
            while True:
                res = get(key, svc, start, start + 999, qc)
                (root / "raw" / f"{svc}_{qc}_{start:07d}.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
                body = res.get(svc)
                if not body: log.append(f"{qc}: {res.get('RESULT', {}).get('MESSAGE', '응답 없음')}"); break
                total = body.get("list_total_count", 0)
                rows += [r for r in body.get("row", []) if not by_ind or r.get("SVC_INDUTY_CD") == INDUSTRY]
                start += 1000
                if start > total: break
            if total: log.append(f"{qc}: 전체 {total}행")
        if rows:
            cols = list(rows[0].keys())
            with open(root / "data" / f"{fname}.csv", "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=cols + ["_source", "_called"]); w.writeheader()
                for r in rows: w.writerow({**r, "_source": dsname, "_called": called})
        manifest.append({"file": f"data/{fname}.csv", "service": svc, "dataset": dsname, "unit": unit,
                         "industry_filter": INDUSTRY if by_ind else None, "rows": len(rows), "quarters": quarters, "called": called, "log": log})
        print(f"{fname}: {len(rows)}행")
    (root / "data" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

if __name__ == "__main__":
    main()
