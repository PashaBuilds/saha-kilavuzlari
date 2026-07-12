#!/usr/bin/env python3
"""
guncelle.py — Saha Kılavuzları raf güncelleyici
================================================
İki katmanı senkronlar:

  kilavuzlar/<slug>/index.html   ← derlenmiş kılavuz (okuma rafı)
  kaynak/<repo-adı>/             ← kılavuzun TAM kaynak yansısı (düzenleme)

Kaynak repoları iki yerde arar (öncelik sırasıyla):

  1. Üst dizindeki kardeş repolar: ../*-saha-kilavuzu   (yazar makinesi)
  2. Repo içindeki yansılar:       kaynak/*-saha-kilavuzu (klonlanmış makine)

Yazar makinesinde her kardeş repo için dist kopyalanır VE kaynak ağacı
(kaynak/ altına, .git/node_modules/dist hariç) yansıtılır. Klonda ise
kaynak/ içindeki kopya düzenlenip build alındıktan sonra bu script yeni
dist'i rafa taşır. `kilavuzlar.js`teki boyut/guncelleme alanları tazelenir.

Kayıtlı olmayan yeni bir kılavuz bulunursa dosyaları yine kopyalanır ve
`kilavuzlar.js`e yapıştırılmaya hazır bir kayıt taslağı basılır.

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
RAF = HUB / "kilavuzlar"
KAYNAK = HUB / "kaynak"
SON_EK = "-saha-kilavuzu"

# Kaynak yansısına girmeyecekler: sürüm geçmişi, üretilebilir/dev artıkları.
YANSI_HARICLERI = (".git", "node_modules", "dist", ".DS_Store", ".cache", ".claude")


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


def kayit_guncelle(js: str, slug: str, boyut: str, tarih: str):
    """kilavuzlar.js içinde ilgili slug bloğunun boyut/guncelleme alanlarını yazar.
    Döndürür: (yeni_metin, bulundu_mu)"""
    blok = re.search(r"\{[^{}]*?slug:\s*\"" + re.escape(slug) + r"\"[^{}]*?\}", js, re.S)
    if not blok:
        return js, False
    eski = blok.group(0)
    yeni = re.sub(r"(boyut:\s*\")[^\"]*(\")", r"\g<1>" + boyut + r"\g<2>", eski)
    yeni = re.sub(r"(guncelleme:\s*\")[^\"]*(\")", r"\g<1>" + tarih + r"\g<2>", yeni)
    return js.replace(eski, yeni), True


def kaynak_yansit(repo: Path) -> Path:
    """Kaynak repoyu kaynak/<ad> altına tam (ama temiz) yansıtır."""
    hedef = KAYNAK / repo.name
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(repo, hedef, ignore=shutil.ignore_patterns(*YANSI_HARICLERI))
    return hedef


def taslak_bas(slug: str, baslik: str, boyut: str, tarih: str):
    print(f"""
  ┌─ YENİ KILAVUZ: {slug} ─ kilavuzlar.js'e kayıt gerekiyor ─────────────
  │ Dosyaları kopyalandı ama rafta kartı yok. Aşağıdaki taslağı
  │ kilavuzlar.js'teki listeye ekle; aciklama/etiketler alanlarını yaz,
  │ renk için boş bir hue açısı seç (kullanılanlar dosyanın başında yazar).
  └───────────────────────────────────────────────────────────────────────
  {{
    sira: <SIRADAKI-NUMARA>,
    slug: "{slug}",
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

    # Adaylar: kardeş repolar (yazar) öncelikli, kaynak/ yansıları (klon) yedek.
    adaylar: dict[str, tuple[str, Path]] = {}
    for d in sorted(UST_DIZIN.glob(f"*{SON_EK}")):
        if d.is_dir() and d.resolve() != HUB:
            adaylar[d.name] = ("kardeş", d)
    if KAYNAK.exists():
        for d in sorted(KAYNAK.glob(f"*{SON_EK}")):
            if d.is_dir():
                adaylar.setdefault(d.name, ("kaynak/", d))

    if not adaylar:
        print(f"Uyarı: ne {UST_DIZIN} altında kardeş repo ne de {KAYNAK} altında yansı var.")
        return 1

    print(f"Raf: {HUB}\n")

    yeni_var = False
    for ad, (koken, repo) in adaylar.items():
        slug = ad.removesuffix(SON_EK)
        dist = repo / "dist" / "index.html"

        if not dist.exists():
            print(f"  ⚠ {ad} [{koken}]: dist/index.html yok — atlandı.")
            print(f"      build almak için: cd {repo} && {build_ipucu(repo)}")
            continue

        hedef = RAF / slug / "index.html"
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dist, hedef)

        # Yazar makinesindeysek kaynak ağacını da yansıt.
        yansi_notu = ""
        if koken == "kardeş":
            kaynak_yansit(repo)
            yansi_notu = " + kaynak yansıtıldı"

        boyut = insan_boyut(dist.stat().st_size)
        tarih = datetime.fromtimestamp(dist.stat().st_mtime).strftime("%Y-%m-%d")

        js, kayitli = kayit_guncelle(js, slug, boyut, tarih)
        durum = "kayıt tazelendi" if kayitli else "KAYIT YOK → taslak aşağıda"
        print(f"  ✓ {slug:<14} {boyut:>8}  {tarih}  [{koken}] raf güncellendi{yansi_notu}, {durum}")

        if not kayitli:
            yeni_var = True
            taslak_bas(slug, dist_basligi(dist), boyut, tarih)

    KAYIT_DOSYASI.write_text(js, encoding="utf-8")

    # Rafta olup artık hiçbir kaynağı olmayan klasörleri haber ver (silmez).
    if RAF.exists():
        mevcut = {ad.removesuffix(SON_EK) for ad in adaylar}
        for eski in sorted(RAF.iterdir()):
            if eski.is_dir() and eski.name not in mevcut:
                print(f"  ⚠ rafta '{eski.name}' duruyor ama kaynağı yok (elle karar ver).")

    print("\nBitti." + (" Yeni kılavuz kaydını kilavuzlar.js'e eklemeyi unutma!" if yeni_var else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
