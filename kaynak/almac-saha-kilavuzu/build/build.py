#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — almac-saha-kilavuzu derleyicisi

content/*.md dosyalarını sırayla okur, seri markdown alt kümesi + bu kılavuza
özgü direktifleri HTML'e çevirir; CSS / JS / SVG / senaryo verisini inline
ederek tamamen self-contained dist/index.html üretir.

Yalnızca Python stdlib. Kullanım:  python build/build.py

Markdown çekirdeği (seri ile ortak):
  # Bölüm N — Ad | # Ek A — Ad     → bölüm başlığı (h2)
  ## / ###                          → h3 (TOC'a girer) / h4
  paragraflar, **kalın**, *eğik*, `kod`, [metin](href)
  - / 1. listeler, | tablo |, > alıntı, ``` kod ```
  :::saha-notu|tuzak|analoji|derin-dalis|ozet|kopru|neden-onemli  …  :::
  {{svg:dosya.svg|altyazı}}  (opsiyonel üçüncü alan: kaydir)

Bu kılavuza özgü:
  ::meta onkosul=12,2 acar=15,20 blok=nco rota=yazilimci,sayisal
  ::kisim V — Sayısal Almaç Zinciri (DDC)
  :::pasaport durak="ADC çıkışı" alan=sayisal     → Etiket: değer satırları ("!" öneki = değişti)
  :::uc-goz                                        → ::rf:: ::fpga:: ::yazilim:: panelleri
  :::formul id=snr-q baslik="…"                    → f: / s: / o: satırları
  :::matlab-fpga baslik="…"                        → ::matlab:: ::fpga::
  :::kendini-sina                                  → S: soru / C: cevap çiftleri
  :::mimari no=1 ad="…" sema=g-70-cvr.svg          → ::ilke:: ::arti:: ::eksi:: ::kullanim:: ::ozellik::
  :::widget id=w11 ad="NCO laboratuvarı"           → gövde: "Ne gözlemlemeliyim?" listesi
  {{tablo: genis belirti-neden}}                   → sonraki tabloya sınıf
  {{s:ddc.nco_mhz}}                                → scenario.json değeri
  {{bolum:14}} / {{bolum:14|metin}}                → bölüm bağlantısı
  {{rf:anchor|metin}}                              → ../rf-sampling/index.html#anchor
  {{ek:a|metin}}                                   → ek bağlantısı
"""

import html
import json
import re
import sys
import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
SVG_DIR = ROOT / "assets" / "svg"
JS_DIR = ROOT / "assets" / "js"
CSS_FILE = ROOT / "assets" / "css" / "kilavuz.css"
DATA = ROOT / "data"
OUT = ROOT / "dist" / "index.html"

BASLIK = "Antenden PDW'ye — Saha Kılavuzu"
ANA_BASLIK = "Antenden PDW'ye"
ALT_BASLIK = "Radar ve Elektronik Harp Sayısal Almaç Sistemleri Saha Kılavuzu"
ACIKLAMA = ("Bir darbenin antenden PDW'ye yolculuğu: RF ön uç, ADC, DDC, FFT, CFAR ve "
            "PDW üretimi — FPGA'lı almaç kartının PS tarafında çalışan gömülü yazılımcı için.")
KAPAK_NOT = ("Tüm sayısal örnekler kurgusal bir referans senaryodan türetilmiştir; gerçek bir "
             "sistemi, platformu veya tehdidi temsil etmez. Yalnızca açık literatür kullanılmıştır.")
RF_YOL = "../rf-sampling/index.html"

KUTU_VARSAYILAN = {
    "saha-notu": "Saha notu",
    "tuzak": "Tuzak",
    "analoji": "Analoji",
    "neden-onemli": "Neden önemli",
    "kopru": "Köprü",
}

# Zincirdeki yerim — poster şemanın mini hali (durak id, etiket, bölüm no, alan)
ZINCIR = [
    ("anten",   "Anten",      5,  "analog"),
    ("onuc",    "LNA / BPF",  5,  "analog"),
    ("mixer",   "Mixer+LO",   6,  "analog"),
    ("if",      "IF / AAF",   6,  "analog"),
    ("adc",     "ADC",        9,  "adc"),
    ("arayuz",  "JESD/SSR",   11, "sayisal"),
    ("nco",     "NCO",        14, "sayisal"),
    ("mixing",  "⊗ I/Q",      15, "sayisal"),
    ("filtre",  "FIR ↓M",     16, "sayisal"),
    ("zarf",    "Zarf",       22, "sayisal"),
    ("esik",    "CFAR",       23, "sayisal"),
    ("fft",     "FFT",        18, "sayisal"),
    ("olcum",   "Ölçüm",      25, "sayisal"),
    ("pdw",     "PDW FIFO",   26, "sayisal"),
    ("ps",      "PS / SW",    30, "yazilim"),
]

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")


def slugify(text: str) -> str:
    s = text.translate(TR_MAP).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "bolum"


def attr_parse(s: str) -> dict:
    """ad=deger ad="değer boşluklu" çiftleri."""
    out = {}
    for m in re.finditer(r'([a-z-]+)=(?:"([^"]*)"|(\S+))', s):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return out


# ----------------------------------------------------------------- senaryo
SENARYO = json.loads((DATA / "scenario.json").read_text(encoding="utf-8"))


def senaryo_deger(yol: str) -> str:
    cur = SENARYO
    for p in yol.split("."):
        if isinstance(cur, list):
            cur = cur[int(p)]
        else:
            if p not in cur:
                raise KeyError(f"scenario.json'da yok: {yol}")
            cur = cur[p]
    if isinstance(cur, float):
        if cur.is_integer():
            return str(int(cur))
        return f"{cur:g}" if abs(cur) >= 1e-3 else repr(cur)
    if isinstance(cur, bool):
        return "evet" if cur else "hayır"
    return str(cur)


# ----------------------------------------------------------------- sözlük
SOZLUK = json.loads((DATA / "glossary.json").read_text(encoding="utf-8")) if (DATA / "glossary.json").exists() else []
SOZLUK_BY_KEY = {t["kisaltma"]: t for t in SOZLUK}
_TERIM_RE = None
if SOZLUK:
    _keys = sorted((t["kisaltma"] for t in SOZLUK), key=len, reverse=True)
    _TERIM_RE = re.compile(r"(?<![\w/])(" + "|".join(re.escape(k) for k in _keys) + r")(?![\w])")


# ----------------------------------------------------------------- formül mini-dili
def formul_html(src: str) -> str:
    """Basit formül işaretlemesini HTML'e çevirir.
    x^2 x^{ab}  x_j x_{ab}  frac{a}{b}  sqrt{a}  **kalın**  ·×−≤≥≈ olduğu gibi."""
    s = html.escape(src, quote=False)

    def grup(t, i):
        """t[i] == '{' varsayımıyla eşleşen '}' bul; (içerik, sonraki indeks)."""
        d = 0
        j = i
        while j < len(t):
            if t[j] == "{":
                d += 1
            elif t[j] == "}":
                d -= 1
                if d == 0:
                    return t[i + 1:j], j + 1
            j += 1
        return t[i + 1:], len(t)

    def cevir(t):
        out = []
        i = 0
        while i < len(t):
            c = t[i]
            if t.startswith("frac{", i):
                a, i = grup(t, i + 4)
                if i < len(t) and t[i] == "{":
                    b, i = grup(t, i)
                else:
                    b = ""
                out.append('<span class="kesir"><span>%s</span><span>%s</span></span>' % (cevir(a), cevir(b)))
                continue
            if t.startswith("sqrt{", i):
                a, i = grup(t, i + 4)
                out.append('<span class="kok-isaret">√</span><span class="kok">%s</span>' % cevir(a))
                continue
            if c in "^_":
                tag = "sup" if c == "^" else "sub"
                if i + 1 < len(t) and t[i + 1] == "{":
                    a, i = grup(t, i + 1)
                else:
                    m = re.match(r"[0-9]+|[−-]?[0-9A-Za-zα-ωΑ-Ω]", t[i + 1:])
                    a = m.group(0) if m else t[i + 1:i + 2]
                    i += 1 + len(a)
                out.append("<%s>%s</%s>" % (tag, cevir(a), tag))
                continue
            if t.startswith("**", i):
                j = t.find("**", i + 2)
                if j > 0:
                    out.append("<strong>%s</strong>" % cevir(t[i + 2:j]))
                    i = j + 2
                    continue
            out.append(c)
            i += 1
        return "".join(out)

    return cevir(s)


# --------------------------------------------------------------- inline parse
class Inline:
    """Satır içi markdown + senaryo/bağlantı makroları + sözlük terimi bağlama."""

    def __init__(self, derleyici):
        self.d = derleyici

    def makrolar(self, text: str) -> str:
        def s_(m):
            try:
                return senaryo_deger(m.group(1))
            except KeyError as e:
                self.d.uyar(str(e))
                return "??"
        text = re.sub(r"\{\{s:([a-zA-Z0-9_.]+)\}\}", s_, text)

        def bolum_(m):
            no = m.group(1)
            metin = m.group(2) or ("Bölüm %s" % no)
            return "[%s](#bolum-%s)" % (metin, no)
        text = re.sub(r"\{\{bolum:(\d+)(?:\|([^}]*))?\}\}", bolum_, text)

        def ek_(m):
            return "[%s](#ek-%s)" % (m.group(2) or ("Ek %s" % m.group(1).upper()), m.group(1).lower())
        text = re.sub(r"\{\{ek:([a-fA-F])(?:\|([^}]*))?\}\}", ek_, text)

        def rf_(m):
            return "[%s](%s#%s)" % (m.group(2) or "RF Örnekleme Saha Kılavuzu", RF_YOL, m.group(1))
        text = re.sub(r"\{\{rf:([a-z0-9-]*)(?:\|([^}]*))?\}\}", rf_, text)

        def f_(m):
            return '\x01F%s\x01' % m.group(1)
        text = re.sub(r"\$([^$\n]+)\$", f_, text)
        return text

    def __call__(self, text: str, terim_bagla: bool = True) -> str:
        text = self.makrolar(text)
        out = []
        parts = re.split(r"(`[^`]+`|\x01F[^\x01]+\x01)", text)
        for p in parts:
            if p.startswith("`") and p.endswith("`") and len(p) > 2:
                out.append("<code>" + html.escape(p[1:-1]) + "</code>")
            elif p.startswith("\x01F"):
                out.append('<span class="f-inline">%s</span>' % formul_html(p[2:-1]))
            else:
                e = html.escape(p, quote=False)
                e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e)
                e = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", e)
                e = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', e)
                if terim_bagla and _TERIM_RE is not None and self.d.terim_aktif:
                    e = self.terimleri_bagla(e)
                out.append(e)
        return "".join(out)

    def terimleri_bagla(self, e: str) -> str:
        """Etiket dışı metinde, bölümde ilk geçen sözlük terimini bağlar."""
        segs = re.split(r"(<[^>]+>)", e)
        derin_a = 0
        for k, seg in enumerate(segs):
            if seg.startswith("<"):
                if re.match(r"<a[\s>]", seg):
                    derin_a += 1
                elif seg.startswith("</a"):
                    derin_a -= 1
                continue
            if derin_a > 0 or not seg:
                continue

            def rep(m):
                key = m.group(1)
                if key in self.d.terim_gorulen:
                    return key
                self.d.terim_gorulen.add(key)
                t = SOZLUK_BY_KEY[key]
                tanim = t.get("tanim", "")
                en = t.get("en", "")
                bal = (en + " — " if en else "") + tanim
                return '<a class="terim" href="#sozluk-%s" data-tanim="%s">%s</a>' % (
                    slugify(key), html.escape(bal, quote=True), key)
            segs[k] = _TERIM_RE.sub(rep, seg)
        return "".join(segs)


# ---------------------------------------------------------------- block parse
class Derleyici:
    def __init__(self):
        self.sekil_no = 0
        self.formul_no = 0
        self.headings = []          # (level, text, hid, bolum_no)
        self.kullanilan_id = set()
        self.inline = Inline(self)
        self.uyarilar = []
        self.eksik_svg = []
        self.terim_gorulen = set()
        self.terim_aktif = True
        self.bolum_no = None
        self.sayac = {}
        self.figur_idler = []
        self.widget_idler = []
        self.bekleyen_tablo_sinif = ""

    def uyar(self, m):
        self.uyarilar.append(m)

    def say(self, k, n=1):
        self.sayac[k] = self.sayac.get(k, 0) + n

    def uniq_id(self, base: str) -> str:
        hid, i = base, 2
        while hid in self.kullanilan_id:
            hid = f"{base}-{i}"
            i += 1
        self.kullanilan_id.add(hid)
        return hid

    # ---- listeler ----
    def parse_list(self, lines, i):
        def item_info(ln):
            m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
            if not m:
                return None
            return len(m.group(1)), m.group(2) not in ("-", "*"), m.group(3)

        first = item_info(lines[i])
        base_indent, ordered = first[0], first[1]
        tag = "ol" if ordered else "ul"
        items, cur = [], None
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
                cur.append(self.inline(lines[i].strip()))
                i += 1
            else:
                break
        if cur is not None:
            items.append(cur)
        li_html = []
        for it in items:
            head = self.inline(it[0])
            rest = "".join(x if x.startswith("<ul") or x.startswith("<ol") else " " + x for x in it[1:])
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
        sinif = self.bekleyen_tablo_sinif
        self.bekleyen_tablo_sinif = ""
        kap = ' class="tablo-kap%s"' % (" genis" if "genis" in sinif else "")
        tsin = " ".join(s for s in sinif.split() if s != "genis")
        out = [f'<div{kap}><table%s>' % ((' class="%s"' % tsin) if tsin else "")]
        if head:
            out.append("<thead><tr>" + "".join(f"<th>{self.inline(c)}</th>" for c in head) + "</tr></thead>")
        out.append("<tbody>")
        for r in body:
            out.append("<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in r) + "</tr>")
        out.append("</tbody></table></div>")
        self.say("tablo")
        return "".join(out), i

    # ---- svg figür ----
    def svg_oku(self, dosya: str):
        yol = SVG_DIR / dosya
        if not yol.exists():
            self.eksik_svg.append(dosya)
            return None
        svg = yol.read_text(encoding="utf-8").strip()
        svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
        if "<title" not in svg:
            self.uyar(f"{dosya}: <title> yok")
        for m in re.finditer(r"#([0-9A-Fa-f]{3,8})\b", re.sub(r"(href|xlink:href)=\"#[^\"]*\"", "", svg)):
            self.uyar(f"{dosya}: sabit renk #{m.group(1)}")
            break
        return svg

    def figur(self, dosya: str, caption: str, secenek: str = "") -> str:
        svg = self.svg_oku(dosya)
        fid = Path(dosya).stem
        if svg is None:
            svg = ('<svg viewBox="0 0 860 200" role="img"><title>eksik</title>'
                   '<text x="430" y="100" text-anchor="middle" class="s-metin2">Şema hazırlanıyor: %s</text></svg>' % html.escape(dosya))
        self.sekil_no += 1
        self.say("sema")
        self.figur_idler.append(fid)
        cap = self.inline(caption)
        kls = "sema" + (" kaydir" if "kaydir" in secenek else "")
        return (f'<figure class="{kls}" id="{fid}">{svg}'
                f'<figcaption><span class="sekil-no">Şekil {self.sekil_no}.</span> {cap}</figcaption></figure>')

    # ---- kutular ----
    def kutu(self, tur: str, baslik: str, ic_md: str) -> str:
        ic = self.blocks(ic_md)
        self.say(tur)
        if tur == "derin-dalis":
            b = html.escape(baslik) if baslik else "devamı"
            return (f'<details class="derin-dalis"><summary>{b}</summary>'
                    f'<div class="dd-icerik">{ic}</div></details>')
        if tur == "ozet":
            ic = re.sub(r"<ul>(.*?)</ul>", r"<ol>\1</ol>", ic, flags=re.S)
            return f'<div class="ozet-karti"><span class="kutu-baslik">Özet kartı</span>{ic}</div>'
        b = baslik or KUTU_VARSAYILAN.get(tur, tur)
        return f'<div class="kutu {tur}"><span class="kutu-baslik">{html.escape(b)}</span>{ic}</div>'

    # ---- bu kılavuza özgü direktifler ----
    def parcala(self, govde: str, anahtarlar):
        """'::ad::' ayraçlarıyla bölünmüş gövdeyi {ad: metin} sözlüğüne çevirir."""
        out = {}
        cur = None
        buf = []
        for ln in govde.split("\n"):
            m = re.match(r"^::([a-z-]+)::\s*$", ln.strip())
            if m and m.group(1) in anahtarlar:
                if cur:
                    out[cur] = "\n".join(buf)
                cur, buf = m.group(1), []
            else:
                buf.append(ln)
        if cur:
            out[cur] = "\n".join(buf)
        return out

    def pasaport(self, attrs, govde):
        durak = attrs.get("durak", "")
        alan = attrs.get("alan", "sayisal")
        items = []
        for ln in govde.split("\n"):
            ln = ln.strip()
            if not ln or ":" not in ln:
                continue
            k, v = ln.split(":", 1)
            degisti = k.startswith("!")
            k = k.lstrip("!").strip()
            v = self.inline(v.strip(), terim_bagla=False)
            if degisti:
                v = f'<span class="degisti">{v}</span>'
            items.append(f"<div><dt>{html.escape(k)}</dt><dd>{v}</dd></div>")
        self.say("pasaport")
        return (f'<div class="pasaport" data-alan="{html.escape(alan)}">'
                f'<div class="pasaport-bas"><span>Sinyal pasaportu</span><span class="durak">{self.inline(durak, False)}</span></div>'
                f'<dl>{"".join(items)}</dl></div>')

    def uc_goz(self, attrs, govde):
        p = self.parcala(govde, ("rf", "fpga", "yazilim"))
        adlar = [("rf", "RF gözüyle"), ("fpga", "FPGA gözüyle"), ("yazilim", "Yazılımcı gözüyle")]
        self.say("uc-goz")
        self.say("ucgoz_n")
        n = self.sayac["ucgoz_n"]
        sek, pan = [], []
        ilk = True
        for k, ad in adlar:
            if k not in p:
                continue
            sek.append(f'<button type="button" role="tab" data-goz="{k}" aria-selected="{"true" if ilk else "false"}" '
                       f'aria-controls="ucgoz-{n}-{k}" id="ucgoz-{n}-{k}-tab">{ad}</button>')
            pan.append(f'<div class="goz-panel" role="tabpanel" id="ucgoz-{n}-{k}" aria-labelledby="ucgoz-{n}-{k}-tab"{"" if ilk else " hidden"}>'
                       f'<h5>{ad}</h5>{self.blocks(p[k])}</div>')
            ilk = False
        return f'<div class="uc-goz"><div class="sekmeler" role="tablist">{"".join(sek)}</div>{"".join(pan)}</div>'

    def formul(self, attrs, govde):
        self.formul_no += 1
        self.say("formul")
        fid = attrs.get("id", f"formul-{self.formul_no}")
        baslik = attrs.get("baslik", "")
        formuller, semboller, ornek = [], [], []
        for ln in govde.split("\n"):
            s = ln.strip()
            if s.startswith("f:"):
                formuller.append(f'<span class="f">{formul_html(s[2:].strip())}</span>')
            elif s.startswith("s:"):
                parcalar = [x.strip() for x in s[2:].split("|")]
                while len(parcalar) < 3:
                    parcalar.append("")
                semboller.append(f'<dt>{formul_html(parcalar[0])}</dt><dd>{self.inline(parcalar[1], False)}</dd>'
                                 f'<dd class="birim">{html.escape(parcalar[2])}</dd>')
            elif s.startswith("o:"):
                ornek.append(f"<p>{self.inline(s[2:].strip(), False)}</p>")
        sem = f'<dl class="fk-semboller">{"".join(semboller)}</dl>' if semboller else ""
        orn = (f'<div class="fk-ornek"><span class="fk-ornek-bas">Referans senaryoda</span>{"".join(ornek)}</div>'
               if ornek else "")
        return (f'<div class="formul-karti" id="f-{html.escape(fid)}"><div class="fk-bas">'
                f'<span>{html.escape(baslik)}</span><span class="fk-no">F.{self.formul_no}</span></div>'
                f'{"".join(formuller)}{sem}{orn}</div>')

    def matlab_fpga(self, attrs, govde):
        p = self.parcala(govde, ("matlab", "fpga"))
        self.say("matlab-fpga")
        return ('<div class="matlab-fpga">'
                f'<div class="mf-matlab"><p class="mf-bas">MATLAB — kayan nokta</p>{self.blocks(p.get("matlab", ""))}</div>'
                f'<div class="mf-fpga"><p class="mf-bas">FPGA — sabit nokta</p>{self.blocks(p.get("fpga", ""))}</div></div>')

    def kendini_sina(self, attrs, govde):
        sorular = []
        cur = None
        for ln in govde.split("\n"):
            s = ln.strip()
            if s.startswith("S:"):
                cur = [s[2:].strip(), []]
                sorular.append(cur)
            elif s.startswith("C:") and cur:
                cur[1].append(s[2:].strip())
            elif s and cur and cur[1]:
                cur[1][-1] += " " + s
            elif s and cur:
                cur[0] += " " + s
        self.say("kendini-sina")
        self.say("soru", len(sorular))
        parts = []
        for soru, cevaplar in sorular:
            parts.append(f'<details><summary>{self.inline(soru, False)}</summary>'
                         f'<div class="cevap">{"".join("<p>%s</p>" % self.inline(c, False) for c in cevaplar)}</div></details>')
        return f'<div class="kendini-sina"><span class="kutu-baslik">Kendini sına</span>{"".join(parts)}</div>'

    def mimari(self, attrs, govde):
        p = self.parcala(govde, ("ilke", "arti", "eksi", "kullanim", "ozellik"))
        self.say("mimari")
        sema = ""
        if "sema" in attrs:
            svg = self.svg_oku(attrs["sema"])
            if svg:
                self.figur_idler.append(Path(attrs["sema"]).stem)
                self.sekil_no += 1
                self.say("sema")
                sema = f'<div class="mk-sema" id="{Path(attrs["sema"]).stem}">{svg}</div>'
        oz = []
        for ln in p.get("ozellik", "").split("\n"):
            if ":" in ln:
                k, v = ln.split(":", 1)
                try:
                    yuzde = int(float(v.strip()) / 5 * 100)
                except ValueError:
                    continue
                oz.append(f'<div>{html.escape(k.strip())}<div class="cubuk"><i style="width:{yuzde}%"></i></div></div>')
        return ('<div class="mimari-karti">'
                f'<div class="mk-bas"><span class="mk-no">M-{html.escape(attrs.get("no", "?"))}</span>'
                f'<span class="mk-ad">{html.escape(attrs.get("ad", ""))}</span></div>'
                f'<div class="mk-govde">{sema}'
                f'<div class="mk-ilke"><h5>Çalışma ilkesi</h5>{self.blocks(p.get("ilke", ""))}</div>'
                f'<div class="mk-ozellik">{"".join(oz)}</div>'
                f'<div class="mk-arti"><h5>Artıları</h5>{self.blocks(p.get("arti", ""))}</div>'
                f'<div class="mk-eksi"><h5>Eksileri</h5>{self.blocks(p.get("eksi", ""))}</div>'
                f'<div class="mk-kullanim"><h5>Tipik kullanım</h5>{self.blocks(p.get("kullanim", ""))}</div>'
                '</div></div>')

    def widget(self, attrs, govde):
        wid = attrs.get("id", "")
        ad = attrs.get("ad", wid)
        self.say("widget")
        self.widget_idler.append(wid)
        gozlem = self.blocks(govde)
        gozlem = re.sub(r"<ul>(.*?)</ul>", r"<ol>\1</ol>", gozlem, flags=re.S)
        return (f'<div class="widget" id="{html.escape(wid)}" data-widget="{html.escape(wid)}">'
                f'<div class="w-bas"><span class="w-no">{html.escape(wid.upper())}</span>'
                f'<span class="w-ad">{html.escape(ad)}</span><span class="w-etiket">İnteraktif</span></div>'
                '<div class="w-govde"><div class="w-kontrol"></div><div class="w-cizim">'
                '<p class="w-jsyok">Bu widget JavaScript ile çalışır. Dosyayı JavaScript açık bir tarayıcıda açın; '
                'baskıda referans senaryo görüntüsü kullanılır.</p></div></div>'
                f'<div class="w-alt"><div class="w-sonuc"></div>'
                f'<div class="w-gozlem"><b>Ne gözlemlemeliyim?</b>{gozlem}</div></div></div>')

    def direktif(self, tur, attr_str, govde):
        attrs = attr_parse(attr_str)
        if tur in ("saha-notu", "tuzak", "analoji", "derin-dalis", "ozet", "kopru", "neden-onemli"):
            baslik = attrs.get("baslik") or (attr_str.strip() if "=" not in attr_str else "")
            return self.kutu(tur, baslik, govde)
        if tur == "pasaport":
            return self.pasaport(attrs, govde)
        if tur == "uc-goz":
            return self.uc_goz(attrs, govde)
        if tur == "formul":
            return self.formul(attrs, govde)
        if tur == "matlab-fpga":
            return self.matlab_fpga(attrs, govde)
        if tur == "kendini-sina":
            return self.kendini_sina(attrs, govde)
        if tur == "mimari":
            return self.mimari(attrs, govde)
        if tur == "widget":
            return self.widget(attrs, govde)
        self.uyar(f"bilinmeyen direktif: {tur}")
        return f"<!-- bilinmeyen direktif {html.escape(tur)} -->"

    # ---- ana blok döngüsü ----
    def blocks(self, md: str) -> str:
        lines = md.split("\n")
        out, i, para = [], 0, []

        def flush():
            if para:
                out.append("<p>" + self.inline(" ".join(para)) + "</p>")
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
                out.append(f'<div class="komut">{dil_html}<pre><code>' + html.escape("\n".join(kod)) + "</code></pre></div>")
                self.say("kod")
                continue

            # ::: direktif
            m = re.match(r"^:::([a-z-]+)\s*(.*)$", s)
            if m:
                flush()
                tur, attr_str = m.group(1), m.group(2).strip()
                i += 1
                ic, derinlik = [], 1
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
                out.append(self.direktif(tur, attr_str, "\n".join(ic)))
                continue

            # svg figürü
            m = re.match(r"^\{\{svg:([^|}]+)\|([^|}]*)(?:\|([^}]*))?\}\}$", s)
            if m:
                flush()
                out.append(self.figur(m.group(1).strip(), m.group(2).strip(), (m.group(3) or "").strip()))
                i += 1
                continue

            # tablo sınıfı
            m = re.match(r"^\{\{tablo:\s*([^}]*)\}\}$", s)
            if m:
                flush()
                self.bekleyen_tablo_sinif = m.group(1).strip()
                i += 1
                continue

            # başlıklar
            m = re.match(r"^(#{1,4})\s+(.*)$", s)
            if m:
                flush()
                seviye, metin = len(m.group(1)), m.group(2).strip()
                if seviye == 1:
                    self.uyar(f"bölüm içinde ikinci # başlık: {metin}")
                    i += 1
                    continue
                if seviye == 2:
                    hid = self.uniq_id(f"bolum-{self.bolum_no}--{slugify(metin)}")
                    self.headings.append((2, metin, hid, self.bolum_no))
                    out.append(f'<h3 id="{hid}"><a class="baglanti" href="#{hid}" aria-label="Bu başlığa bağlantı">#</a>{self.inline(metin, False)}</h3>')
                else:
                    out.append(f"<h4>{self.inline(metin, False)}</h4>")
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
                out.append("<blockquote><p>" + self.inline(" ".join(q)) + "</p></blockquote>")
                continue

            if re.fullmatch(r"-{3,}", s):
                flush(); out.append("<hr>"); i += 1; continue

            para.append(s); i += 1

        flush()
        return "\n".join(out)


# ------------------------------------------------------------------ bölüm meta
def zincir_svg(aktif: set, bolum_no) -> str:
    """Zincirdeki yerim mini şeması."""
    n = len(ZINCIR)
    w = 900
    bw, gap, x0, y0, h = 52, 8, 10, 14, 36
    parts = ['<svg viewBox="0 0 %d 66" role="img" aria-labelledby="zy-%s"><title id="zy-%s">Zincirdeki yerim: büyük resim şemasının mini hali, bu bölümün bloğu vurgulu</title>' % (w, bolum_no, bolum_no)]
    parts.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="yol-sayisal" opacity=".5"/>' % (x0, y0 + h / 2, x0 + n * (bw + gap), y0 + h / 2))
    for k, (sid, ad, bno, alan) in enumerate(ZINCIR):
        x = x0 + k * (bw + gap)
        kls = "blok-aktif" if sid in aktif else ("blok-analog" if alan == "analog" else ("blok-kontrol" if alan == "yazilim" else "blok"))
        parts.append('<a href="#bolum-%d"><rect x="%d" y="%d" width="%d" height="%d" rx="6" class="%s"/>'
                     '<text x="%.1f" y="%.1f" text-anchor="middle" class="s-kucuk"%s>%s</text></a>'
                     % (bno, x, y0, bw, h, kls, x + bw / 2, y0 + h / 2 + 4,
                        ' style="fill:var(--accent);font-weight:700"' if sid in aktif else "", html.escape(ad)))
    parts.append('<text x="%d" y="62" class="s-kucuk">RF dünyası</text><text x="%d" y="62" class="s-kucuk">veri dönüştürme</text>'
                 '<text x="%d" y="62" class="s-kucuk">sayısal dünya (FPGA)</text><text x="%d" y="62" class="s-kucuk" text-anchor="end">yazılım</text>'
                 % (x0, x0 + 4 * (bw + gap), x0 + 6 * (bw + gap), x0 + n * (bw + gap) - gap))
    parts.append("</svg>")
    return "".join(parts)


def meta_serit(meta: dict, kelime: int, bolum_no, bolumler_adi: dict) -> str:
    dk = max(2, round(kelime / 170))
    def baglar(key):
        v = meta.get(key, "")
        if not v:
            return "—"
        out = []
        for t in re.split(r"[,\s]+", v.strip()):
            if not t:
                continue
            if t.isdigit():
                out.append(f'<a href="#bolum-{t}" title="{html.escape(bolumler_adi.get(t, ""))}">B{t}</a>')
            elif t.startswith("rf:"):
                out.append(f'<a href="{RF_YOL}#{t[3:]}">RF Örnekleme</a>')
            else:
                out.append(html.escape(t))
        return " · ".join(out)
    rotalar = [r for r in re.split(r"[,\s]+", meta.get("rota", "")) if r]
    roz = "".join(f'<span class="rota-rozet {r}">{ {"yazilimci": "Yazılımcı rotası", "sayisal": "Sayısal tasarımcı rotası"}.get(r, r)}</span>' for r in rotalar)
    if not roz:
        roz = '<span class="rota-rozet">Tam yolculuk</span>'
    return (f'<div class="bolum-meta"><div><b>Okuma süresi</b>≈ {dk} dk · {kelime:,} kelime</div>'
            f'<div><b>Ön koşul</b>{baglar("onkosul")}</div><div><b>Açtığı bölümler</b>{baglar("acar")}</div>'
            f'<div><b>Rota</b>{roz}</div></div>'.replace(",", "."))


# ------------------------------------------------------------------ şablonlar
TEMA_JS = r"""
(function () {
  var t = null;
  try { t = localStorage.getItem('tema'); } catch (e) {}
  if (!t) t = (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', t);
})();
"""

TEMA_DUGME = """
<button id="tema-dugme" type="button" aria-label="Temayı değiştir">
<svg class="ikon-gunes" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><title>Açık tema</title><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
<svg class="ikon-ay" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><title>Koyu tema</title><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
</button>
"""

KAPAK_DALGA = """
<svg class="kapak-dalga" viewBox="0 0 760 64" preserveAspectRatio="none" aria-hidden="true">
<path class="yol-analog" d="M0 32 L120 32 C125 32 126 6 130 6 C134 6 135 58 139 58 C143 58 144 6 148 6 C152 6 153 58 157 58 C161 58 162 6 166 6 C170 6 171 58 175 58 C179 58 180 6 184 6 C188 6 189 58 193 58 C197 58 198 6 202 6 C206 6 207 32 212 32 L760 32" opacity=".9"/>
<path class="yol-sayisal" d="M420 56 L440 56 L440 20 L452 20 L452 44 L464 44 L464 12 L476 12 L476 50 L488 50 L488 26 L500 26 L500 40 L512 40 L512 16 L524 16 L524 48 L536 48 L536 56 L560 56" opacity=".9"/>
<path class="yol-kontrol" d="M600 44 h20 v-22 h14 v22 h10 v-10 h14 v10 h10 v-22 h14 v22 h10 v-10 h14 v10 h10 v-22 h14 v22 h16" opacity=".9"/>
<text x="0" y="12" class="s-kucuk">anten</text><text x="760" y="12" text-anchor="end" class="s-kucuk">PDW</text>
</svg>
"""


def toc_html(bolumler) -> str:
    out = ["<ul>"]
    for b in bolumler:
        if b["kisim"]:
            out.append(f'<li class="toc-kisim">{html.escape(b["kisim"])}</li>')
        rota = " ".join(b["rota"]) if b["rota"] else ""
        out.append(f'<li class="toc-bolum" data-rota="{html.escape(rota)}"><a href="#{b["id"]}">'
                   f'<span class="bolum-no-k">{html.escape(b["no_kisa"])}</span> {html.escape(b["ad"])}</a>')
        if b["altlar"]:
            out.append('<ul class="toc-alt">' + "".join(f'<li><a href="#{hid}">{html.escape(t)}</a></li>' for t, hid in b["altlar"]) + "</ul>")
        out.append("</li>")
    out.append("</ul>")
    return "".join(out)


def js_topla() -> str:
    parcalar = []
    for ad in ("dsp-core.js", "widget-kit.js"):
        p = JS_DIR / ad
        if p.exists():
            parcalar.append(f"/* ---- {ad} ---- */\n" + p.read_text(encoding="utf-8"))
    for p in sorted((JS_DIR / "widgets").glob("w*.js")):
        parcalar.append(f"/* ---- widgets/{p.name} ---- */\n" + p.read_text(encoding="utf-8"))
    p = JS_DIR / "site.js"
    if p.exists():
        parcalar.append("/* ---- site.js ---- */\n" + p.read_text(encoding="utf-8"))
    return "\n".join(parcalar)


def main():
    dosyalar = sorted(CONTENT.glob("*.md"))
    if not dosyalar:
        sys.exit("content/ boş — derlenecek bölüm yok")

    d = Derleyici()
    bolumler = []
    # ön tarama: bölüm adları (meta bağlantılarının title'ı için)
    adlar = {}
    for f in dosyalar:
        ilk = f.read_text(encoding="utf-8").split("\n", 1)[0]
        m = re.match(r"#\s+(Bölüm\s+(\d+)|Ek\s+([A-F]))\s*—\s*(.*)", ilk)
        if m:
            adlar[m.group(2) or m.group(3).lower()] = m.group(4).strip()

    toplam_kelime = 0
    istatistik = []
    for f in dosyalar:
        md = f.read_text(encoding="utf-8")
        satirlar = md.split("\n")
        ilk = satirlar[0].strip()
        m = re.match(r"#\s+(Bölüm\s+(\d+)|Ek\s+([A-F]))\s*—\s*(.*)", ilk)
        if not m:
            sys.exit(f"{f.name}: ilk satır '# Bölüm N — Ad' ya da '# Ek A — Ad' olmalı")
        if m.group(2):
            no_metin, no_kisa, bid, bolum_no = f"Bölüm {m.group(2)}", m.group(2), f"bolum-{m.group(2)}", m.group(2)
        else:
            harf = m.group(3)
            no_metin, no_kisa, bid, bolum_no = f"Ek {harf}", harf, f"ek-{harf.lower()}", f"ek-{harf.lower()}"
        ad = m.group(4).strip()
        govde = satirlar[1:]

        meta, kisim = {}, None
        while govde and govde[0].strip().startswith("::"):
            s = govde.pop(0).strip()
            if s.startswith("::meta"):
                meta = attr_parse(s[6:])
            elif s.startswith("::kisim"):
                kisim = s[7:].strip()

        d.bolum_no = bolum_no
        d.terim_gorulen = set()
        d.terim_aktif = not f.name.startswith(("3", "4")) or "ek-" not in bid  # eklerde de bağlanır; sözlük eki hariç
        d.terim_aktif = bid != "ek-a"
        d.sayac = {}
        d.kullanilan_id.add(bid)
        govde_md = "\n".join(govde)
        kelime = len(re.findall(r"\w+", govde_md))
        toplam_kelime += kelime
        ic = d.blocks(govde_md)

        aktif = set(x for x in re.split(r"[,\s]+", meta.get("blok", "")) if x)
        ust = ""
        if m.group(2):  # yalnızca bölümlerde meta şeridi + zincir
            ust = meta_serit(meta, kelime, bolum_no, adlar)
            ust += f'<figure class="zincir">{zincir_svg(aktif, bolum_no)}<figcaption>Zincirdeki yerim — vurgulu blok bu bölümün konusu; bloğa tıklayınca ilgili bölüme gider.</figcaption></figure>'

        baslik_html = f'<span class="bolum-no">{html.escape(no_metin)}</span>{d.inline(ad, False)}'
        sec = (f'<section class="bolum" id="{bid}"><h2 id="{bid}-baslik"><a class="baglanti" href="#{bid}" aria-label="Bu bölüme bağlantı">#</a>{baslik_html}</h2>\n{ust}\n{ic}\n</section>')
        if kisim:
            kno, _, kad = kisim.partition("—")
            sec = f'<div class="kisim-ayrac"><div class="kisim-no">Kısım {html.escape(kno.strip())}</div><div class="kisim-ad">{html.escape(kad.strip())}</div></div>\n' + sec

        altlar = [(t, hid) for (lvl, t, hid, bno) in d.headings if bno == bolum_no]
        bolumler.append({"id": bid, "no_kisa": no_kisa, "ad": ad, "html": sec, "altlar": altlar,
                         "kisim": kisim, "rota": [r for r in re.split(r"[,\s]+", meta.get("rota", "")) if r]})
        istatistik.append((f.stem, kelime, dict(d.sayac)))

    css = CSS_FILE.read_text(encoding="utf-8")
    toc = toc_html(bolumler)
    nav = (f'<p class="toc-baslik">{html.escape(ANA_BASLIK)}</p><p class="toc-seri">Saha Kılavuzu Serisi</p>'
           '<div class="rota-filtre" role="group" aria-label="Okuma rotası">'
           '<button type="button" data-rota="" aria-pressed="true">Tam yolculuk</button>'
           '<button type="button" data-rota="yazilimci" aria-pressed="false">Yazılımcı</button>'
           '<button type="button" data-rota="sayisal" aria-pressed="false">Sayısal tasarımcı</button></div>'
           f'<nav class="toc" aria-label="İçindekiler" data-rota="">{toc}</nav>')

    semboller = ""
    sym = SVG_DIR / "symbols.svg"
    if sym.exists():
        semboller = re.sub(r"<\?xml[^>]*\?>\s*", "", sym.read_text(encoding="utf-8").strip())

    senaryo_js = "window.SENARYO = " + json.dumps(SENARYO, ensure_ascii=False, separators=(",", ":")) + ";"
    js = js_topla()
    simdi = datetime.date.today().isoformat()

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
{semboller}
<div id="progress" role="presentation"></div>
{TEMA_DUGME}
<div class="yerlesim">
<aside class="toc-kolon"><div class="toc-ic">{nav}</div></aside>
<main>
<header class="kapak">
<p class="seri">Saha Kılavuzu Serisi · SK-05</p>
<h1>{html.escape(ANA_BASLIK)}</h1>
<p class="alt">{html.escape(ALT_BASLIK)}</p>
<p class="kapak-not">{html.escape(KAPAK_NOT)} Derleme: {simdi}.</p>
{KAPAK_DALGA}
</header>
<details class="toc-mobil"><summary>İçindekiler</summary>{nav}</details>
<div class="icerik">
{chr(10).join(b["html"] for b in bolumler)}
</div>
<footer class="dipnot">
<p>Saha Kılavuzu Serisi — Antenden PDW'ye. Tek dosya, bağımlılıksız; USB ile taşınabilir, internetsiz açılır.
Sayısal örnekler kurgusaldır; yalnızca açık literatür kullanılmıştır.</p>
</footer>
</main>
</div>
<script>{senaryo_js}</script>
<script>
{js}
</script>
</body>
</html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(sayfa, encoding="utf-8")
    kb = OUT.stat().st_size / 1024

    print("=" * 72)
    print(f"BUILD TAMAM: dist/index.html  {kb:,.0f} KB — {len(dosyalar)} bölüm, {d.sekil_no} şekil, "
          f"{len(d.widget_idler)} widget, {d.formul_no} formül, {toplam_kelime:,} kelime")
    print("-" * 72)
    print("%-26s %6s %4s %3s %3s %3s %3s %3s %3s %3s" % ("bölüm", "kelime", "şema", "wid", "frm", "tzk", "ozt", "ks", "ucg", "psp"))
    for ad, kel, s in istatistik:
        print("%-26s %6d %4d %3d %3d %3d %3d %3d %3d %3d" % (
            ad[:26], kel, s.get("sema", 0), s.get("widget", 0), s.get("formul", 0), s.get("tuzak", 0),
            s.get("ozet", 0), s.get("kendini-sina", 0), s.get("uc-goz", 0), s.get("pasaport", 0)))
    if d.eksik_svg:
        print("-" * 72)
        print("EKSİK SVG (%d): %s" % (len(d.eksik_svg), ", ".join(d.eksik_svg)))
    if d.uyarilar:
        print("-" * 72)
        print("UYARILAR (%d):" % len(d.uyarilar))
        for u in d.uyarilar[:40]:
            print("  •", u)
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
