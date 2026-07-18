# ============================================================
# export_visuals.tcl — Katman A: gercek BD export'lari + raporlar
#
# Her iki demo projeyi acar, sunlari uretir:
#   assets/bd-exports/<ad>-bd-full.svg   (write_bd_layout)
#   assets/bd-exports/<ad>-bd-full.pdf   (SVG bozuksa yedek)
#   assets/reports/<ad>-hucreler.md      (IP envanteri: ad + VLNV)
#   assets/reports/<ad>-adres-haritasi.md (gercek adres haritasi)
#   assets/reports/<ad>-ps-config-full.txt (PS/CIPS tum CONFIG dokumu)
#   assets/reports/<ad>-ps-config-secme.md  (yazilim-ilgili secme ayarlar)
#   vivado/work/<proje>/<ad>.xsa         (pre-synthesis hardware export)
#   assets/reports/<ad>-validate.txt     (validate_design ciktisi)
#
# Kullanim:
#   vivado -mode batch -source vivado/export_visuals.tcl
#   vivado -mode batch -source vivado/export_visuals.tcl -tclargs ultrascale
# ============================================================

set script_dizin [file dirname [file normalize [info script]]]
set repo         [file normalize [file join $script_dizin ..]]
set bd_dizin     [file join $repo assets bd-exports]
set rapor_dizin  [file join $repo assets reports]
file mkdir $bd_dizin
file mkdir $rapor_dizin

# ---- yardimcilar --------------------------------------------
proc dosyaya {yol icerik} {
    set f [open $yol w]
    fconfigure $f -encoding utf-8
    puts $f $icerik
    close $f
    puts "  yazildi: $yol"
}

proc hucre_envanteri {} {
    set satirlar {"| Hucre | IP (VLNV) | Tur |" "|---|---|---|"}
    foreach c [lsort [get_bd_cells]] {
        set vlnv [get_property VLNV $c]
        set tip  [get_property TYPE $c]
        lappend satirlar "| `$c` | `$vlnv` | $tip |"
    }
    return [join $satirlar "\n"]
}

proc adres_haritasi {} {
    set satirlar {"| Master adres uzayi | Segment | Base | High | Aralik |" "|---|---|---|---|---|"}
    # NOT: -filter {EXCLUDED == 0} yeniden acilan dizaynda bos donebiliyor;
    # tum segmentleri alip OFFSET'i olanlari (haritalanmis olanlar) suzuyoruz.
    foreach seg [lsort [get_bd_addr_segs -quiet]] {
        if {![string match "*/SEG_*" $seg]} { continue }
        set ofs [get_property -quiet OFFSET $seg]
        set rng [get_property -quiet RANGE  $seg]
        if {$ofs eq "" || $rng eq ""} { continue }
        # 32 bit ustu adresler icin ll (wide) belirteci sart
        set yuksek [format 0x%08llX [expr {$ofs + $rng - 1}]]
        set ofs_hex [format 0x%08llX $ofs]
        # /ps_ultra/Data/SEG_axi_gpio_led_Reg -> uzay: /ps_ultra/Data, seg: SEG_...
        set parcalar [split $seg /]
        set segad [lindex $parcalar end]
        set uzay  [join [lrange $parcalar 0 end-1] /]
        # okunur aralik
        if {$rng >= 1073741824} { set rtxt "[expr {$rng/1073741824}]G"
        } elseif {$rng >= 1048576} { set rtxt "[expr {$rng/1048576}]M"
        } elseif {$rng >= 1024} { set rtxt "[expr {$rng/1024}]K"
        } else { set rtxt $rng }
        lappend satirlar "| `$uzay` | `$segad` | `$ofs_hex` | `$yuksek` | $rtxt |"
    }
    return [join $satirlar "\n"]
}

proc config_full {cell dosya} {
    set satirlar {}
    foreach p [lsort [list_property $cell]] {
        if {![string match "CONFIG.*" $p]} { continue }
        set deger [get_property $p $cell]
        lappend satirlar "$p = $deger"
    }
    dosyaya $dosya [join $satirlar "\n"]
}

proc secme_tablo {cell desenler} {
    set satirlar {"| Parametre | Deger |" "|---|---|"}
    set eklenen {}
    foreach desen $desenler {
        foreach p [lsort [list_property $cell]] {
            if {![string match "CONFIG.$desen" $p]} { continue }
            if {[lsearch -exact $eklenen $p] >= 0} { continue }
            lappend eklenen $p
            set deger [get_property $p $cell]
            if {$deger eq ""} { set deger "(bos)" }
            set kisa [string range $p 7 end]
            lappend satirlar "| `$kisa` | `$deger` |"
        }
    }
    return [join $satirlar "\n"]
}

# ---- tek proje isleme ---------------------------------------
# "rapor" argumani verilirse XSA/generate adimi atlanir (hizli tur).
proc proje_isle {ad xpr ps_hucre secme_desenler} {
    global bd_dizin rapor_dizin sadece_rapor
    puts "=== PROJE: $ad ==="
    open_project $xpr
    open_bd_design [get_files sistem.bd]

    # BD layout export: SVG dene, PDF'i her durumda yedek al
    # (batch modda calismaz — GUI oturumunda stage_export_layout.tcl kullan)
    set svg [file join $bd_dizin "$ad-bd-full.svg"]
    set pdf [file join $bd_dizin "$ad-bd-full.pdf"]
    if {[catch { write_bd_layout -force -format svg -orientation landscape $svg } h1]} {
        puts "SVG export hatasi: $h1"
    }
    if {[catch { write_bd_layout -force -format pdf -orientation landscape $pdf } h2]} {
        puts "PDF export hatasi: $h2"
    }

    dosyaya [file join $rapor_dizin "$ad-hucreler.md"] [hucre_envanteri]
    dosyaya [file join $rapor_dizin "$ad-adres-haritasi.md"] [adres_haritasi]

    set ps [get_bd_cells $ps_hucre]
    config_full $ps [file join $rapor_dizin "$ad-ps-config-full.txt"]
    dosyaya [file join $rapor_dizin "$ad-ps-config-secme.md"] \
        [secme_tablo $ps $secme_desenler]

    # MicroBlaze ise cevre birimlerinin config dokumunu ayrica yaz
    if {$ad eq "microblaze"} {
        set satirlar {}
        foreach {hucre desenler} {
            axi_uartlite_0  {C_BAUDRATE C_DATA_BITS C_USE_PARITY C_ODD_PARITY C_S_AXI_ACLK_FREQ_HZ*}
            axi_iic_0       {IIC_FREQ_KHZ C_IIC_FREQ* C_TEN_BIT_ADR C_GPO_WIDTH C_SDA_LEVEL C_SCL_INHIBIT*}
            axi_quad_spi_0  {C_SCK_RATIO C_NUM_SS_BITS C_NUM_TRANSFER_BITS C_SPI_MODE C_USE_STARTUP C_FIFO_DEPTH}
            axi_gpio_led    {C_GPIO_WIDTH C_ALL_OUTPUTS C_ALL_INPUTS C_IS_DUAL C_INTERRUPT_PRESENT}
            axi_timer_0     {COUNT_WIDTH ONE_TIMER_ONLY TRIG* GEN* C_COUNT_WIDTH C_ONE_TIMER_ONLY}
            axi_bram_ctrl_0 {SINGLE_PORT_BRAM DATA_WIDTH ECC_TYPE MEM_DEPTH*}
        } {
            set c [get_bd_cells -quiet $hucre]
            if {![llength $c]} { continue }
            lappend satirlar "" "### $hucre" "" "| Parametre | Deger |" "|---|---|"
            foreach desen $desenler {
                foreach p [lsort [list_property $c]] {
                    if {![string match "CONFIG.$desen" $p]} { continue }
                    set deger [get_property $p $c]
                    if {$deger eq ""} { set deger "(bos)" }
                    lappend satirlar "| `[string range $p 7 end]` | `$deger` |"
                }
            }
        }
        # intc ayrica (otomasyonun verdigi adla bul)
        set intc [get_bd_cells -quiet -filter {VLNV =~ "*axi_intc*"}]
        if {[llength $intc]} {
            lappend satirlar "" "### [lindex $intc 0] (axi_intc)" "" "| Parametre | Deger |" "|---|---|"
            foreach desen {C_IRQ_IS_LEVEL C_IRQ_ACTIVE C_HAS_FAST C_HAS_ILR C_NUM_INTR_INPUTS C_KIND_OF_INTR} {
                foreach p [lsort [list_property [lindex $intc 0]]] {
                    if {![string match "CONFIG.$desen" $p]} { continue }
                    lappend satirlar "| `[string range $p 7 end]` | `[get_property $p [lindex $intc 0]]` |"
                }
            }
        }
        dosyaya [file join $rapor_dizin "$ad-cevre-config.md"] [join $satirlar "\n"]
    }

    # CIPS ise PS_PMC_CONFIG sozlugunu ayrica coz
    if {$ad eq "versal"} {
        set cfg [get_property -quiet CONFIG.PS_PMC_CONFIG $ps]
        if {$cfg ne ""} {
            set satirlar {}
            foreach {k v} $cfg { lappend satirlar "$k = $v" }
            dosyaya [file join $rapor_dizin "$ad-ps-pmc-config.txt"] \
                [join [lsort $satirlar] "\n"]
        }
        # NoC ve DDRMC konfig dokumu
        set noc [get_bd_cells -quiet axi_noc_0]
        if {[llength $noc]} {
            config_full $noc [file join $rapor_dizin "$ad-noc-config-full.txt"]
        }
    }

    # validate ciktisi
    set vf [file join $rapor_dizin "$ad-validate.txt"]
    if {[catch { validate_bd_design } vh]} {
        dosyaya $vf "validate_bd_design HATA:\n$vh"
    } else {
        dosyaya $vf "validate_bd_design: HATASIZ (kritik uyari yok)\nTarih: [clock format [clock seconds]]"
    }

    # pre-synthesis XSA
    if {!$sadece_rapor && [catch {
        generate_target all [get_files sistem.bd]
        set xsa [file join [file dirname $xpr] "$ad-demo.xsa"]
        write_hw_platform -fixed -force -file $xsa
        puts "XSA: $xsa"
    } xh]} {
        puts "XSA export atlandi/hata: $xh"
    }

    close_project
}

# ---- kosum --------------------------------------------------
set hedefler $argv
set sadece_rapor 0
set idx [lsearch $hedefler rapor]
if {$idx >= 0} { set sadece_rapor 1; set hedefler [lreplace $hedefler $idx $idx] }
if {![llength $hedefler]} { set hedefler {ultrascale versal} }

set us_desenler {
    PSU__*__PERIPHERAL__ENABLE PSU__*__PERIPHERAL__IO
    PSU__PSS_REF_CLK__FREQMHZ
    PSU__CRL_APB__UART*_REF_CTRL__FREQMHZ PSU__CRL_APB__UART*_REF_CTRL__ACT_FREQMHZ
    PSU__CRL_APB__I2C*_REF_CTRL__ACT_FREQMHZ
    PSU__CRL_APB__SDIO*_REF_CTRL__ACT_FREQMHZ
    PSU__CRL_APB__QSPI_REF_CTRL__ACT_FREQMHZ
    PSU__CRL_APB__GEM*_REF_CTRL__ACT_FREQMHZ
    PSU__CRL_APB__USB*_REF_CTRL__ACT_FREQMHZ
    PSU__FPGA_PL*_ENABLE
    PSU__CRL_APB__PL*_REF_CTRL__FREQMHZ PSU__CRL_APB__PL*_REF_CTRL__ACT_FREQMHZ
    PSU__DDRC__MEMORY_TYPE PSU__DDRC__DRAM_WIDTH PSU__DDRC__BUS_WIDTH
    PSU__DDRC__SPEED_BIN PSU__DDRC__DEVICE_CAPACITY PSU__DDRC__ECC
    PSU__DDRC__CL PSU__DDRC__FREQ_MHZ
    PSU__USE__M_AXI_GP* PSU__USE__S_AXI_GP* PSU__MAXIGP*__DATA_WIDTH
    PSU__USE__IRQ* PSU__NUM_FABRIC_RESETS
}

set versal_desenler {
    PS_PMC_CONFIG_APPLIED CLOCK_MODE DDR_MEMORY_MODE DEBUG_MODE
    PS_BOARD_INTERFACE PMC_* PS_*
}

set mb_desenler {
    C_FREQ C_USE_MSR_INSTR C_USE_PCMP_INSTR C_USE_BARREL C_USE_HW_MUL
    C_USE_DIV C_USE_FPU C_USE_REORDER_INSTR
    C_USE_ICACHE C_USE_DCACHE C_CACHE_BYTE_SIZE C_DCACHE_BYTE_SIZE
    C_ICACHE_BASEADDR C_DCACHE_BASEADDR
    C_DEBUG_ENABLED C_NUMBER_OF_PC_BRK C_NUMBER_OF_RD_ADDR_BRK
    C_NUMBER_OF_WR_ADDR_BRK
    C_D_AXI C_I_AXI C_D_LMB C_I_LMB
    C_USE_MMU C_FAULT_TOLERANT C_PVR C_INTERCONNECT
}

foreach h $hedefler {
    if {$h eq "ultrascale"} {
        proje_isle ultrascale \
            [file join $repo vivado work demo_ultrascale demo_ultrascale.xpr] \
            ps_ultra $us_desenler
    } elseif {$h eq "versal"} {
        proje_isle versal \
            [file join $repo vivado work demo_versal demo_versal.xpr] \
            versal_cips_0 $versal_desenler
    } elseif {$h eq "microblaze"} {
        proje_isle microblaze \
            [file join $repo vivado work demo_microblaze demo_microblaze.xpr] \
            microblaze_0 $mb_desenler
    }
}
puts "EXPORT TAMAM."
