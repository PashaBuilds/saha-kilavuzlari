#!/usr/bin/env python3
"""
guncelle.py — Saha Kılavuzları raf güncelleyici
================================================
Kayıt-güdümlü: `kilavuzlar.js`teki her belge için kaynağını bulur, iki katmanı
senkronlar ve boyut/tarih alanlarını tazeler.

  <yol>              ← derlenmiş belge, kartın açtığı dosya (okuma katmanı)
  kaynak/<kaynak>/   ← belgenin TAM kaynak yansısı (düzenleme katmanı)

Her kayıt `kaynak` (repo klasör adı) ve `yol` alanlarını taşır; `kaynak`
yoksa "<slug>-saha-kilavuzu" varsayılır. Kaynak repo iki yerde aranır
(öncelik sırasıyla):

  1. Üst dizindeki kardeş repo: ../<kaynak>        (yazar makinesi)
  2. Repo içindeki yansı:       kaynak/<kaynak>     (klonlanmış makine)

Kardeş repo varsa dist kopyalanır VE kaynak ağacı (kaynak/ altına;
.git/node_modules/dist/_önekli-scratch hariç) yansıtılır. Klonda ise kaynak/
içindeki kopya düzenlenip build alındıktan sonra bu script dist'i rafa taşır.

Kayıtsız yeni bir "*-saha-kilavuzu" reposu görülürse dosyaları yine kopyalanır
ve kilavuzlar.js'e yapıştırılacak kayıt taslağı basılır. (Son eki taşımayan
repolar — ör. gomulu-oryantasyon — otomatik keşfedilemez; kaydı elle eklenir,
sonra bu script onu da senkronlar.)

Kullanım:  python3 guncelle.py
Bağımlılık: yok (stdlib). Ağ erişimi: yok.
"""

import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

HUB = Path(__file__).resolve().parent
UST_DIZIN = HUB.parent
KAYIT_DOSYASI = HUB / "kilavuzlar.js"
KAYNAK = HUB / "kaynak"
SON_EK = "-saha-kilavuzu"

# Kaynak yansısına girmeyecekler: sürüm geçmişi, üretilebilir/dev artıkları,
# ve "_" ile başlayan yazar-scratch dosyaları (araştırma, stil, görev-zinciri —
# build'ler bunları zaten atlar).
YANSI_HARICLERI = (".git", "node_modules", "dist", ".DS_Store", ".cache", ".claude", "_*")


def insan_boyut(bayt: int) -> str:
    """302 KB / 2,1 MB biçiminde, Türkçe ondalık virgüllü boyut."""
    if bayt < 1024 * 1024:
        return f"{round(bayt / 1024)} KB"
    mb = bayt / (1024 * 1024)
    return f"{mb:.1f}".replace(".", ",") + " MB"


def dist_basligi(dosya: Path) -> str:
    """dist/index.html içindeki <title> etiketini çeker."""
    metin = dosya.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>([^<]+)</title>", metin)
    return m.group(1).strip() if m else "(başlık bulunamadı)"


def build_ipucu(repo: Path) -> str:
    """Repo tipine göre build komutu önerisi."""
    if (repo / "package.json").exists():
        return "npm install && npm run build"
    if (repo / "build" / "build.py").exists():
        return "python3 build/build.py"
    return "(repo içindeki build talimatına bak)"


def kayitlari_oku(js: str):
    """kilavuzlar.js'teki her { ... } bloğundan slug/kaynak/yol çıkarır.
    (Girişler iç içe süslü parantez içermez; array alanları [] kullanır.)"""
    kayitlar = []
    for blok in re.finditer(r"\{[^{}]*\}", js, re.S):
        t = blok.group(0)
        m_slug = re.search(r"slug:\s*\"([^\"]+)\"", t)
        if not m_slug:
            continue
        slug = m_slug.group(1)
        m_kaynak = re.search(r"kaynak:\s*\"([^\"]+)\"", t)
        m_yol = re.search(r"yol:\s*\"([^\"]+)\"", t)
        kayitlar.append({
            "slug": slug,
            "kaynak": m_kaynak.group(1) if m_kaynak else f"{slug}{SON_EK}",
            "yol": m_yol.group(1) if m_yol else f"kilavuzlar/{slug}/index.html",
        })
    return kayitlar


def kayit_guncelle(js: str, slug: str, boyut: str, tarih: str) -> str:
    """İlgili slug bloğunun boyut/guncelleme alanlarını yazar."""
    blok = re.search(r"\{[^{}]*?slug:\s*\"" + re.escape(slug) + r"\"[^{}]*?\}", js, re.S)
    if not blok:
        return js
    eski = blok.group(0)
    yeni = re.sub(r"(boyut:\s*\")[^\"]*(\")", r"\g<1>" + boyut + r"\g<2>", eski)
    yeni = re.sub(r"(guncelleme:\s*\")[^\"]*(\")", r"\g<1>" + tarih + r"\g<2>", yeni)
    return js.replace(eski, yeni)


def kaynak_yansit(repo: Path):
    """Kaynak repoyu kaynak/<ad> altına tam (ama temiz) yansıtır."""
    hedef = KAYNAK / repo.name
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(repo, hedef, ignore=shutil.ignore_patterns(*YANSI_HARICLERI))


def kaynak_bul(kaynak_ad: str):
    """(köken, repo_yolu) döndürür; kardeş öncelikli, kaynak/ yansısı yedek."""
    kardes = UST_DIZIN / kaynak_ad
    if kardes.is_dir() and kardes.resolve() != HUB:
        return "kardeş", kardes
    yansi = KAYNAK / kaynak_ad
    if yansi.is_dir():
        return "kaynak/", yansi
    return None, None


def taslak_bas(slug: str, kaynak_ad: str, baslik: str, boyut: str, tarih: str):
    print(f"""
  ┌─ YENİ KILAVUZ: {slug} ─ kilavuzlar.js'e kayıt gerekiyor ─────────────
  │ Dosyaları kopyalandı ama rafta kartı yok. Aşağıdaki taslağı
  │ kilavuzlar.js'teki listeye ekle; aciklama/etiketler alanlarını yaz,
  │ renk için boş bir hue açısı seç (kullanılanlar dosyanın başında yazar).
  └───────────────────────────────────────────────────────────────────────
  {{
    sira: <SIRADAKI-NUMARA>,
    slug: "{slug}",
    kaynak: "{kaynak_ad}",
    baslik: "{baslik.replace(' — Saha Kılavuzu', '')}",
    aciklama: "<2-3 cümlelik tanıtım — kim için, ne anlatıyor>",
    etiketler: ["<etiket>", "<etiket>", "<etiket>", "<etiket>", "<etiket>"],
    bolum: "<N bölüm + ekler>",
    bolumSayi: 0,
    sema: 0,
    kelime: 0,
    boyut: "{boyut}",
    guncelleme: "{tarih}",
    yol: "kilavuzlar/{slug}/index.html",
    renk: 210,
    motif: "varsayilan",
  }},
""")


def main() -> int:
    if not KAYIT_DOSYASI.exists():
        print(f"HATA: {KAYIT_DOSYASI} bulunamadı — hub kurulumu eksik.")
        return 1

    js = KAYIT_DOSYASI.read_text(encoding="utf-8")
    kayitlar = kayitlari_oku(js)

    print(f"Raf: {HUB}\n")

    # 1) Kayıtlı belgeleri senkronla.
    kayitli_kaynaklar = set()
    for kayit in kayitlar:
        slug, kaynak_ad, yol = kayit["slug"], kayit["kaynak"], kayit["yol"]
        kayitli_kaynaklar.add(kaynak_ad)
        koken, repo = kaynak_bul(kaynak_ad)

        if repo is None:
            print(f"  ⚠ {slug:<13} kaynak yok (ne ../{kaynak_ad} ne kaynak/{kaynak_ad}) — atlandı.")
            continue

        dist = repo / "dist" / "index.html"
        if not dist.exists():
            print(f"  ⚠ {slug:<13} [{koken}] dist/index.html yok — atlandı.")
            print(f"      build: cd {repo} && {build_ipucu(repo)}")
            continue

        hedef = HUB / yol
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dist, hedef)

        yansi_notu = ""
        if koken == "kardeş":
            kaynak_yansit(repo)
            yansi_notu = " + kaynak yansıtıldı"

        boyut = insan_boyut(dist.stat().st_size)
        tarih = datetime.fromtimestamp(dist.stat().st_mtime).strftime("%Y-%m-%d")
        js = kayit_guncelle(js, slug, boyut, tarih)
        print(f"  ✓ {slug:<13} {boyut:>8}  {tarih}  [{koken}] raf güncellendi{yansi_notu}")

    # 2) Kayıtsız yeni "*-saha-kilavuzu" repolarını keşfet.
    yeni_var = False
    for repo in sorted(UST_DIZIN.glob(f"*{SON_EK}")):
        if not repo.is_dir() or repo.resolve() == HUB or repo.name in kayitli_kaynaklar:
            continue
        dist = repo / "dist" / "index.html"
        if not dist.exists():
            print(f"  ⚠ {repo.name}: kayıtsız ve dist/index.html yok — atlandı.")
            continue
        slug = repo.name.removesuffix(SON_EK)
        hedef = HUB / "kilavuzlar" / slug / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dist, hedef)
        kaynak_yansit(repo)
        yeni_var = True
        taslak_bas(slug, repo.name,
                   dist_basligi(dist),
                   insan_boyut(dist.stat().st_size),
                   datetime.fromtimestamp(dist.stat().st_mtime).strftime("%Y-%m-%d"))

    KAYIT_DOSYASI.write_text(js, encoding="utf-8")

    print("\nBitti." + (" Yeni kılavuz kaydını kilavuzlar.js'e eklemeyi unutma!" if yeni_var else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
