# Ek A — Tcl Hızlı Başvuru (Yazılımcı Seti)

GUI açmadan cevap almanın reçeteleri. Bu komutlar repo'daki demo projelerle
2022.2'de birebir koşuldu; çıktıları `assets/reports/` altındadır. Kendi
projende de aynı komutlar çalışır.

## Projeyi batch açma (GUI'siz)

```tcl
# Salt-okunur inceleme: aç, oku, kaydetmeden kapat
open_project vivado/work/demo_ultrascale/demo_ultrascale.xpr
open_bd_design [get_files sistem.bd]
# ... sorgular ...
close_project
```

Komut satırından tek atış:

```bash
vivado -mode batch -source sorgu.tcl -nolog -nojournal -notrace
```

## Adres haritası raporu (Address Editor'ın Tcl'i)

```tcl
foreach seg [get_bd_addr_segs] {
    set ofs [get_property -quiet OFFSET $seg]
    set rng [get_property -quiet RANGE  $seg]
    if {$ofs ne ""} {
        puts "[format 0x%08llX $ofs]  $rng  $seg"
    }
}
```

Repo'da hazır: `vivado/export_visuals.tcl` bu mantığı
`assets/reports/<proje>-adres-haritasi.md` olarak tabloya döker.

## IP envanteri (blok dizaynda ne var)

```tcl
foreach c [lsort [get_bd_cells]] {
    puts "[get_property VLNV $c]\t$c"
}
```

## PS property dökme (bir ayarın değerini öğrenme)

```tcl
set ps [get_bd_cells ps_ultra]
# Tek ayar:
get_property CONFIG.PSU__UART0__PERIPHERAL__IO $ps       ;# -> MIO 18 .. 19
get_property CONFIG.PSU__CRL_APB__UART0_REF_CTRL__ACT_FREQMHZ $ps  ;# -> 99.990005
# Tüm CONFIG.* adlarını listele:
foreach p [lsort [list_property $ps]] {
    if {[string match CONFIG.* $p]} { puts "$p = [get_property $p $ps]" }
}
```

Versal CIPS için sözlük değeri PS_PMC_CONFIG içindedir:

```tcl
set cips [get_bd_cells versal_cips_0]
foreach {k v} [get_property CONFIG.PS_PMC_CONFIG $cips] { puts "$k = $v" }
# -> PS_UART0_PERIPHERAL = {ENABLE 1} {IO {PMC_MIO 42 .. 43}}
# -> DDR_MEMORY_MODE = Connectivity to DDR via NOC ...
```

## BD layout'u SVG'ye verme

```tcl
# Not: write_bd_layout GUI/TCL oturumunda çalışır, saf batch'te değil.
# GUI'yi start_gui ile açıp konsoldan koş:
write_bd_layout -force -format svg -orientation landscape out.svg
write_bd_layout -force -format pdf -orientation landscape out.pdf
```

## Validate (çakışma/eksik kontrolü)

```tcl
validate_bd_design       ;# BD Integrator diyaloğunun Tcl karşılığı
```

## Interrupt zincirini Tcl'den okuma

```tcl
# concat girişlerinin kaynağını bul:
foreach p [get_bd_pins irq_concat/In*] {
    set net [get_bd_nets -quiet -of $p]
    puts "$p <- [get_bd_pins -quiet -of $net -filter {DIR == O}]"
}
```

## .xsa export (GUI'siz)

```tcl
generate_target all [get_files sistem.bd]
write_hw_platform -fixed -force -file out.xsa
# bitstream'li istersen: -include_bit (implementasyon bitmiş olmalı)
```

:::saha-notu
En hızlı öğrenme yolu **journal**'dır: GUI'de bir işlem yap, çalıştığın
dizindeki `vivado.jou` dosyasını aç, işlemin Tcl karşılığını oku, kopyala.
Bu ekteki komutların çoğu böyle öğrenilebilir. `-quiet` bayrağı, sorgu
bulunamadığında hata yerine boş sonuç döndürür — scriptleri kırılgan olmaktan
kurtarır.
:::
