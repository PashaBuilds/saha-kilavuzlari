#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — content/*.md → tek self-contained dist/index.html

Akış:
  1. content/ altındaki NN-*.md dosyaları sırayla okunur (_ ile başlayanlar atlanır).
  2. Özel direktifler işlenir (kutular, görev kartları, SVG/kod gömme).
  3. python-markdown ile HTML'e çevrilir; başlıklara id + anchor eklenir.
  4. TOC, ilerleme panosu, kapak üretilir; CSS/JS inline gömülür.

Özel sözdizimi için CLAUDE.md'ye bak.
"""

import html
import json
import re
import sys
from pathlib import Path

import markdown

KOK = Path(__file__).resolve().parent.parent
ICERIK = KOK / "content"
LABS = KOK / "labs"
SVG = KOK / "assets" / "svg"
CSS = KOK / "assets" / "css" / "kilavuz.css"
JS = KOK / "assets" / "js" / "kilavuz.js"
CIKTI = KOK / "dist" / "index.html"

BASLIK = "Gömülü Sistemlere Giriş"
ALT_BASLIK = "Ekip Oryantasyon Yolculuğu"
SERI = "Saha Kılavuzu Serisi — Rehberli Yolculuk"

UYARILAR: list[str] = []


def uyar(mesaj: str) -> None:
    UYARILAR.append(mesaj)
    print(f"  UYARI: {mesaj}", file=sys.stderr)


# ---------------------------------------------------------------- yardımcılar

_TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜâÂ", "cgiosuCGIOSUaA")


def slugla(metin: str, kullanilan: set) -> str:
    s = metin.translate(_TR_MAP).lower()
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "bolum"
    aday, i = s, 2
    while aday in kullanilan:
        aday, i = f"{s}-{i}", i + 1
    kullanilan.add(aday)
    return aday


def oznitelik_ayikla(satir: str) -> dict:
    """`no=1 zorluk=2 baslik="LED Yak"` → dict"""
    sonuc = {}
    for m in re.finditer(r'([a-z_]+)=(?:"([^"]*)"|(\S+))', satir):
        sonuc[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return sonuc


# ---------------------------------------------------------------- C vurgulama

C_ANAHTAR = (
    "if|else|for|while|do|switch|case|default|break|continue|return|goto|"
    "sizeof|typedef|struct|union|enum|static|extern|const|volatile|register|"
    "inline|restrict|signed|unsigned|do|_Bool|true|false|NULL"
)
C_TIP = (
    "void|char|short|int|long|float|double|u?int(?:8|16|32|64)_t|size_t|"
    "ssize_t|bool|u8|u16|u32|u64|s8|s16|s32|s64|BaseType_t|TickType_t|"
    "TaskHandle_t|QueueHandle_t|SemaphoreHandle_t|XGpioPs|XScuGic|XTtcPs|"
    "XUartPs|XIicPs|XGpio|XGpioPs_Config|XScuGic_Config|XTtcPs_Config|"
    "XUartPs_Config|XIicPs_Config"
)

C_DESEN = re.compile(
    r"(?P<yorum>/\*.*?\*/|//[^\n]*)"
    r"|(?P<dizgi>\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*')"
    r"|(?P<onis>^[ \t]*#[^\n]*)"
    rf"|(?P<tip>\b(?:{C_TIP})\b)"
    rf"|(?P<anahtar>\b(?:{C_ANAHTAR})\b)"
    r"|(?P<sabit>\b(?:0[xX][0-9a-fA-F]+[uUlL]*|\d+[uUlL]*|\d*\.\d+[fF]?)\b)",
    re.MULTILINE | re.DOTALL,
)

_SINIF = {"yorum": "tok-yorum", "dizgi": "tok-dizgi", "onis": "tok-onisleyici",
          "tip": "tok-tip", "anahtar": "tok-anahtar", "sabit": "tok-sabit"}


def c_vurgula(kod: str) -> str:
    parcalar, son = [], 0
    for m in C_DESEN.finditer(kod):
        parcalar.append(html.escape(kod[son:m.start()]))
        parcalar.append(
            f'<span class="{_SINIF[m.lastgroup]}">{html.escape(m.group())}</span>')
        son = m.end()
    parcalar.append(html.escape(kod[son:]))
    return "".join(parcalar)


def kod_kutusu(kod: str, dil: str, etiket: str) -> str:
    kod = kod.rstrip("\n")
    if dil in ("c", "h", "cpp"):
        icerik = c_vurgula(kod)
    else:
        icerik = html.escape(kod)
    terminal = " komut" if dil in ("komut", "bash", "sh", "console", "tcl") else ""
    return (
        f'<div class="kod-kutu{terminal}">'
        f'<div class="kod-etiket"><span>{html.escape(etiket)}</span>'
        f'<button type="button" class="kopyala-dugme">kopyala</button></div>'
        f'<pre><code>{icerik}</code></pre></div>'
    )


# ---------------------------------------------------------------- markdown

MD_UZANTILAR = ["tables", "sane_lists"]

KUTU_ETIKETLERI = {
    "saha-notu": ("Saha Notu",
                  '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1l2 4.3 4.7.6-3.4 3.2.9 4.6L8 11.5l-4.2 2.2.9-4.6L1.3 5.9 6 5.3z"/></svg>'),
    "tuzak": ("Tuzak",
              '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1L1 14h14L8 1zm0 4.5l.4 5h-.8l.4-5zM8 12.8a.9.9 0 110-1.8.9.9 0 010 1.8z"/></svg>'),
    "analoji": ("Analoji",
                '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1a5 5 0 00-2.5 9.3V12h5v-1.7A5 5 0 008 1zM6 13h4v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-1z"/></svg>'),
    "ekip-notu": ("Ekip Notu",
                  '<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M6 2a2.5 2.5 0 100 5 2.5 2.5 0 000-5zm5 1a2 2 0 100 4 2 2 0 000-4zM1.5 13c0-2.2 2-4 4.5-4s4.5 1.8 4.5 4v1h-9v-1zm10.5 1v-1c0-1.1-.4-2.1-1-2.9.3-.1.7-.1 1-.1 1.9 0 3.5 1.4 3.5 3.1V14h-3.5z"/></svg>'),
}

GOREV_KAYITLARI: list[dict] = []  # build sırası = doküman sırası
_MEVCUT_BOLUM = [""]
_PH_SAYAC = [0]  # global placeholder sayacı — iç içe Isleyici'lerde çakışmayı önler


class Isleyici:
    """Bir markdown metnini (özyinelemeli) HTML'e çevirir."""

    def __init__(self):
        self.yerler: dict[str, str] = {}

    def _sakla(self, html_parca: str) -> str:
        # /: private-use — python-markdown STX/ETX'i (\x02/\x03) siler
        anahtar = f"GOMULU{_PH_SAYAC[0]}"
        _PH_SAYAC[0] += 1
        self.yerler[anahtar] = html_parca
        return anahtar

    # --- adım 1: çitli kod bloklarını ayır ---
    def _kodlari_ayir(self, metin: str) -> str:
        satirlar = metin.split("\n")
        sonuc, i = [], 0
        while i < len(satirlar):
            m = re.match(r"^```(\S*)\s*$", satirlar[i])
            if m:
                dil = m.group(1) or "metin"
                j = i + 1
                while j < len(satirlar) and not satirlar[j].startswith("```"):
                    j += 1
                kod = "\n".join(satirlar[i + 1:j])
                etiket = {"c": "C", "h": "C başlık", "komut": "terminal",
                          "bash": "terminal", "sh": "terminal",
                          "console": "terminal", "tcl": "XSCT",
                          "metin": "metin", "ld": "linker script",
                          "make": "Makefile"}.get(dil, dil)
                sonuc.append(self._sakla(kod_kutusu(kod, dil, etiket)))
                i = j + 1
            else:
                sonuc.append(satirlar[i])
                i += 1
        return "\n".join(sonuc)

    # --- adım 2: ::: kapsayıcı blokları ---
    def _bloklari_isle(self, metin: str) -> str:
        satirlar = metin.split("\n")
        sonuc, i = [], 0
        while i < len(satirlar):
            m = re.match(r"^:::([a-z-]+)(?:\s+(.*))?$", satirlar[i])
            if not m:
                sonuc.append(satirlar[i])
                i += 1
                continue
            ad, arg = m.group(1), (m.group(2) or "").strip()
            derinlik, j = 1, i + 1
            while j < len(satirlar):
                if re.match(r"^:::[a-z-]+", satirlar[j]):
                    derinlik += 1
                elif satirlar[j].rstrip() == ":::":
                    derinlik -= 1
                    if derinlik == 0:
                        break
                j += 1
            if derinlik != 0:
                uyar(f"kapanmamış :::{ad} bloğu")
                sonuc.append(satirlar[i])
                i += 1
                continue
            govde = "\n".join(satirlar[i + 1:j])
            sonuc.append(self._sakla(self._blok_uret(ad, arg, govde)))
            i = j + 1
        return "\n".join(sonuc)

    def _blok_uret(self, ad: str, arg: str, govde: str) -> str:
        if ad == "gorev":
            return self._gorev_karti(arg, govde)
        ic = Isleyici().cevir(govde)
        if ad == "derin-dalis":
            baslik = html.escape(arg or "Derin dalış")
            return (f'<details class="derin-dalis"><summary>Derin dalış — {baslik}'
                    f'</summary><div class="derin-icerik">{ic}</div></details>')
        if ad in KUTU_ETIKETLERI:
            etiket, ikon = KUTU_ETIKETLERI[ad]
            baslik = html.escape(arg) if arg else etiket
            return (f'<aside class="kutu {ad}"><div class="kutu-baslik">{ikon}'
                    f'<span>{baslik}</span></div>{ic}</aside>')
        uyar(f"bilinmeyen blok türü :::{ad}")
        return ic

    # --- görev kartı ---
    def _gorev_karti(self, arg: str, govde: str) -> str:
        oz = oznitelik_ayikla(arg)
        no = oz.get("no", "?")
        mezuniyet = no.lower() in ("mezuniyet", "m")
        gid = "gorev-mezuniyet" if mezuniyet else f"gorev-{int(no):02d}"
        baslik = oz.get("baslik", "Görev")
        zorluk = max(1, min(3, int(oz.get("zorluk", "1"))))
        kisa = oz.get("kisa", baslik.split("(")[0].strip())

        GOREV_KAYITLARI.append({
            "id": gid, "no": no, "baslik": baslik, "kisa": kisa,
            "zorluk": zorluk, "mezuniyet": mezuniyet,
            "bolum": _MEVCUT_BOLUM[0],
        })

        # bölümleri [Başlık] satırlarına göre ayır
        bolumler: list[tuple[str, list[str]]] = []
        for satir in govde.split("\n"):
            m = re.match(r"^\[([^\]]+)\]\s*$", satir)
            if m:
                bolumler.append((m.group(1).strip(), []))
            elif bolumler:
                bolumler[-1][1].append(satir)
            elif satir.strip():
                uyar(f"{gid}: bölüm etiketi öncesi metin yok sayıldı: {satir[:40]}")

        sinif_haritasi = {
            "hedef": "hedef", "ön koşul": "onkosul", "on kosul": "onkosul",
            "adımlar": "adimlar", "adimlar": "adimlar",
            "başarı kriteri": "basari", "basari kriteri": "basari",
            "kendini sına": "sina", "kendini sina": "sina",
            "takıldıysan": "takildiysan", "takildiysan": "takildiysan",
            "teslim": "teslim", "gereksinimler": "gereksinimler",
            "kabul kriterleri": "basari", "serbest alan": "serbest",
        }

        govde_html = []
        for bas, satirlar in bolumler:
            sinif = sinif_haritasi.get(bas.lower(), "diger")
            icerik = "\n".join(satirlar)
            if sinif == "takildiysan":
                ic = self._ipucu_merdiveni(icerik, gid)
            else:
                ic = Isleyici().cevir(icerik)
            govde_html.append(
                f'<div class="gorev-bolum {sinif}">'
                f'<div class="gorev-bolum-baslik">{html.escape(bas)}</div>{ic}</div>')

        noktalar = "".join(
            f'<svg viewBox="0 0 10 10" aria-hidden="true">'
            f'<circle cx="5" cy="5" r="4" class="{"dolu" if k < zorluk else "bos"}"/></svg>'
            for k in range(3))
        zorluk_adi = {1: "kolay", 2: "orta", 3: "zorlu"}[zorluk]
        rozet_no = "M" if mezuniyet else no
        ust_etiket = "Mezuniyet Görevi" if mezuniyet else f"Görev {no}"

        return (
            f'<section class="gorev-karti{" mezuniyet" if mezuniyet else ""}" id="{gid}">'
            f'<div class="gorev-baslik">'
            f'<div class="gorev-rozet" aria-hidden="true"><span class="no">{rozet_no}</span>GÖREV</div>'
            f'<div class="gorev-baslik-metin">'
            f'<div class="gorev-ust-etiket">{ust_etiket}</div>'
            f'<h3>{html.escape(baslik)}'
            f'<span class="zorluk" role="img" aria-label="zorluk: {zorluk_adi}" '
            f'title="zorluk: {zorluk_adi}">{noktalar}</span></h3></div>'
            f'<label class="gorev-tamam"><input type="checkbox" class="gorev-kutucuk" '
            f'data-gorev="{gid}"><span class="kutucuk"><svg viewBox="0 0 12 12" '
            f'aria-hidden="true"><path d="M2 6.5L5 9l5-6" fill="none" stroke-width="2" '
            f'stroke="currentColor"/></svg></span>'
            f'<span class="gorev-tamam-yazi">Tamamladım</span></label>'
            f'</div><div class="gorev-govde">{"".join(govde_html)}</div></section>'
        )

    def _ipucu_merdiveni(self, metin: str, gid: str) -> str:
        """::ipucu Başlık ... ::/  ve  ::cozum yol|Başlık ... ::/ blokları."""
        satirlar = metin.split("\n")
        parcalar, serbest, i = [], [], 0

        def serbesti_bosalt():
            if any(s.strip() for s in serbest):
                parcalar.append(Isleyici().cevir("\n".join(serbest)))
            serbest.clear()

        while i < len(satirlar):
            m = re.match(r"^::(ipucu|cozum)\s*(.*)$", satirlar[i])
            if not m:
                serbest.append(satirlar[i])
                i += 1
                continue
            tur, arg = m.group(1), m.group(2).strip()
            j = i + 1
            while j < len(satirlar) and satirlar[j].rstrip() != "::/":
                j += 1
            if j >= len(satirlar):
                uyar(f"{gid}: kapanmamış ::{tur} bloğu")
                break
            govde = "\n".join(satirlar[i + 1:j])
            serbesti_bosalt()
            ic = Isleyici().cevir(govde)
            if tur == "ipucu":
                parcalar.append(
                    f'<details class="ipucu"><summary>{html.escape(arg or "İpucu")}'
                    f'</summary><div class="ipucu-icerik">{ic}</div></details>')
            else:
                baslik = arg or "Tam çözüm"
                parcalar.append(
                    f'<details class="cozum"><summary>{html.escape(baslik)}'
                    f'</summary><div class="cozum-icerik">{ic}</div></details>')
            i = j + 1
        serbesti_bosalt()
        # merdiven dışarıdan tek bir katlanabilir "Takıldıysan" içinde sunulur
        return ('<details class="ipucu takildiysan-dis"><summary>Takıldıysan — '
                'ipucu merdiveni (önce kendin dene)</summary>'
                f'<div class="ipucu-icerik">{"".join(parcalar)}</div></details>')

    # --- adım 3: {{...}} direktifleri ---
    def _direktifler(self, metin: str) -> str:
        def svg_koy(m):
            parca = m.group(1).split("|", 1)
            dosya = parca[0].strip()
            aciklama = parca[1].strip() if len(parca) > 1 else ""
            yol = SVG / dosya
            if not yol.exists():
                uyar(f"SVG bulunamadı: {dosya}")
                return self._sakla(
                    f'<figure class="sema"><p><em>[şema eksik: {html.escape(dosya)}]</em>'
                    f'</p></figure>')
            icerik = yol.read_text(encoding="utf-8")
            icerik = re.sub(r"<\?xml[^>]*\?>\s*", "", icerik)
            if "<title" not in icerik:
                uyar(f"SVG'de <title> yok: {dosya}")
            for renk in re.findall(r"(?:fill|stroke)=\"(#[0-9a-fA-F]{3,8})\"", icerik):
                uyar(f"SVG'de hard-coded renk ({renk}): {dosya}")
            bas_html = ""
            if aciklama:
                m2 = re.match(r"^(Şekil\s+\d+)\s*[—-]\s*(.*)$", aciklama)
                if m2:
                    bas_html = (f'<figcaption><span class="sekil-no">{m2.group(1)}.</span> '
                                f'{html.escape(m2.group(2))}</figcaption>')
                else:
                    bas_html = f"<figcaption>{html.escape(aciklama)}</figcaption>"
            return self._sakla(f'<figure class="sema">{icerik}{bas_html}</figure>')

        def kod_koy(m):
            yol = LABS / m.group(1).strip()
            if not yol.exists():
                uyar(f"lab dosyası bulunamadı: {m.group(1)}")
                return self._sakla(
                    f'<div class="kod-kutu"><div class="kod-etiket"><span>eksik: '
                    f'{html.escape(m.group(1))}</span></div><pre><code></code></pre></div>')
            dil = {".c": "c", ".h": "h", ".py": "py", ".md": "md",
                   ".ld": "ld", ".tcl": "tcl", ".mk": "make"}.get(yol.suffix, "metin")
            return self._sakla(kod_kutusu(yol.read_text(encoding="utf-8"), dil,
                                          f"labs/{m.group(1).strip()}"))

        metin = re.sub(r"\{\{svg:([^}]+)\}\}", svg_koy, metin)
        metin = re.sub(r"\{\{kod:([^}]+)\}\}", kod_koy, metin)
        metin = metin.replace("{{ilerleme-panosu}}",
                              self._sakla("PANO-YERI"))
        return metin

    # --- hepsi bir arada ---
    def cevir(self, metin: str) -> str:
        metin = self._kodlari_ayir(metin)
        metin = self._bloklari_isle(metin)
        metin = self._direktifler(metin)
        sonuc = markdown.markdown(metin, extensions=MD_UZANTILAR)
        # tabloları kaydırılabilir sar
        sonuc = sonuc.replace("<table>", '<div class="tablo-sar"><table>')
        sonuc = sonuc.replace("</table>", "</table></div>")
        # Azalan numara sırasıyla: kapsayıcılar (yüksek no) önce yerine oturur,
        # içlerinde taşıdıkları düşük numaralı placeholder'lar sonra çözülür.
        def _no(anahtar: str) -> int:
            return int(anahtar[7:-1])
        for anahtar, deger in sorted(self.yerler.items(),
                                     key=lambda kv: _no(kv[0]), reverse=True):
            sonuc = sonuc.replace(f"<p>{anahtar}</p>", deger).replace(anahtar, deger)
        return sonuc


# ---------------------------------------------------------------- pano SVG

def pano_uret(gorevler: list[dict]) -> str:
    """Yolculuk haritası: serpantin patika üzerinde duraklar."""
    if not gorevler:
        return ""
    SUTUN, GEN = 4, 760
    xler = [110, 290, 470, 650]
    y0, satir_araligi = 46, 108
    duraklar = []
    for i, g in enumerate(gorevler):
        satir, sutun = divmod(i, SUTUN)
        x = xler[sutun] if satir % 2 == 0 else xler[SUTUN - 1 - sutun]
        duraklar.append((x, y0 + satir * satir_araligi, g))
    yukseklik = duraklar[-1][1] + 62

    def parca_yolu(a, b):
        (x1, y1, _), (x2, y2, _) = a, b
        if y1 == y2:
            return f"M {x1} {y1} L {x2} {y2}"
        cik = GEN - 38 if x1 > GEN / 2 else 38
        return (f"M {x1} {y1} C {cik + (52 if cik > GEN / 2 else -52)} {y1}, "
                f"{cik + (52 if cik > GEN / 2 else -52)} {y2}, {x2} {y2}")

    taban, dolgular = [], []
    for i in range(1, len(duraklar)):
        yol = parca_yolu(duraklar[i - 1], duraklar[i])
        taban.append(f'<path class="patika-yol" d="{yol}"/>')
        dolgular.append(
            f'<path class="patika-yol-dolu patika-parca" '
            f'data-gorev="{duraklar[i][2]["id"]}" d="{yol}" style="opacity:0"/>')

    durak_html = []
    for i, (x, y, g) in enumerate(duraklar):
        etiket = html.escape(g["kisa"])
        kelimeler = etiket.split()
        satir1, satir2 = "", ""
        for k in kelimeler:
            if len(satir1) + len(k) <= 14 and not satir2:
                satir1 = (satir1 + " " + k).strip()
            else:
                satir2 = (satir2 + " " + k).strip()
        if len(satir2) > 16:
            satir2 = satir2[:15] + "…"
        ad_svg = (f'<text class="durak-ad" x="{x}" y="{y + 34}">{satir1}</text>')
        if satir2:
            ad_svg += f'<text class="durak-ad" x="{x}" y="{y + 47}">{satir2}</text>'
        no_gorunum = "M" if g["mezuniyet"] else g["no"]
        durak_html.append(
            f'<g class="durak{" mezuniyet" if g["mezuniyet"] else ""}" '
            f'data-gorev="{g["id"]}" role="button" tabindex="0" '
            f'aria-label="{html.escape(g["baslik"])}">'
            f'<circle class="durak-halka" cx="{x}" cy="{y}" r="14"/>'
            f'<text class="durak-no" x="{x}" y="{y + 3.6}">{no_gorunum}</text>'
            f'<path class="durak-tik" d="M {x - 5} {y} l 3.5 3.5 L {x + 5.5} {y - 4}"/>'
            f'{ad_svg}</g>')

    ilk = duraklar[0][2]
    ilk_parca = (f'<circle cx="{duraklar[0][0]}" cy="{duraklar[0][1]}" r="0"/>')
    return (
        '<div class="ilerleme-panosu" id="ilerleme-panosu">'
        '<div class="pano-baslik"><h3>Yolculuk Haritası</h3>'
        '<span class="pano-durum" id="pano-durum"></span></div>'
        '<div class="pano-ilerleme-cizgi"><div class="pano-ilerleme-dolu" '
        'id="pano-ilerleme-dolu"></div></div>'
        f'<svg viewBox="0 0 {GEN} {yukseklik}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Görev ilerleme haritası">'
        f'<title>Yolculuk haritası: görev durakları</title>'
        f'{"".join(taban)}{"".join(dolgular)}{ilk_parca}{"".join(durak_html)}</svg>'
        "</div>"
    )


# ---------------------------------------------------------------- toplama

def bolumleri_derle() -> tuple[str, list[dict]]:
    dosyalar = sorted(p for p in ICERIK.glob("*.md")
                      if not p.name.startswith("_"))
    if not dosyalar:
        uyar("content/ altında bölüm dosyası yok")
    kullanilan_idler: set = set()
    govdeler, toc = [], []

    for dosya in dosyalar:
        metin = dosya.read_text(encoding="utf-8")
        # ilk '# ' başlığı bölüm başlığıdır
        m = re.match(r"^#\s+(.+?)\s*\n", metin)
        if m:
            bolum_basligi = m.group(1).strip()
            metin = metin[m.end():]
        else:
            bolum_basligi = dosya.stem
            uyar(f"{dosya.name}: '# Başlık' ile başlamıyor")
        _MEVCUT_BOLUM[0] = bolum_basligi

        bolum_id = slugla(bolum_basligi, kullanilan_idler)
        icerik_html = Isleyici().cevir(metin)

        # ## → h3, ### → h4 zaten markdown h2/h3 üretir; bölüm başlığı h2 olur.
        # içerikteki h2'leri h3'e, h3'leri h4'e indir
        icerik_html = re.sub(r"<(/?)h3(?=[ >])", r"<\1h4", icerik_html)
        icerik_html = re.sub(r"<(/?)h2(?=[ >])", r"<\1h3", icerik_html)

        # h3/h4'lere id + anchor
        alt_basliklar = []

        def id_ver(m2):
            seviye, ic = m2.group(1), m2.group(2)
            duz = re.sub(r"<[^>]+>", "", ic)
            hid = slugla(duz, kullanilan_idler)
            if seviye == "3":
                alt_basliklar.append({"id": hid, "baslik": duz,
                                      "sira": m2.start()})
            return (f'<h{seviye} id="{hid}">{ic}'
                    f'<a class="baslik-anchor" href="#{hid}" '
                    f'aria-label="bağlantı">#</a></h{seviye}>')

        icerik_html = re.sub(r"<h([34])>(.*?)</h\1>", id_ver, icerik_html,
                             flags=re.DOTALL)

        # bölüm başlığı görünümü: "Bölüm N — Ad" / "Ek A — Ad"
        m3 = re.match(r"^((?:Bölüm|Ek)\s+\S+)\s*[—-]\s*(.+)$", bolum_basligi)
        if m3:
            baslik_html = (f'<span class="bolum-no">{html.escape(m3.group(1))}</span>'
                           f'{html.escape(m3.group(2))}')
        else:
            baslik_html = html.escape(bolum_basligi)

        govdeler.append(
            f'<section class="bolum" id="{bolum_id}">'
            f'<h2 id="{bolum_id}-baslik">{baslik_html}'
            f'<a class="baslik-anchor" href="#{bolum_id}" aria-label="bağlantı">#</a>'
            f"</h2>{icerik_html}</section>")

        # TOC girdileri: alt başlıklar + bu bölümdeki görevler, belge sırasıyla
        girdiler = list(alt_basliklar)
        for g in GOREV_KAYITLARI:
            if g["bolum"] == bolum_basligi:
                konum = icerik_html.find(f'id="{g["id"]}"')
                girdiler.append({"id": g["id"],
                                 "baslik": ("Mezuniyet Görevi" if g["mezuniyet"]
                                            else f'Görev {g["no"]} — {g["kisa"]}'),
                                 "sira": konum, "gorev": True})
        girdiler.sort(key=lambda x: x["sira"])
        toc.append({"id": bolum_id, "baslik": bolum_basligi, "altlar": girdiler})

    return "\n".join(govdeler), toc


def toc_uret(toc: list[dict]) -> str:
    parcalar = ["<ol>"]
    for b in toc:
        m = re.match(r"^((?:Bölüm|Ek)\s+\S+)\s*[—-]\s*(.+)$", b["baslik"])
        gorunen = f'{m.group(1)} · {m.group(2)}' if m else b["baslik"]
        parcalar.append(f'<li><a href="#{b["id"]}">{html.escape(gorunen)}</a>')
        if b["altlar"]:
            parcalar.append("<ol>")
            for a in b["altlar"]:
                if a.get("gorev"):
                    parcalar.append(
                        f'<li class="toc-gorev" data-gorev="{a["id"]}">'
                        f'<a href="#{a["id"]}">{html.escape(a["baslik"])}</a></li>')
                else:
                    parcalar.append(
                        f'<li><a href="#{a["id"]}">{html.escape(a["baslik"])}</a></li>')
            parcalar.append("</ol>")
        parcalar.append("</li>")
    parcalar.append("</ol>")
    return "".join(parcalar)


# ---------------------------------------------------------------- sayfa

def sayfa_uret(govde: str, toc_html: str, pano_html: str) -> str:
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    gorev_sayisi = len(GOREV_KAYITLARI)

    kapak = f"""
<div class="kapak">
  <div class="seri-etiket">{html.escape(SERI)}</div>
  <h1>{html.escape(BASLIK)}</h1>
  <p class="kapak-alt">{html.escape(ALT_BASLIK)} — Zynq UltraScale+ RFSoC (ZCU111)
  ile bare-metal'den FreeRTOS'a, ilk gününden mezuniyet görevine rehberli bir patika.</p>
  <div class="kapak-meta">
    <span><strong>Hedef kitle:</strong> ekibe yeni katılan elektrik-elektronik mühendisi</span>
    <span><strong>Donanım:</strong> ZCU111 geliştirme kartı</span>
    <span><strong>Görev sayısı:</strong> {gorev_sayisi}</span>
  </div>
</div>"""

    govde = govde.replace("PANO-YERI", pano_html)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(BASLIK)} — {html.escape(ALT_BASLIK)}</title>
<meta name="description" content="ZCU111 ile gömülü sistemlere rehberli oryantasyon yolculuğu.">
<style>
{css}
</style>
</head>
<body>
<header class="ust-cubuk">
  <span class="baslik-kisa">{html.escape(BASLIK)} · {html.escape(ALT_BASLIK)}</span>
  <span class="bosluk"></span>
  <span class="gorev-sayac" id="gorev-sayac"></span>
  <button type="button" class="tema-dugme" id="tema-dugme" aria-label="Tema değiştir">
    <svg id="tema-gunes" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>
    <svg id="tema-ay" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><path d="M20.5 14.5A8.5 8.5 0 019.5 3.5a8.5 8.5 0 1011 11z"/></svg>
  </button>
  <div class="okuma-bar" id="okuma-bar"></div>
</header>
<div class="sayfa">
<nav class="toc" aria-label="İçindekiler">
{toc_html}
</nav>
<main>
{kapak}
{govde}
</main>
</div>
<script>
{js}
</script>
</body>
</html>"""


def main() -> int:
    print("gomulu-oryantasyon build başlıyor...")
    GOREV_KAYITLARI.clear()
    govde, toc = bolumleri_derle()
    pano = pano_uret(GOREV_KAYITLARI)
    if "PANO-YERI" not in govde and GOREV_KAYITLARI:
        uyar("{{ilerleme-panosu}} hiçbir bölümde yok")
    cikti = sayfa_uret(govde, toc_uret(toc), pano)
    CIKTI.parent.mkdir(exist_ok=True)
    CIKTI.write_text(cikti, encoding="utf-8")
    boyut = CIKTI.stat().st_size
    print(f"  yazıldı: {CIKTI.relative_to(KOK)} ({boyut / 1024:.0f} KB, "
          f"{len(GOREV_KAYITLARI)} görev, {len(toc)} bölüm)")
    if boyut > 2_500_000:
        uyar(f"HTML 2.5 MB hedefini aşıyor: {boyut / 1e6:.2f} MB")
    if UYARILAR:
        print(f"  toplam {len(UYARILAR)} uyarı — yayın öncesi sıfırlanmalı.",
              file=sys.stderr)
    else:
        print("  uyarı yok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
