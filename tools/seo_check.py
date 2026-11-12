#!/usr/bin/env python3
"""SEOの自動チェック（外部ライブラリ不要）。pet.shiokonbu.com の seo_check.py をもとにしたもの。
使い方: python3 tools/seo_check.py .   → NG があれば終了コード1。PRごとに .github/workflows/seo-check.yml で動く。
"""
import json, os, re, sys, collections
from html.parser import HTMLParser

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://katachi.shiokonbu.com"
# 本文に出してはいけない言葉（AGENTS.md）。取り扱わない分野を売り込むような言葉を止める。
BAN = ["酒類OEM", "お酒のOEM", "医薬品OEM", "医療機器の製造を", "口コミ評価", "★5"]

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.title = ""; s.desc = None; s.canon = None; s.h1 = 0; s.robots = ""
        s._t = False; s._skip = 0; s._ld = False; s.ld = []; s.text = []
    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag == "title": s._t = True
        elif tag == "script" and a.get("type") == "application/ld+json": s._ld = True; s.ld.append("")
        elif tag in ("script", "style"): s._skip += 1
        elif tag == "meta" and a.get("name") == "description": s.desc = a.get("content", "")
        elif tag == "meta" and a.get("name") == "robots": s.robots = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical": s.canon = a.get("href")
        elif tag == "h1" and not s._skip: s.h1 += 1
    def handle_endtag(s, tag):
        if tag == "title": s._t = False
        elif tag == "script" and s._ld: s._ld = False
        elif tag in ("script", "style"): s._skip -= 1
    def handle_data(s, d):
        if s._t: s.title += d
        elif s._ld: s.ld[-1] += d
        elif not s._skip: s.text.append(d)

def main():
    locs = re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read())
    ng, warn, titles = [], [], collections.defaultdict(list)
    for u in locs:
        rel = u.replace(SITE, "").lstrip("/")
        f = os.path.join(ROOT, rel, "index.html") if (rel == "" or rel.endswith("/")) else os.path.join(ROOT, rel)
        if not os.path.exists(f):
            ng.append(f"{u}: sitemap にあるのにファイルがない"); continue
        p = P(); p.feed(open(f, encoding="utf-8").read())
        t = p.title.strip(); titles[t].append(u)
        if not t: ng.append(f"{u}: title がない")
        elif len(t) > 45: warn.append(f"{u}: title が長い（{len(t)}字。32字前後が目安）")
        if not p.desc: ng.append(f"{u}: description がない")
        elif not 50 <= len(p.desc) <= 160: warn.append(f"{u}: description の長さ {len(p.desc)}字（80〜120字が目安）")
        if p.canon != u: ng.append(f"{u}: canonical が {p.canon}")
        if "noindex" in p.robots: ng.append(f"{u}: noindex なのに sitemap にある")
        if p.h1 != 1: ng.append(f"{u}: h1 が {p.h1} 個")
        for j in p.ld:
            try: json.loads(j)
            except ValueError as e: ng.append(f"{u}: 構造化データが壊れている（{e}）")
        if not p.ld: warn.append(f"{u}: 構造化データがない")
        body = "".join(p.text)
        for w in BAN:
            if w in body: ng.append(f"{u}: 使わない言葉「{w}」")
    for t, us in titles.items():
        if t and len(us) > 1: ng.append(f"title が重複「{t}」: {', '.join(us)}")
    for w in warn: print("注意:", w)
    for n in ng: print("NG:", n)
    print(f"{len(locs)}ページを確認。NG {len(ng)}件・注意 {len(warn)}件")
    sys.exit(1 if ng else 0)

main()
