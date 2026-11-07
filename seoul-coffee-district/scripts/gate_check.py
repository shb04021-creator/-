#!/usr/bin/env python3
"""블랙의 퍼플 평가 전 게이트. report.html에 키 노출, 출처 없는 차트, 필수 섹션 누락이 있으면 FAIL(종료코드 1).
사용: python gate_check.py <프로젝트폴더>"""
import os, re, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8")
root = pathlib.Path(sys.argv[1]); html_p = root / "output" / "report.html"
fails = []
if not html_p.exists(): sys.exit("FAIL: output/report.html 없음")
html = html_p.read_text(encoding="utf-8")
key = os.environ.get("SEOUL_API_KEY", "")
env = root / ".env"
if not key and env.exists():
    key = next((l.split("=", 1)[1].strip() for l in env.read_text(encoding="utf-8").splitlines() if l.startswith("SEOUL_API_KEY=")), "")
for p in root.rglob("*"):
    if p.is_file() and p.suffix in {".md", ".html", ".json", ".csv", ".log"} and "raw" not in p.parts and key and key in p.read_text(encoding="utf-8", errors="ignore"):
        fails.append(f"API 키 노출: {p.relative_to(root)}")
if "데이터 한계" not in html: fails.append("'데이터 한계 및 보정 방법' 섹션 없음")
charts = len(re.findall(r'<(svg|canvas)\b', html)); caps = len(re.findall(r'class="[^"]*source-caption', html))
if caps < charts: fails.append(f"차트 {charts}개 중 출처 캡션(class=source-caption) {caps}개")
if '<meta name="viewport"' not in html: fails.append("반응형 viewport 메타 없음")
for f in ["data_quality.md", "hypotheses.md", "risks.md", "solutions.md", "final_solution.md", "design_spec.md"]:
    if not (root / f).exists(): fails.append(f"산출물 누락: {f}")
print("PASS" if not fails else "FAIL\n- " + "\n- ".join(fails)); sys.exit(1 if fails else 0)
