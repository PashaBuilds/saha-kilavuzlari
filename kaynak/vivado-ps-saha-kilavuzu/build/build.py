# -*- coding: utf-8 -*-
"""
build.py — vivado-ps-saha-kilavuzu build sistemi

content/*.md dosyalarını sıra ile okur, markdown alt kümesi + özel
direktifleri HTML'e çevirir, CSS/JS/SVG/screenshot'ları inline ederek
tamamen self-contained dist/index.html üretir.

Kullanım:  python build/build.py

Özel direktifler (markdown içinde):
  :::saha-notu | tuzak | derin-dalis | analoji | ekip-notu | yazilima-yansimasi
  ...gövde...
  :::
      → renkli kutu

  :::deneme id=deneme-5-1
  ...görev gövdesi...
  ::cozum::
  ...katlanabilir çözüm...
  :::
      → lab görev kartı (checkbox + localStorage)

  :::kontrol id=kontrol-bringup
  - madde bir
  - madde iki
  :::
      → kalıcı işaretlenebilir kontrol listesi

  [[adim: Flow Navigator → IP Integrator → Open Block Design]]
      → vivado-adim tıklama-yolu şeridi (kopyalanabilir)

  [[sema: dosya-adi | figcaption metni]]
      → assets/svg/dosya-adi.svg inline edilir (Katman C)

  [[bd: dosya-adi | altyazı]]
      → assets/bd-exports/dosya-adi.svg zoom/pan görüntüleyicide (Katman A)

  [[ekran: 07 | Başlık
  rozet 1: açıklama
  rozet 2: açıklama
  not: figcaption ek metni
  ]]
      → Katman B ekran çerçevesi. Görsel önceliği:
        assets/svg/ekran-07.svg (açıklama katmanı; içindeki __SHOT_07__
        yer tutucusu base64 PNG ile değiştirilir)
        → yoksa assets/screenshots/shot-07.png
        → o da yoksa placeholder + eksik raporu
"""

import base64
import html
import re
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"

DOC_BASLIK = "Vivado'yu Yazılımcı Gibi Okumak"
DOC_ALT = "PS Perspektifinden Sayısal Tasarım Analizi — Saha Kılavuzu"
SURUM_NOTU = ("Bu kılavuzdaki ekranlar ve komutlar Vivado 2022.2 ile üretilmiş ve "
              "doğrulanmıştır. Ekran yerleşimleri sürümler arasında değişebilir; "
              "kavramlar kalıcıdır.")

KUTU_TURLERI = {
    "saha-notu": "Saha Notu",
    "tuzak": "Tuzak",
    "derin-dalis": "Derin Dalış",
    "analoji": "Analoji",
    "ekip-notu": "Ekip Notu",
    "yazilima-yansimasi": "Yazılıma Yansıması",
}

eksikler = []       # (tur, detay)
istatistik = {}     # bolum_id -> dict(sayaçlar)


def slugify(s: str) -> str:
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    s = s.translate(tr).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "bolum"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


# ---------------------------------------------------------------- inline md
_KOD_YER = "\x00KOD%d\x00"

def inline_md(s: str) -> str:
    """Satır içi markdown: `kod`, **kalın**, *italik*, [metin](href)."""
    kodlar = []
    def kod_al(m):
        kodlar.append(m.group(1))
        return _KOD_YER % (len(kodlar) - 1)
    s = re.sub(r"`([^`]+)`", kod_al, s)
    s = esc(s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    for i, k in enumerate(kodlar):
        s = s.replace(_KOD_YER % i, "<code>%s</code>" % html.escape(k))
    return s


# ---------------------------------------------------------------- bileşenler
def yap_adim(icerik: str) -> str:
    parcalar = [p.strip() for p in icerik.split("→")]
    ic = '<span class="ok"> › </span>'.join(
        '<span class="adim">%s</span>' % esc(p) for p in parcalar if p)
    duz = " > ".join(p for p in parcalar if p)
    return ('<div class="vivado-adim" data-yol="%s">%s'
            '<button class="kopyala" title="Yolu kopyala">kopyala</button></div>'
            % (html.escape(duz, quote=True), ic))


def svg_oku_inline(yol: Path, kimlik_oneki: str = "") -> str | None:
    if not yol.exists():
        return None
    t = yol.read_text(encoding="utf-8")
    t = re.sub(r"<\?xml[^>]*\?>", "", t)
    t = re.sub(r"<!DOCTYPE[^>]*>", "", t)
    return t.strip()


def png_data_uri(yol: Path) -> str | None:
    if not yol.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(yol.read_bytes()).decode()


def svg_data_uri(yol: Path) -> str | None:
    if not yol.exists():
        return None
    return ("data:image/svg+xml;base64,"
            + base64.b64encode(yol.read_bytes()).decode())


def yap_sema(ad: str, caption: str, sayac: dict) -> str:
    yol = ASSETS / "svg" / (ad + ".svg")
    svg = svg_oku_inline(yol)
    if svg is None:
        eksikler.append(("sema", ad))
        svg = ('<div class="eksik">Şema hazırlanıyor: <code>%s.svg</code></div>'
               % esc(ad))
    else:
        sayac["sema"] = sayac.get("sema", 0) + 1
    cap = ("<figcaption>%s</figcaption>" % inline_md(caption)) if caption else ""
    return '<figure class="sema" id="sema-%s">%s%s</figure>' % (slugify(ad), svg, cap)


def yap_bd(ad: str, altyazi: str, sayac: dict) -> str:
    yol = ASSETS / "bd-exports" / (ad + ".svg")
    uri = svg_data_uri(yol)
    if uri is None:
        eksikler.append(("bd-export", ad))
        govde = ('<div class="eksik" style="height:200px;display:flex;'
                 'align-items:center;justify-content:center">BD export bekleniyor: '
                 '<code>%s.svg</code></div>' % esc(ad))
    else:
        sayac["bd"] = sayac.get("bd", 0) + 1
        govde = ('<div class="bd-tuval"><img src="%s" alt="%s" draggable="false"></div>'
                 % (uri, html.escape(altyazi or ad, quote=True)))
    return (
        '<div class="bd-viewer" id="bd-%s">'
        '<div class="bd-arac">'
        '<button class="bd-buyut" title="Yakınlaştır">+</button>'
        '<button class="bd-kucult" title="Uzaklaştır">−</button>'
        '<button class="bd-sifirla" title="Sıfırla">⌂</button>'
        '</div>%s<div class="bd-ipucu">sürükle: kaydır · tekerlek: yakınlaştır</div></div>'
        '<p class="bd-altyazi">%s</p>' % (slugify(ad), govde, inline_md(altyazi))
    )


def yap_ekran(blok: str, sayac: dict) -> str:
    """[[ekran: NN | Başlık \n rozet 1: ... \n not: ...]]"""
    satirlar = blok.split("\n")
    bas = satirlar[0]
    m = re.match(r"\s*(\S+)\s*\|\s*(.+)", bas)
    if not m:
        return "<!-- bozuk ekran direktifi -->"
    no, baslik = m.group(1).strip(), m.group(2).strip()
    rozetler, notlar = [], []
    for s in satirlar[1:]:
        s = s.strip()
        rm = re.match(r"rozet\s+(\d+)\s*:\s*(.+)", s)
        if rm:
            rozetler.append((rm.group(1), rm.group(2)))
        elif s.startswith("not:"):
            notlar.append(s[4:].strip())

    ann_svg = ASSETS / "svg" / ("ekran-%s.svg" % no)
    png = ASSETS / "screenshots" / ("shot-%s.png" % no)
    govde = None
    if ann_svg.exists():
        svg = svg_oku_inline(ann_svg)
        uri = png_data_uri(png)
        yer = "__SHOT_%s__" % no
        if uri and yer in svg:
            svg = svg.replace(yer, uri)
            govde = svg
            sayac["ekran"] = sayac.get("ekran", 0) + 1
        elif yer not in svg:
            govde = svg  # açıklama katmanı görüntüyü kendisi gömmüş
            sayac["ekran"] = sayac.get("ekran", 0) + 1
    if govde is None and png.exists():
        uri = png_data_uri(png)
        govde = ('<img src="%s" alt="Ekran %s: %s" loading="lazy">'
                 % (uri, esc(no), html.escape(baslik, quote=True)))
        sayac["ekran"] = sayac.get("ekran", 0) + 1
        eksikler.append(("aciklama-katmani", "ekran-%s (ham screenshot var, SVG katmanı yok)" % no))
    if govde is None:
        eksikler.append(("screenshot", "shot-%s.png — %s" % (no, baslik)))
        govde = ('<div class="eksik">Ekran görüntüsü bekleniyor: '
                 '<code>assets/screenshots/shot-%s.png</code><br>%s<br>'
                 'Çekim reçetesi: SHOT-LIST.md</div>' % (esc(no), esc(baslik)))

    roz_html = ""
    if rozetler:
        roz_html = ('<ol class="rozetler">%s</ol>'
                    % "".join('<li data-no="%s">%s</li>' % (r, inline_md(t))
                              for r, t in rozetler))
    not_html = "".join("<p>%s</p>" % inline_md(n) for n in notlar)
    return (
        '<figure class="ekran" id="ekran-%s">'
        '<div class="ekran-baslik"><span class="ekran-no">Ekran %s</span>'
        '<span>%s</span></div>'
        '<div class="ekran-govde">%s</div>'
        '<figcaption>%s%s</figcaption></figure>'
        % (no, no.lstrip("0") or "0", inline_md(baslik), govde, not_html, roz_html)
    )


# ---------------------------------------------------------------- blok parser
def md_to_html(md: str, bolum_id: str, sayac: dict) -> str:
    out = []
    lines = md.split("\n")
    i = 0
    n = len(lines)

    def paragraf_bitir(buf):
        if buf:
            out.append("<p>%s</p>" % inline_md(" ".join(buf).strip()))
            buf.clear()

    pbuf = []
    while i < n:
        line = lines[i]
        s = line.strip()

        # --- çok satırlı direktifler
        if s.startswith(":::") and len(s) > 3:
            paragraf_bitir(pbuf)
            bas = s[3:].strip()
            govde = []
            i += 1
            while i < n and lines[i].strip() != ":::":
                govde.append(lines[i])
                i += 1
            i += 1
            out.append(direktif_isle(bas, "\n".join(govde), bolum_id, sayac))
            continue

        # --- tek satır bileşen: [[adim: ...]]
        m = re.match(r"\[\[adim:\s*(.+?)\]\]\s*$", s)
        if m:
            paragraf_bitir(pbuf)
            out.append(yap_adim(m.group(1)))
            sayac["adim"] = sayac.get("adim", 0) + 1
            i += 1
            continue

        m = re.match(r"\[\[sema:\s*([^|\]]+?)\s*(?:\|\s*(.*?))?\]\]\s*$", s)
        if m:
            paragraf_bitir(pbuf)
            out.append(yap_sema(m.group(1).strip(), (m.group(2) or "").strip(), sayac))
            i += 1
            continue

        m = re.match(r"\[\[bd:\s*([^|\]]+?)\s*(?:\|\s*(.*?))?\]\]\s*$", s)
        if m:
            paragraf_bitir(pbuf)
            out.append(yap_bd(m.group(1).strip(), (m.group(2) or "").strip(), sayac))
            i += 1
            continue

        # --- çok satırlı ekran direktifi
        if s.startswith("[[ekran:"):
            paragraf_bitir(pbuf)
            blok = [s[len("[[ekran:"):]]
            while not blok[-1].rstrip().endswith("]]") and i + 1 < n:
                i += 1
                blok.append(lines[i])
            blok[-1] = blok[-1].rstrip()
            if blok[-1].endswith("]]"):
                blok[-1] = blok[-1][:-2]
            out.append(yap_ekran("\n".join(blok).strip(), sayac))
            i += 1
            continue

        # --- kod bloğu
        if s.startswith("```"):
            paragraf_bitir(pbuf)
            dil = s[3:].strip()
            kod = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                kod.append(lines[i])
                i += 1
            i += 1
            kod_txt = html.escape("\n".join(kod))
            dil_html = ('<span class="dil-etiket">%s</span>' % esc(dil)) if dil else ""
            out.append('<pre class="kod-kutu">%s'
                       '<button class="kopyala" title="Kodu kopyala">kopyala</button>'
                       '<code>%s</code></pre>' % (dil_html, kod_txt))
            continue

        # --- başlıklar (içerik dosyasında ## => h3 sayfa hiyerarşisi)
        m = re.match(r"(#{1,4})\s+(.*)", s)
        if m:
            paragraf_bitir(pbuf)
            seviye = len(m.group(1))
            metin = m.group(2).strip()
            hid = bolum_id + "--" + slugify(re.sub(r"[`*]", "", metin))
            etiket = {1: "h2", 2: "h3", 3: "h4", 4: "h4"}[seviye]
            out.append('<%s id="%s">%s<a class="baslik-halka" href="#%s">#</a></%s>'
                       % (etiket, hid, inline_md(metin), hid, etiket))
            i += 1
            continue

        # --- tablo
        if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|?$", lines[i + 1].strip()):
            paragraf_bitir(pbuf)
            basliklar = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            satirlar = []
            while i < n and lines[i].strip().startswith("|"):
                satirlar.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join("<th>%s</th>" % inline_md(c) for c in basliklar)
            tb = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline_md(c) for c in r)
                         for r in satirlar)
            out.append('<div class="tablo-sar"><table><thead><tr>%s</tr></thead>'
                       '<tbody>%s</tbody></table></div>' % (th, tb))
            continue

        # --- listeler
        if re.match(r"[-*]\s+", s) or re.match(r"\d+[.)]\s+", s):
            paragraf_bitir(pbuf)
            sirali = bool(re.match(r"\d+[.)]\s+", s))
            ogeler = []
            while i < n:
                ls = lines[i].strip()
                if re.match(r"[-*]\s+", ls) and not sirali:
                    ogeler.append(re.sub(r"^[-*]\s+", "", ls))
                elif re.match(r"\d+[.)]\s+", ls) and sirali:
                    ogeler.append(re.sub(r"^\d+[.)]\s+", "", ls))
                elif ls and (lines[i].startswith("  ") or lines[i].startswith("\t")) and ogeler:
                    ogeler[-1] += " " + ls
                else:
                    break
                i += 1
            etiket = "ol" if sirali else "ul"
            out.append("<%s>%s</%s>" % (etiket,
                       "".join("<li>%s</li>" % inline_md(o) for o in ogeler), etiket))
            continue

        # --- blockquote
        if s.startswith(">"):
            paragraf_bitir(pbuf)
            q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % inline_md(" ".join(q)))
            continue

        # --- hr
        if re.match(r"^-{3,}$", s):
            paragraf_bitir(pbuf)
            out.append("<hr>")
            i += 1
            continue

        # --- boş satır
        if not s:
            paragraf_bitir(pbuf)
            i += 1
            continue

        pbuf.append(s)
        i += 1

    paragraf_bitir(pbuf)
    return "\n".join(out)


def direktif_isle(bas: str, govde: str, bolum_id: str, sayac: dict) -> str:
    parcalar = bas.split()
    tur = parcalar[0]
    attrs = dict(p.split("=", 1) for p in parcalar[1:] if "=" in p)

    if tur in KUTU_TURLERI:
        sayac[tur] = sayac.get(tur, 0) + 1
        ic = md_to_html(govde, bolum_id, sayac)
        return ('<aside class="kutu %s"><span class="kutu-baslik">%s</span>%s</aside>'
                % (tur, KUTU_TURLERI[tur], ic))

    if tur == "deneme":
        sayac["deneme"] = sayac.get("deneme", 0) + 1
        did = attrs.get("id", "deneme-%s-%d" % (bolum_id, sayac["deneme"]))
        if "::cozum::" in govde:
            gov, coz = govde.split("::cozum::", 1)
        else:
            gov, coz = govde, ""
        gov_html = md_to_html(gov, bolum_id, sayac)
        coz_html = ('<details><summary>Çözümü göster</summary>%s</details>'
                    % md_to_html(coz, bolum_id, sayac)) if coz.strip() else ""
        return ('<aside class="kutu deneme" id="%s">'
                '<span class="kutu-baslik"><input type="checkbox" data-kalici="%s" '
                'title="Tamamlandı olarak işaretle">Deneme</span>%s%s</aside>'
                % (did, did, gov_html, coz_html))

    if tur == "kontrol":
        kid = attrs.get("id", "kontrol-%s" % bolum_id)
        ogeler = []
        j = 0
        for ln in govde.split("\n"):
            ln = ln.strip()
            if ln.startswith("- "):
                j += 1
                ogeler.append('<label><input type="checkbox" data-kalici="%s-%d">'
                              '<span>%s</span></label>'
                              % (kid, j, inline_md(ln[2:])))
            elif ln.startswith("### "):
                ogeler.append("<h4>%s</h4>" % inline_md(ln[4:]))
        return '<div class="kontrol-listesi" id="%s">%s</div>' % (kid, "".join(ogeler))

    if tur == "ozet":
        ic = md_to_html(govde, bolum_id, sayac)
        return ('<div class="ozet"><span class="kutu-baslik">Bölüm Özeti</span>%s</div>' % ic)

    if tur == "sozluk":
        ogeler = []
        for ln in govde.split("\n"):
            m = re.match(r"\s*\*\*(.+?)\*\*\s*[—:-]\s*(.+)", ln)
            if m:
                ogeler.append("<dt id=\"sozluk-%s\">%s</dt><dd>%s</dd>"
                              % (slugify(m.group(1)), esc(m.group(1)), inline_md(m.group(2))))
        return '<dl class="sozluk">%s</dl>' % "".join(ogeler)

    return "<!-- bilinmeyen direktif: %s -->" % esc(tur)


# ---------------------------------------------------------------- sayfa
JS = r"""
(function () {
  // Tema
  var kok = document.documentElement;
  var kayitli = null;
  try { kayitli = localStorage.getItem('kilavuz-tema'); } catch (e) {}
  if (kayitli === 'light' || kayitli === 'dark') kok.setAttribute('data-theme', kayitli);
  var dugme = document.querySelector('.tema-dugme');
  function temaEtiket() {
    dugme.textContent = kok.getAttribute('data-theme') === 'light' ? '● koyu tema' : '○ açık tema';
  }
  dugme.addEventListener('click', function () {
    var yeni = kok.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    kok.setAttribute('data-theme', yeni);
    try { localStorage.setItem('kilavuz-tema', yeni); } catch (e) {}
    temaEtiket();
  });
  temaEtiket();

  // İlerleme çubuğu
  var bar = document.getElementById('ilerleme');
  function ilerle() {
    var h = document.documentElement;
    var oran = h.scrollTop / (h.scrollHeight - h.clientHeight);
    bar.style.width = (oran * 100).toFixed(2) + '%';
  }
  document.addEventListener('scroll', ilerle, { passive: true });
  ilerle();

  // TOC scrollspy
  var tocLinkler = Array.prototype.slice.call(document.querySelectorAll('#toc a'));
  var hedefler = tocLinkler.map(function (a) {
    return document.getElementById(a.getAttribute('href').slice(1));
  }).filter(Boolean);
  var etkin = null;
  var io = new IntersectionObserver(function (girisler) {
    girisler.forEach(function (g) {
      if (g.isIntersecting) {
        var id = g.target.id;
        tocLinkler.forEach(function (a) {
          a.classList.toggle('etkin', a.getAttribute('href') === '#' + id);
        });
      }
    });
  }, { rootMargin: '-10% 0px -80% 0px' });
  hedefler.forEach(function (h) { io.observe(h); });

  // Kopyala düğmeleri
  document.querySelectorAll('button.kopyala').forEach(function (b) {
    b.addEventListener('click', function () {
      var metin;
      var kap = b.closest('.vivado-adim');
      if (kap) { metin = kap.getAttribute('data-yol'); }
      else {
        var kod = b.parentElement.querySelector('code');
        metin = kod ? kod.textContent : '';
      }
      function tamam() {
        b.classList.add('kopyalandi'); b.textContent = 'kopyalandı';
        setTimeout(function () { b.classList.remove('kopyalandi'); b.textContent = 'kopyala'; }, 1400);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(metin).then(tamam, tamam);
      } else {
        var ta = document.createElement('textarea');
        ta.value = metin; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta); tamam();
      }
    });
  });

  // Kalıcı checkbox'lar (deneme + kontrol listesi)
  document.querySelectorAll('input[data-kalici]').forEach(function (cb) {
    var anahtar = 'kilavuz-cb-' + cb.getAttribute('data-kalici');
    var deger = null;
    try { deger = localStorage.getItem(anahtar); } catch (e) {}
    cb.checked = deger === '1';
    guncelle(cb);
    cb.addEventListener('change', function () {
      try { localStorage.setItem(anahtar, cb.checked ? '1' : '0'); } catch (e) {}
      guncelle(cb);
    });
    function guncelle(c) {
      var deneme = c.closest('.deneme');
      if (deneme) deneme.classList.toggle('tamam', c.checked);
      var etiket = c.closest('label');
      if (etiket) etiket.classList.toggle('tamam', c.checked);
    }
  });

  // BD zoom/pan görüntüleyici
  document.querySelectorAll('.bd-viewer').forEach(function (v) {
    var tuval = v.querySelector('.bd-tuval');
    var hedef = tuval && tuval.firstElementChild;
    if (!hedef || hedef.classList.contains('eksik')) return;
    var olcek = 1, tx = 0, ty = 0;
    function uygula() {
      hedef.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + olcek + ')';
    }
    function yakinlas(carpan, cx, cy) {
      var yeni = Math.min(12, Math.max(0.2, olcek * carpan));
      var r = tuval.getBoundingClientRect();
      var px = (cx !== undefined ? cx : r.width / 2) - r.left;
      var py = (cy !== undefined ? cy : r.height / 2) - r.top;
      tx = px - (px - tx) * (yeni / olcek);
      ty = py - (py - ty) * (yeni / olcek);
      olcek = yeni; uygula();
    }
    tuval.addEventListener('wheel', function (e) {
      e.preventDefault();
      yakinlas(e.deltaY < 0 ? 1.18 : 1 / 1.18, e.clientX, e.clientY);
    }, { passive: false });
    var surukle = null;
    tuval.addEventListener('pointerdown', function (e) {
      surukle = { x: e.clientX - tx, y: e.clientY - ty };
      tuval.setPointerCapture(e.pointerId);
    });
    tuval.addEventListener('pointermove', function (e) {
      if (!surukle) return;
      tx = e.clientX - surukle.x; ty = e.clientY - surukle.y; uygula();
    });
    tuval.addEventListener('pointerup', function () { surukle = null; });
    tuval.addEventListener('pointercancel', function () { surukle = null; });
    v.querySelector('.bd-buyut').addEventListener('click', function () { yakinlas(1.3); });
    v.querySelector('.bd-kucult').addEventListener('click', function () { yakinlas(1 / 1.3); });
    v.querySelector('.bd-sifirla').addEventListener('click', function () {
      olcek = 1; tx = 0; ty = 0; uygula();
    });
  });

  // Lightbox: ekran görsellerine tıkla → tam boyut
  var lb = document.createElement('div');
  lb.id = 'lightbox';
  lb.innerHTML = '<div class="lb-baslik"></div>' +
    '<button class="lb-kapat" title="Kapat (Esc)">✕</button>' +
    '<div class="lb-icerik"></div>';
  document.body.appendChild(lb);
  var lbIcerik = lb.querySelector('.lb-icerik');
  var lbBaslik = lb.querySelector('.lb-baslik');
  function lbKapat() { lb.classList.remove('acik'); lbIcerik.innerHTML = ''; }
  lb.addEventListener('click', function (e) {
    if (e.target === lb || e.target.classList.contains('lb-kapat') ||
        e.target.classList.contains('lb-icerik')) lbKapat();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') lbKapat();
  });
  document.querySelectorAll('figure.ekran .ekran-govde').forEach(function (g) {
    if (g.querySelector('.eksik')) return;
    g.addEventListener('click', function () {
      var kaynak = g.querySelector('img, svg');
      if (!kaynak) return;
      lbIcerik.innerHTML = '';
      lbIcerik.appendChild(kaynak.cloneNode(true));
      var fig = g.closest('figure.ekran');
      var bas = fig ? fig.querySelector('.ekran-baslik') : null;
      lbBaslik.textContent = bas ? bas.textContent : '';
      lb.classList.add('acik');
    });
  });
})();
"""


def derle():
    dosyalar = sorted(CONTENT.glob("*.md"))
    if not dosyalar:
        print("UYARI: content/ altında .md yok.")
    bolumler = []       # (id, no_metin, baslik, html, alt_basliklar)
    for f in dosyalar:
        md = f.read_text(encoding="utf-8")
        satirlar = md.split("\n")
        ilk = satirlar[0].strip()
        m = re.match(r"#\s+(.*)", ilk)
        baslik_tam = m.group(1).strip() if m else f.stem
        gov = "\n".join(satirlar[1:]) if m else md

        nm = re.match(r"(Bölüm\s+\d+|Ek\s+[A-Z]|Önsöz)\s*[—-]\s*(.*)", baslik_tam)
        if nm:
            no_metin, baslik = nm.group(1), nm.group(2)
        else:
            no_metin, baslik = "", baslik_tam
        bid = slugify(f.stem)
        sayac = {}
        istatistik[bid] = sayac
        govde_html = md_to_html(gov, bid, sayac)

        altlar = re.findall(r'<h3 id="([^"]+)">(.*?)<a class', govde_html)
        altlar = [(i2, re.sub(r"<[^>]+>", "", t2)) for i2, t2 in altlar]
        bolumler.append((bid, no_metin, baslik, govde_html, altlar))

    # TOC
    toc = ['<div class="toc-baslik">İçindekiler</div><ol>']
    for bid, no, baslik, _, altlar in bolumler:
        toc.append('<li><a href="#%s"><span class="bolum-no">%s</span> %s</a>' %
                   (bid, esc(no), esc(baslik)))
        if altlar:
            toc.append("<ol>")
            for aid, at in altlar:
                toc.append('<li><a href="#%s">%s</a></li>' % (aid, esc(at)))
            toc.append("</ol>")
        toc.append("</li>")
    toc.append("</ol>")

    govde = []
    for bid, no, baslik, bhtml, _ in bolumler:
        tam = ('<span class="bolum-no">%s</span>%s' % (esc(no), esc(baslik))) if no else esc(baslik)
        govde.append('<section id="%s"><h2 id="%s-baslik">%s'
                     '<a class="baslik-halka" href="#%s">#</a></h2>\n%s\n</section>'
                     % (bid, bid, tam, bid, bhtml))

    css = (ASSETS / "css" / "kilavuz.css").read_text(encoding="utf-8")
    simdi = datetime.date.today().isoformat()

    sayfa = f"""<!DOCTYPE html>
<html lang="tr" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(DOC_BASLIK)} — Saha Kılavuzu</title>
<style>
{css}
</style>
</head>
<body>
<div id="ilerleme"></div>
<header class="tepe">
  <span class="seri">Saha Kılavuzu</span>
  <span class="baslik">{esc(DOC_BASLIK)}</span>
  <span class="bosluk"></span>
  <button class="tema-dugme" type="button">tema</button>
</header>
<div class="sayfa">
<nav id="toc">{''.join(toc)}</nav>
<main>
<div class="kapak">
  <h1>{esc(DOC_BASLIK)}</h1>
  <div class="alt-baslik">{esc(DOC_ALT)}</div>
  <div class="surum-notu">{esc(SURUM_NOTU)} · Derleme: {simdi}</div>
</div>
{''.join(govde)}
</main>
</div>
<script>
{JS}
</script>
</body>
</html>
"""
    DIST.mkdir(exist_ok=True)
    hedef = DIST / "index.html"
    hedef.write_text(sayfa, encoding="utf-8")

    # ------- rapor
    print("=" * 60)
    print("BUILD TAMAM: %s (%.1f KB)" % (hedef, hedef.stat().st_size / 1024))
    print("Bölüm sayısı: %d" % len(bolumler))
    print("-" * 60)
    print("%-28s %5s %5s %6s %5s %5s" % ("bölüm", "ekran", "şema", "bd", "y-y", "den."))
    for bid, no, baslik, _, _2 in bolumler:
        s = istatistik[bid]
        print("%-28s %5d %5d %6d %5d %5d" % (
            bid[:28], s.get("ekran", 0), s.get("sema", 0), s.get("bd", 0),
            s.get("yazilima-yansimasi", 0), s.get("deneme", 0)))
    if eksikler:
        print("-" * 60)
        print("EKSİKLER (%d):" % len(eksikler))
        for tur, det in eksikler:
            print("  [%s] %s" % (tur, det))
    else:
        print("Eksik görsel yok.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(derle())
