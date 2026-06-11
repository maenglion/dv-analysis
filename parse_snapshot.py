"""
데이터바우처 공급기업 수행영역 파싱 — 스냅샷 재현 스크립트
============================================================
입력 : html_snapshot_backup.zip
       (K-DATA 데이터바우처 포털 검색 목록 원문 145페이지, 2026. 6. 11. 동결)
       기대 SHA-256:
       f625bcd520c55fc61984c35de8c45cecaadc9de53e8fde4ced9e26ec8d580489
출력 : datavoucher_723_full.csv (기업 723행 × 수행영역 8열)
       기대 SHA-256:
       2654f81b065d55a7ad170fb9dde17d3dd18b6919593608c6d3cb4e4ca4bc2fd8

방법 : 각 기업 카드(div.gr_item_box)의 공식 수행영역 배지
       (span.icon_file, span.icon_finance)를 파싱한다.
       기업 소개문의 단어 언급이 아닌 포털 게재 공식 배지 기준.
       실게재는 121페이지(120×6건+3건=723건)에서 종료되며
       122–145페이지는 공백(포털 페이지 수 산정 오류).

실행 : pip install beautifulsoup4 pandas
       python parse_snapshot.py
"""

import hashlib
import io
import sys
import zipfile

import pandas as pd
from bs4 import BeautifulSoup

ZIP_PATH = "html_snapshot_backup.zip"
ZIP_SHA256 = "f625bcd520c55fc61984c35de8c45cecaadc9de53e8fde4ced9e26ec8d580489"
OUT_CSV = "datavoucher_723_full.csv"
KW = ["가공", "전처리", "품질", "코딩", "시각화",
      "정보추출또는조합", "태깅또는라벨링", "분석"]


def main():
    # 1. 입력 무결성 검증 — 해시가 다르면 동결본이 아니므로 중단
    raw = open(ZIP_PATH, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != ZIP_SHA256:
        sys.exit(f"[중단] 스냅샷 해시 불일치\n  기대: {ZIP_SHA256}\n  실제: {digest}")
    print(f"[확인] 스냅샷 무결성 검증 통과 (SHA-256 일치)")

    # 2. 스냅샷에서 카드 단위 파싱
    rows = []
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = sorted(n for n in zf.namelist() if n.endswith(".html"))
        for fname in names:
            soup = BeautifulSoup(zf.read(fname).decode("utf-8"), "html.parser")
            for card in soup.select("div.gr_item_box"):
                a = card.find("a")
                if a is None:
                    continue
                name = a.get_text(strip=True)
                badges = {s.get_text(strip=True)
                          for s in card.select("span.icon_file, span.icon_finance")}
                rows.append([name] + ["O" if k in badges else "X" for k in KW])

    df = pd.DataFrame(rows, columns=["기업명"] + KW)
    df["k"] = df[KW].apply(lambda r: sum(v == "O" for v in r), axis=1)

    # 3. 산출 및 검산 출력
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    n = len(df)
    full = int((df["k"] == 8).sum())
    out_hash = hashlib.sha256(open(OUT_CSV, "rb").read()).hexdigest()
    print(f"[산출] 기업 {n}행 (고유 {df['기업명'].nunique()}곳)")
    print(f"[검산] 8개 영역 전부 표기: {full}곳 ({full/n:.1%})")
    print(f"[검산] 조건부 일치 확률: {(full-1)/(n-1):.1%}")
    print(f"[산출] {OUT_CSV} SHA-256: {out_hash}")
    print(f"[대조] 기대 해시와 {'일치 — 재현 성공' if out_hash == '2654f81b065d55a7ad170fb9dde17d3dd18b6919593608c6d3cb4e4ca4bc2fd8' else '불일치'}")


if __name__ == "__main__":
    main()
