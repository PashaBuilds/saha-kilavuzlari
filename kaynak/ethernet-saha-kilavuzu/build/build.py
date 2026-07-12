#!/usr/bin/env python3
"""
build.py — content/*.md dosyalarını tek self-contained dist/index.html'e derler.

Python 3 stdlib dışında bağımlılık yok. Desteklenen markdown alt kümesi:

  # Başlık            → bölüm başlığı (h2), "Bölüm N — Ad" biçimi ayrıştırılır
  ## Alt başlık       → h3 (TOC'a girer)
  ### Alt alt başlık  → h4
  paragraflar, **kalın**, *eğik*, `kod`, [metin](url)
  - / 1. listeler (iki boşluk girintiyle bir seviye iç içe)
  | tablo | satırları |
  > alıntı
  ```dil ... ```      → kopyala butonlu komut kutusu
  :::saha-notu Başlık ... :::   (tuzak / analoji / ozet / derin-dalis aynı)
  {{svg:dosya.svg|Şekil açıklaması}}  → inline SVG + otomatik numaralı figcaption
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SVG_DIR = ROOT / "assets" / "svg"
CSS_FILE = ROOT / "assets" / "css" / "kilavuz.css"
OUT = ROOT / "dist" / "index.html"

BASLIK = "Ethernet ve Ağ İletişimi — Saha Kılavuzu"
ACIKLAMA = ("Katmanlardan Wireshark'a, ARP'tan TCP'ye, gömülü Ethernet'ten arıza "
            "teşhisine: gömülü yazılımcı için uçtan uca ağ saha kılavuzu.")

KUTU_VARSAYILAN = {
    "saha-notu": "Saha notu",
    "tuzak": "Tuzak",
    "analoji": "Analoji",
    "ozet": "Bölüm özeti",
}

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")


def slugify(text: str) -> str:
    s = text.translate(TR_MAP).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "bolum"


# --------------------------------------------------------------- inline parse
def inline(text: str) -> str:
    """HTML'i kaçır, sonra sınırlı inline markdown uygula."""
    out = []
    # önce kod aralıklarını ayır ki içleri işlenmesin
    parts = re.split(r"(`[^`]+`)", text)
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 2:
            out.append("<code>" + html.escape(p[1:-1]) + "</code>")
        else:
            e = html.escape(p, quote=False)
            e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e)
            e = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", e)
            e = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', e)
            out.append(e)
    return "".join(out)


# ---------------------------------------------------------------- block parse
class Derleyici:
    def __init__(self):
        self.sekil_no = 0
        self.headings = []           # (level, text, hid)  — TOC için
        self.kullanilan_id = set()

    def uniq_id(self, base: str) -> str:
        hid, i = base, 2
        while hid in self.kullanilan_id:
            hid = f"{base}-{i}"
            i += 1
        self.kullanilan_id.add(hid)
        return hid

    # ---- listeler ----
    def parse_list(self, lines, i):
        """i konumunda liste başlıyor; (html, yeni_i) döner."""
        def item_info(ln):
            m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
            if not m:
                return None
            indent = len(m.group(1))
            ordered = m.group(2) not in ("-", "*")
            return indent, ordered, m.group(3)

        first = item_info(lines[i])
        base_indent, ordered = first[0], first[1]
        tag = "ol" if ordered else "ul"
        items = []
        cur = None
        while i < len(lines):
            info = item_info(lines[i])
            if info and info[0] == base_indent:
                if cur is not None:
                    items.append(cur)
                cur = [info[2]]
                i += 1
            elif info and info[0] > base_indent:
                sub, i = self.parse_list(lines, i)
                cur.append(sub)
            elif lines[i].strip() and not info and lines[i].startswith(" " * (base_indent + 2)):
                cur.append(inline(lines[i].strip()))
                i += 1
            else:
                break
        if cur is not None:
            items.append(cur)
        li_html = []
        for it in items:
            head = inline(it[0])
            rest = "".join(x if x.startswith("<ul") or x.startswith("<ol")
                           else " " + x for x in it[1:])
            li_html.append(f"<li>{head}{rest}</li>")
        return f"<{tag}>" + "".join(li_html) + f"</{tag}>", i

    # ---- tablo ----
    def parse_table(self, lines, i):
        rows = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows.append(cells)
            i += 1
        if len(rows) >= 2 and all(re.fullmatch(r":?-{2,}:?", c) for c in rows[1]):
            head, body = rows[0], rows[2:]
        else:
            head, body = None, rows
        out = ['<div class="tablo-kap"><table>']
        if head:
            out.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead>")
        out.append("<tbody>")
        for r in body:
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
        out.append("</tbody></table></div>")
        return "".join(out), i

    # ---- svg figür ----
    def figur(self, dosya: str, caption: str) -> str:
        yol = SVG_DIR / dosya
        if not yol.exists():
            sys.exit(f"HATA: SVG bulunamadı: {yol}")
        svg = yol.read_text(encoding="utf-8").strip()
        if "<title" not in svg:
            sys.exit(f"HATA: {dosya} içinde <title> yok (erişilebilirlik kuralı).")
        for m in re.finditer(r"#([0-9A-Fa-f]{3,8})\b", svg):
            sys.exit(f"HATA: {dosya} içinde sabit renk (#{m.group(1)}) var — CSS değişkeni kullan.")
        self.sekil_no += 1
        cap = inline(caption)
        return (f'<figure class="sema" id="sekil-{self.sekil_no}">{svg}'
                f'<figcaption><span class="sekil-no">Şekil {self.sekil_no}.</span> '
                f"{cap}</figcaption></figure>")

    # ---- kutular ----
    def kutu(self, tur: str, baslik: str, ic_md: str) -> str:
        ic = self.blocks(ic_md)
        if tur == "derin-dalis":
            b = html.escape(baslik) if baslik else "devamı"
            return (f'<details class="derin-dalis"><summary>{b}</summary>'
                    f'<div class="dd-icerik">{ic}</div></details>')
        b = baslik or KUTU_VARSAYILAN.get(tur, tur)
        return (f'<div class="kutu {tur}"><span class="kutu-baslik">{html.escape(b)}</span>'
                f"{ic}</div>")

    # ---- ana blok döngüsü ----
    def blocks(self, md: str, chapter=False) -> str:
        lines = md.split("\n")
        out, i, para = [], 0, []

        def flush():
            if para:
                out.append("<p>" + inline(" ".join(para)) + "</p>")
                para.clear()

        while i < len(lines):
            ln = lines[i]
            s = ln.strip()

            if not s:
                flush(); i += 1; continue

            # kod bloğu
            if s.startswith("```"):
                flush()
                dil = s[3:].strip()
                i += 1
                kod = []
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    kod.append(lines[i]); i += 1
                i += 1
                dil_html = f'<span class="dil">{html.escape(dil)}</span>' if dil else ""
                out.append(f'<div class="komut">{dil_html}<pre><code>'
                           + html.escape("\n".join(kod)) + "</code></pre></div>")
                continue

            # kutu / container
            m = re.match(r"^:::([a-z-]+)\s*(.*)$", s)
            if m and m.group(1) in ("saha-notu", "tuzak", "analoji", "ozet", "derin-dalis"):
                flush()
                tur, baslik = m.group(1), m.group(2).strip()
                i += 1
                ic = []
                derinlik = 1
                while i < len(lines):
                    t = lines[i].strip()
                    if re.match(r"^:::[a-z-]+", t):
                        derinlik += 1
                    elif t == ":::":
                        derinlik -= 1
                        if derinlik == 0:
                            break
                    ic.append(lines[i]); i += 1
                i += 1
                out.append(self.kutu(tur, baslik, "\n".join(ic)))
                continue

            # svg figürü
            m = re.match(r"^\{\{svg:([^|}]+)\|([^}]*)\}\}$", s)
            if m:
                flush()
                out.append(self.figur(m.group(1).strip(), m.group(2).strip()))
                i += 1
                continue

            # başlıklar
            m = re.match(r"^(#{1,4})\s+(.*)$", s)
            if m:
                flush()
                seviye, metin = len(m.group(1)), m.group(2).strip()
                if seviye == 1:
                    # bölüm başlığı: "Bölüm 5 — Ad" / "Ek A — Ad" / düz
                    hid = self.uniq_id(slugify(metin))
                    self.headings.append((1, metin, hid))
                    parcala = re.split(r"\s+—\s+", metin, maxsplit=1)
                    if len(parcala) == 2:
                        ic = (f'<span class="bolum-no">{inline(parcala[0])}</span>'
                              f"{inline(parcala[1])}")
                    else:
                        ic = inline(metin)
                    out.append(f'<h2 id="{hid}"><a class="baglanti" href="#{hid}" '
                               f'aria-label="Bu bölüme bağlantı">#</a>{ic}</h2>')
                elif seviye == 2:
                    hid = self.uniq_id(slugify(metin))
                    self.headings.append((2, metin, hid))
                    out.append(f'<h3 id="{hid}"><a class="baglanti" href="#{hid}" '
                               f'aria-label="Bu başlığa bağlantı">#</a>{inline(metin)}</h3>')
                else:
                    out.append(f"<h4>{inline(metin)}</h4>")
                i += 1
                continue

            # tablo
            if s.startswith("|"):
                flush()
                t, i = self.parse_table(lines, i)
                out.append(t)
                continue

            # liste
            if re.match(r"^(\s*)([-*]|\d+\.)\s+", ln):
                flush()
                l, i = self.parse_list(lines, i)
                out.append(l)
                continue

            # alıntı
            if s.startswith(">"):
                flush()
                q = []
                while i < len(lines) and lines[i].strip().startswith(">"):
                    q.append(lines[i].strip()[1:].strip()); i += 1
                out.append("<blockquote><p>" + inline(" ".join(q)) + "</p></blockquote>")
                continue

            # yatay çizgi
            if re.fullmatch(r"-{3,}", s):
                flush(); out.append("<hr>"); i += 1; continue

            para.append(s); i += 1

        flush()
        return "\n".join(out)


# ------------------------------------------------------------------ şablonlar
JS = r"""
(function () {
  // tema
  var kok = document.documentElement;
  document.getElementById('tema-dugme').addEventListener('click', function () {
    var t = kok.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    kok.setAttribute('data-theme', t);
    try { localStorage.setItem('tema', t); } catch (e) {}
  });

  // okuma ilerleme çubuğu
  var bar = document.getElementById('progress');
  function ilerleme() {
    var h = document.documentElement;
    var oran = h.scrollTop / (h.scrollHeight - h.clientHeight);
    bar.style.width = (oran * 100) + '%';
  }
  addEventListener('scroll', ilerleme, { passive: true });
  ilerleme();

  // kod kopyala butonları
  document.querySelectorAll('.komut').forEach(function (kutu) {
    var b = document.createElement('button');
    b.className = 'kopyala'; b.type = 'button'; b.textContent = 'Kopyala';
    b.addEventListener('click', function () {
      var metin = kutu.querySelector('code').innerText;
      (navigator.clipboard ? navigator.clipboard.writeText(metin)
                           : Promise.reject()).then(function () {
        b.textContent = 'Kopyalandı'; b.classList.add('ok');
        setTimeout(function () { b.textContent = 'Kopyala'; b.classList.remove('ok'); }, 1600);
      }).catch(function () { b.textContent = 'Olmadı'; });
    });
    kutu.appendChild(b);
  });

  // başlık anchor'ı: tıklayınca tam URL panoya
  document.querySelectorAll('a.baglanti').forEach(function (a) {
    a.addEventListener('click', function () {
      var url = location.origin + location.pathname + a.getAttribute('href');
      if (navigator.clipboard) navigator.clipboard.writeText(url);
    });
  });

  // TOC aktif bölüm vurgusu
  var basliklar = Array.prototype.slice.call(document.querySelectorAll('h2[id], h3[id]'));
  var linkler = {};
  document.querySelectorAll('nav.toc a[href^="#"]').forEach(function (a) {
    var id = a.getAttribute('href').slice(1);
    (linkler[id] = linkler[id] || []).push(a);
  });
  var aktifBolum = null, aktifAlt = null;
  function vurgula(id) {
    var h = document.getElementById(id);
    if (!h) return;
    var bolumId = id, altId = null;
    if (h.tagName === 'H3') {
      altId = id;
      var el = h;
      while (el && el.tagName !== 'H2') el = el.previousElementSibling;
      if (!el) { // bölüm section'ının başındaki h2
        var sec = h.closest('section');
        el = sec && sec.querySelector('h2[id]');
      }
      bolumId = el ? el.id : id;
    }
    if (bolumId === aktifBolum && altId === aktifAlt) return;
    aktifBolum = bolumId; aktifAlt = altId;
    document.querySelectorAll('nav.toc a.aktif').forEach(function (a) { a.classList.remove('aktif'); });
    document.querySelectorAll('nav.toc li.acik').forEach(function (li) { li.classList.remove('acik'); });
    (linkler[bolumId] || []).forEach(function (a) {
      a.classList.add('aktif');
      var li = a.closest('li.toc-bolum');
      if (li) li.classList.add('acik');
    });
    if (altId) (linkler[altId] || []).forEach(function (a) {
      a.classList.add('aktif');
      var li = a.closest('li.toc-bolum') || a.parentElement.closest('li.toc-bolum');
      if (li) li.classList.add('acik');
    });
    // TOC'ta görünür tut
    var ilk = (linkler[altId || bolumId] || [])[0];
    if (ilk && ilk.scrollIntoView && innerWidth > 960)
      ilk.scrollIntoView({ block: 'nearest' });
  }
  // scroll konumuna göre aktif başlık: viewport'un üst %35'inin üstündeki son başlık
  var sonToc = 0;
  function tocGuncelle() {
    var esik = innerHeight * 0.35;
    var aday = null;
    for (var i = 0; i < basliklar.length; i++) {
      var r = basliklar[i].getBoundingClientRect();
      if (r.top <= esik) aday = basliklar[i].id;
      else break;
    }
    if (!aday && basliklar.length) aday = basliklar[0].id;
    if (aday) vurgula(aday);
  }
  addEventListener('scroll', function () {
    var t = Date.now();
    if (t - sonToc > 80) { sonToc = t; tocGuncelle(); }
    else { clearTimeout(tocGuncelle._z); tocGuncelle._z = setTimeout(tocGuncelle, 100); }
  }, { passive: true });
  addEventListener('resize', tocGuncelle);
  tocGuncelle();
})();
"""

TEMA_JS = r"""
(function () {
  var t = null;
  try { t = localStorage.getItem('tema'); } catch (e) {}
  if (!t) t = (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches)
              ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', t);
})();
"""

TEMA_DUGME = """
<button id="tema-dugme" type="button" aria-label="Temayı değiştir">
<svg class="ikon-gunes" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><title>Açık tema</title><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
<svg class="ikon-ay" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><title>Koyu tema</title><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
</button>
"""


def toc_html(headings) -> str:
    out = ["<ul>"]
    acik_alt = False
    for lvl, metin, hid in headings:
        if lvl == 1:
            if acik_alt:
                out.append("</ul></li>")
                acik_alt = False
            else:
                if len(out) > 1:
                    out.append("</li>")
            out.append(f'<li class="toc-bolum"><a href="#{hid}">{html.escape(metin)}</a>')
            acik_alt = False
        else:
            if not acik_alt:
                out.append('<ul class="toc-alt">')
                acik_alt = True
            out.append(f'<li><a href="#{hid}">{html.escape(metin)}</a></li>')
    if acik_alt:
        out.append("</ul></li>")
    elif len(out) > 1:
        out.append("</li>")
    out.append("</ul>")
    return "".join(out)


def main():
    if not CONTENT.exists():
        sys.exit("content/ yok")
    dosyalar = sorted(CONTENT.glob("*.md"))
    if not dosyalar:
        sys.exit("content/ boş — derlenecek bölüm yok")

    d = Derleyici()
    bolumler = []
    for f in dosyalar:
        md = f.read_text(encoding="utf-8")
        ic = d.blocks(md, chapter=True)
        # section id'si bölümün ilk h2 id'si + '-b' (çakışmasın diye ayrı tutulur)
        m = re.search(r'<h2 id="([^"]+)"', ic)
        sid = f'sec-{m.group(1)}' if m else f"sec-{slugify(f.stem)}"
        bolumler.append(f'<section class="bolum" id="{sid}">{ic}</section>')

    css = CSS_FILE.read_text(encoding="utf-8")
    toc = toc_html(d.headings)

    nav = (f'<p class="toc-baslik">{html.escape(BASLIK.split(" — ")[0])}</p>'
           f'<p class="toc-seri">Saha Kılavuzu Serisi</p>'
           f'<nav class="toc" aria-label="İçindekiler">{toc}</nav>')

    sayfa = f"""<!DOCTYPE html>
<html lang="tr" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(BASLIK)}</title>
<meta name="description" content="{html.escape(ACIKLAMA)}">
<script>{TEMA_JS}</script>
<style>
{css}
</style>
</head>
<body>
<div id="progress" role="presentation"></div>
{TEMA_DUGME}
<div class="yerlesim">
<aside class="toc-kolon"><div class="toc-ic">{nav}</div></aside>
<main>
<header class="kapak">
<p class="seri">Saha Kılavuzu Serisi</p>
<h1>{html.escape(BASLIK.split(" — ")[0])}</h1>
<p class="alt">{html.escape(ACIKLAMA)}</p>
</header>
<details class="toc-mobil"><summary>İçindekiler</summary>{nav}</details>
<div class="icerik">
{chr(10).join(bolumler)}
</div>
<footer class="dipnot">
<p>Saha Kılavuzu Serisi — Ethernet ve Ağ İletişimi. Tek dosya, bağımlılıksız;
USB ile taşınabilir, internetsiz açılır.</p>
</footer>
</main>
</div>
<script>{JS}</script>
</body>
</html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(sayfa, encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"OK  dist/index.html  {kb:,.0f} KB — {len(dosyalar)} bölüm, "
          f"{d.sekil_no} şema, {len(d.headings)} başlık")
    if kb > 2048:
        print("UYARI: çıktı 2 MB üstünde")


if __name__ == "__main__":
    main()
