#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check.py — kalite kapıları (KICKOFF §12.2)

  python build/check.py            → dist/index.html üzerinde denetimler + testler
  python build/check.py --hizli    → testleri atla

Denetimler:
  1. dist tek dosya; dış URL / ağ isteği sıfır (http(s):// yalnızca metin içinde, src/href'te değil)
  2. tüm id'ler benzersiz; tüm #iç bağlantılar çözülüyor; TOC eksiksiz
  3. SVG'lerde sabit renk yok, her SVG'de <title>
  4. G-xx / W-xx envanteri KICKOFF §6/§7 ile eşleşiyor (eksik / fazla raporu)
  5. bölüm şablonu: her bölümde meta şeridi, ≥1 tuzak, özet kartı, kendini sına, ≥3 şekil
  6. dsp-core testleri (node varsa) + Python bilinen-cevap testleri
  7. JS sözdizimi (node --check)
"""
import re
import subprocess
import sys
import shutil
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "index.html"
CONTENT = ROOT / "content"

# KICKOFF §6 görsel envanteri (dosya adı öneki) — bölüm: [G-xx...]
G_BEKLENEN = {
    0: ["g-00", "g-01", "g-02"], 1: ["g-10", "g-11"], 2: ["g-20", "g-21", "g-22"], 3: ["g-30", "g-31", "g-32"],
    4: ["g-40", "g-41"], 5: ["g-50", "g-51", "g-52"], 6: ["g-60", "g-61", "g-62"],
    7: ["g-70", "g-71", "g-72", "g-73", "g-74", "g-75", "g-76", "g-77", "g-78", "g-79", "g-7a", "g-7b"],
    8: ["g-80", "g-81"], 9: ["g-90", "g-91", "g-92", "g-93"], 10: ["g-100", "g-101", "g-102", "g-103"],
    11: ["g-110", "g-111", "g-112"], 12: ["g-120", "g-121", "g-122"], 13: ["g-130", "g-131"],
    14: ["g-140", "g-141"], 15: ["g-150", "g-151"], 16: ["g-160", "g-161", "g-162", "g-163"],
    17: ["g-170", "g-171", "g-172"], 18: ["g-180", "g-181", "g-182"], 19: ["g-190", "g-191"],
    20: ["g-200", "g-201", "g-202"], 21: ["g-210", "g-211", "g-212"], 22: ["g-220", "g-221", "g-222"],
    23: ["g-230", "g-231", "g-232", "g-233"], 24: ["g-240", "g-241"], 25: ["g-250", "g-251", "g-252"],
    26: ["g-260", "g-261", "g-262"], 27: ["g-270"], 28: ["g-280"], 29: ["g-290"], 30: ["g-300", "g-301"],
}
W_BEKLENEN = {1: ["w01"], 2: ["w02"], 3: ["w03"], 4: ["w04"], 6: ["w05"], 7: ["w06"], 8: ["w07"], 9: ["w08", "w09"],
              12: ["w10"], 14: ["w11"], 15: ["w12"], 16: ["w13"], 18: ["w14"], 19: ["w15"], 20: ["w16"],
              21: ["w17"], 23: ["w18"], 25: ["w19"], 28: ["w20"]}

hatalar, uyarilar = [], []


def hata(m): hatalar.append(m)
def uyar(m): uyarilar.append(m)


def main():
    hizli = "--hizli" in sys.argv
    if not DIST.exists():
        print("dist/index.html yok — önce build."); return 1
    h = DIST.read_text(encoding="utf-8")

    # 1) dış istek
    for m in re.finditer(r'(?:src|href)="(https?://[^"]+)"', h):
        if "rf-sampling" in m.group(1):
            continue
        hata(f"dış URL: {m.group(1)[:80]}")
    if re.search(r"@import|url\(\s*['\"]?https?:", h):
        hata("CSS içinde dış kaynak")
    if "<link" in h and 'rel="stylesheet"' in h:
        hata("<link rel=stylesheet> var")

    # 2) id benzersizliği + iç bağlantılar
    idler = re.findall(r'\bid="([^"]+)"', h)
    tekrar = {i for i in idler if idler.count(i) > 1}
    for t in sorted(tekrar):
        hata(f"tekrarlı id: {t}")
    idset = set(idler)
    for m in re.finditer(r'href="#([^"]+)"', h):
        if m.group(1) not in idset:
            hata(f"kırık iç bağlantı: #{m.group(1)}")
    # TOC: her bölüm section'ı TOC'ta var mı
    bolum_idler = re.findall(r'<section class="bolum" id="([^"]+)"', h)
    toc = re.search(r'<nav class="toc"[^>]*>(.*?)</nav>', h, re.S).group(1)
    for b in bolum_idler:
        if f'href="#{b}"' not in toc:
            hata(f"TOC'ta yok: {b}")

    # 3) SVG sabit renk / title (widget/kit dışı, statik figürler)
    for m in re.finditer(r"<figure[^>]*>(.*?)</figure>", h, re.S):
        fig = m.group(1)
        idm = re.search(r'<svg[^>]*aria-labelledby="([^"]+)"', fig)
        if "<title" not in fig:
            hata("figürde <title> yok: " + (re.search(r'id="([^"]+)"', m.group(0)) or ["?", "?"])[1])
        temiz = re.sub(r'(href|xlink:href)="#[^"]*"', "", fig)
        temiz = re.sub(r'id="[^"]*"', "", temiz)
        c = re.search(r"#([0-9A-Fa-f]{3,8})\b", temiz)
        if c:
            hata(f"figürde sabit renk #{c.group(1)}: " + (re.search(r'id="([^"]+)"', m.group(0)) or ["?", "?"])[1])

    # 4) G/W envanteri
    figur_idler = set(re.findall(r'<figure class="sema[^"]*" id="([^"]+)"', h)) | set(re.findall(r'<div class="mk-sema" id="([^"]+)"', h))
    widget_idler = set(re.findall(r'data-widget="([^"]+)"', h))
    eksik_g, eksik_w = [], []
    for b, gl in G_BEKLENEN.items():
        for g in gl:
            if not any(f == g or f.startswith(g + "-") for f in figur_idler):
                eksik_g.append(g)
    for b, wl in W_BEKLENEN.items():
        for w in wl:
            if w not in widget_idler:
                eksik_w.append(w)
    fazla_g = sorted(f for f in figur_idler if not any(f == g or f.startswith(g + "-") for gl in G_BEKLENEN.values() for g in gl))

    # 5) bölüm şablonu
    for m in re.finditer(r'<section class="bolum" id="(bolum-\d+)">(.*?)</section>', h, re.S):
        bid, sec = m.group(1), m.group(2)
        no = int(bid.split("-")[1])
        sekil = len(re.findall(r'<figure class="sema', sec)) + len(re.findall(r'class="mk-sema"', sec))
        eksikler = []
        if 'class="bolum-meta"' not in sec: eksikler.append("meta")
        if 'class="kutu tuzak"' not in sec: eksikler.append("tuzak")
        if 'class="ozet-karti"' not in sec: eksikler.append("özet")
        if 'class="kendini-sina"' not in sec: eksikler.append("kendini-sına")
        if 'class="kutu neden-onemli"' not in sec and no != 0: eksikler.append("neden-önemli")
        if sekil < 3 and no not in (27,): eksikler.append(f"şekil {sekil}<3")
        if 'class="pasaport"' not in sec and no in (5, 6, 8, 9, 11, 14, 15, 16, 22, 23, 26): eksikler.append("pasaport")
        if eksikler:
            uyar(f"{bid}: şablon eksik → " + ", ".join(eksikler))

    # 6) testler
    node = shutil.which("node")
    if not hizli:
        if node:
            r = subprocess.run([node, "--test", str(ROOT / "tests" / "dsp-core.test.js")], capture_output=True, text=True, encoding="utf-8", errors="replace")
            ozet = re.search(r"pass (\d+)\s+.*?fail (\d+)", r.stdout, re.S)
            if r.returncode != 0:
                hata("dsp-core testleri başarısız:\n" + "\n".join(l for l in r.stdout.splitlines() if l.startswith("✖") or "AssertionError" in l)[:2000])
            else:
                print(f"  ✓ dsp-core testleri: {ozet.group(1) if ozet else '?'} geçti")
        else:
            uyar("node yok — dsp-core testleri atlandı")
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-p", "test_*.py", "-q"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            hata("Python bilinen-cevap testleri başarısız:\n" + r.stderr[-2000:])
        else:
            print("  ✓ Python bilinen-cevap testleri geçti")
        # 7) JS sözdizimi
        if node:
            js = re.search(r"<script>\n(/\* ---- dsp-core\.js.*?)</script>\s*</body>", h, re.S)
            if js:
                tmp = ROOT / "dist" / "_bundle_check.js"
                tmp.write_text(js.group(1), encoding="utf-8")
                r = subprocess.run([node, "--check", str(tmp)], capture_output=True, text=True, encoding="utf-8", errors="replace")
                tmp.unlink(missing_ok=True)
                if r.returncode != 0:
                    hata("JS sözdizimi: " + r.stderr[:800])
                else:
                    print("  ✓ JS paketi sözdizimi geçti")

    boyut = DIST.stat().st_size / (1024 * 1024)
    print(f"  dist boyutu: {boyut:.2f} MB" + ("  (hedef < 8 MB aşıldı!)" if boyut > 8 else ""))
    print(f"  şekil: {len(figur_idler)}  widget: {len(widget_idler)}  bölüm: {len(bolum_idler)}")
    if eksik_g: print(f"  eksik G: {len(eksik_g)} → {', '.join(eksik_g)}")
    if eksik_w: print(f"  eksik W: {len(eksik_w)} → {', '.join(eksik_w)}")
    if fazla_g: print(f"  envanter dışı şekil (KICKOFF'a ek): {', '.join(fazla_g)}")
    if uyarilar:
        print("UYARILAR (%d):" % len(uyarilar))
        for u in uyarilar: print("  •", u)
    if hatalar:
        print("HATALAR (%d):" % len(hatalar))
        for e in hatalar: print("  ✗", e)
        return 1
    print("CHECK: hata yok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
