# ============================================================
# create_bd.tcl — Demo 2: Versal CIPS + NoC + DDRMC ogretici dizayn
#
# Hedef: VPK120 board part'i; makinede yoksa VCK190'a duser
# (KICKOFF'un ongordugu yedek). Ders hedefleri:
#   1) DDR denetleyicisi artik NoC'un arkasinda (DDRMC)
#   2) PL IP'ye giden yol NoC'tan GECEBILIR (axi_timer NoC arkasinda)
#   3) PL IP'ye dogrudan yol da var (axi_gpio, CIPS M_AXI_FPD uzerinden)
#
# Kullanim:
#   vivado -mode batch -source vivado/versal/create_bd.tcl
#
# Cikti: vivado/work/demo_versal/demo_versal.xpr, BD adi "sistem"
# ============================================================

set script_dizin [file dirname [file normalize [info script]]]
set work_dizin   [file normalize [file join $script_dizin .. work demo_versal]]

# ---- board secimi: once VPK120, yoksa VCK190 ----------------
set board ""
set board_adi ""
foreach {aday etiket} {*vpk120* VPK120 *vck190:* VCK190} {
    set bulunan [get_board_parts -quiet -latest_file_version $aday]
    if {[llength $bulunan]} {
        set board [lindex $bulunan 0]
        set board_adi $etiket
        break
    }
}
if {$board eq ""} {
    puts "HATA: VPK120 veya VCK190 board part'i bulunamadi."
    exit 1
}
set part [get_property PART_NAME $board]
puts "SECILEN BOARD: $board_adi ($board) — part: $part"

# ---- proje --------------------------------------------------
create_project -force demo_versal $work_dizin -part $part
set_property board_part $board [current_project]
set_property target_language Verilog [current_project]

create_bd_design "sistem"

proc vlnv_bul {ip_adi} {
    set defs [get_ipdefs -quiet "xilinx.com:ip:${ip_adi}:*"]
    if {![llength $defs]} { set defs [get_ipdefs -quiet -all "xilinx.com:ip:${ip_adi}:*"] }
    if {![llength $defs]} { error "IP bulunamadi: $ip_adi" }
    return [lindex [lsort $defs] end]
}

# ---- CIPS + board preset + NoC/DDR otomasyonu ---------------
set cips [create_bd_cell -type ip -vlnv [vlnv_bul versal_cips] versal_cips_0]
apply_bd_automation -rule xilinx.com:bd_rule:cips -config { \
    board_preset {Yes} boot_config {Custom} configure_noc {Add new AXI NoC} \
    debug_config {JTAG} design_flow {Full System} mc_type {DDR} \
    num_mc_ddr {1} num_mc_lpddr {None} pl_clocks {1} pl_resets {1} \
} $cips

puts "CIPS otomasyonu sonrasi hucreler:"
foreach c [get_bd_cells] { puts "  $c  ([get_property VLNV $c])" }

# ---- PL cevre birimleri -------------------------------------
set gpio  [create_bd_cell -type ip -vlnv [vlnv_bul axi_gpio]  axi_gpio_led]
set timer [create_bd_cell -type ip -vlnv [vlnv_bul axi_timer] axi_timer_0]

# M_AXI_FPD'yi ac: board preset bunu kapali birakiyor. PS_PMC_CONFIG
# sozlugune anahtar eklemek mevcut preset degerlerini korur (merge).
if {![llength [get_bd_intf_pins -quiet versal_cips_0/M_AXI_FPD]]} {
    if {[catch {
        set_property -dict [list CONFIG.PS_PMC_CONFIG {PS_USE_M_AXI_FPD 1}] $cips
    } h_fpd]} { puts "PS_USE_M_AXI_FPD acilamadi: $h_fpd" }
}
set fpd_var [llength [get_bd_intf_pins -quiet versal_cips_0/M_AXI_FPD]]
puts "M_AXI_FPD mevcut: $fpd_var"

# GPIO: dogrudan yol — CIPS M_AXI_FPD, intc_ip Auto.
# M_AXI_FPD acilamadiysa GPIO da NoC uzerinden gider.
if {$fpd_var} {
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config [list \
        Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} \
        Master {/versal_cips_0/M_AXI_FPD} Slave {/axi_gpio_led/S_AXI} \
        ddr_seg {Auto} intc_ip {Auto} master_apm {0} \
    ] [get_bd_intf_pins axi_gpio_led/S_AXI]
} else {
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config [list \
        Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} \
        Master {/versal_cips_0/M_AXI_FPD} Slave {/axi_gpio_led/S_AXI} \
        ddr_seg {Auto} intc_ip {/axi_noc_0} master_apm {0} \
    ] [get_bd_intf_pins axi_gpio_led/S_AXI]
}

# Timer: NoC uzerinden yol — dersin can alici kismi.
# 2022.2 otomasyonu NSU'yu kendisi ekleyemiyor; elle kablolanir:
#   NoC'a M_AXI (NSU) portu ekle -> S00_AXI (FPD_CCI_NOC_0)
#   connectivity'sine M00_AXI'yi ekle -> NSU (AXI4) ile timer
#   (AXI4-Lite) arasina SmartConnect koy -> saat/reset bagla.
set timer_yolu "belirsiz"
if {[catch {
    set noc [get_bd_cells axi_noc_0]
    set eski_clk [get_property CONFIG.NUM_CLKS $noc]
    set_property -dict [list CONFIG.NUM_MI {1} \
        CONFIG.NUM_CLKS [expr {$eski_clk + 1}]] $noc
    set aclk_adi "aclk$eski_clk"
    set_property CONFIG.ASSOCIATED_BUSIF {M00_AXI} [get_bd_pins $noc/$aclk_adi]

    # FPD_CCI_NOC_0'in girdigi S00_AXI'ye M00_AXI rotasi ekle
    set s_pin [get_bd_intf_pins $noc/S00_AXI]
    set baglar [get_property CONFIG.CONNECTIONS $s_pin]
    lappend baglar M00_AXI {read_bw {100} write_bw {100} read_avg_burst {4} write_avg_burst {4}}
    set_property CONFIG.CONNECTIONS $baglar $s_pin

    # NSU (AXI4) -> SmartConnect -> timer (AXI4-Lite)
    set smc2 [create_bd_cell -type ip -vlnv [vlnv_bul smartconnect] smc_noc]
    set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $smc2
    connect_bd_intf_net [get_bd_intf_pins $noc/M00_AXI] [get_bd_intf_pins smc_noc/S00_AXI]
    connect_bd_intf_net [get_bd_intf_pins smc_noc/M00_AXI] [get_bd_intf_pins axi_timer_0/S_AXI]

    # saat: GPIO otomasyonunun kullandigi pl0_ref_clk netine katil
    set pl_clk_net [get_bd_nets -of [get_bd_pins versal_cips_0/pl0_ref_clk]]
    connect_bd_net -net $pl_clk_net [get_bd_pins $noc/$aclk_adi]
    connect_bd_net -net $pl_clk_net [get_bd_pins smc_noc/aclk]
    connect_bd_net -net $pl_clk_net [get_bd_pins axi_timer_0/s_axi_aclk]

    # reset: GPIO otomasyonunun kurdugu proc_sys_reset'ten
    set rst [lindex [get_bd_cells -filter {VLNV =~ "*proc_sys_reset*"}] 0]
    connect_bd_net [get_bd_pins $rst/peripheral_aresetn] [get_bd_pins smc_noc/aresetn]
    connect_bd_net [get_bd_pins $rst/peripheral_aresetn] [get_bd_pins axi_timer_0/s_axi_aresetn]
    set timer_yolu "noc-nsu-elle"
} hata]} {
    puts "NoC NSU kablolamasi olmadi: $hata"
    puts "Yedek: timer Auto ile baglaniyor (NoC dersi CIPS/NoC ekranlariyla verilir)."
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config [list \
        Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} \
        Master {/versal_cips_0/M_AXI_FPD} Slave {/axi_timer_0/S_AXI} \
        ddr_seg {Auto} intc_ip {Auto} master_apm {0} \
    ] [get_bd_intf_pins axi_timer_0/S_AXI]
    set timer_yolu "auto"
}
puts "TIMER YOLU: $timer_yolu"
puts "Otomasyon sonrasi hucreler ve baglantilar:"
foreach c [get_bd_cells] { puts "  $c  ([get_property VLNV $c])" }
foreach n [get_bd_intf_nets] { puts "  NET: $n" }

# ---- GPIO'yu karttaki LED'lere bagla ------------------------
set led_iface ""
foreach aday {gpio_led led_4bits led_8bits led_2bits} {
    if {[llength [get_board_part_interfaces -quiet $aday]]} { set led_iface $aday; break }
}
if {$led_iface ne ""} {
    apply_board_connection -board_interface $led_iface -ip_intf "axi_gpio_led/GPIO" -diagram "sistem"
    puts "GPIO -> $led_iface baglandi."
} else {
    puts "LED board interface bulunamadi; GPIO harici port olarak cikariliyor."
    set_property -dict [list CONFIG.C_GPIO_WIDTH {4} CONFIG.C_ALL_OUTPUTS {1}] $gpio
    make_bd_intf_pins_external [get_bd_intf_pins axi_gpio_led/GPIO]
}

# ---- interrupt: timer -> CIPS pl_ps_irq ---------------------
set irq_pin ""
foreach aday {pl_ps_irq0 pl_ps_irq} {
    set p [get_bd_pins -quiet versal_cips_0/$aday]
    if {[llength $p]} { set irq_pin $p; break }
}
if {$irq_pin eq ""} {
    # CIPS'te IRQ girisi acik degilse ac
    if {[catch {
        set_property -dict [list CONFIG.PS_PMC_CONFIG {PS_IRQ_USAGE {{CH0 1}}}] $cips
        set irq_pin [get_bd_pins -quiet versal_cips_0/pl_ps_irq0]
    } h]} { puts "IRQ pini acilamadi: $h" }
}
if {$irq_pin ne ""} {
    connect_bd_net [get_bd_pins axi_timer_0/interrupt] $irq_pin
    puts "Timer interrupt -> $irq_pin"
} else {
    puts "UYARI: CIPS IRQ pini bulunamadi; interrupt baglantisi yapilamadi."
}

# proc_sys_reset'in dis reset girisini CIPS pl0_resetn'e bagla
# (otomasyon bunu bos birakiyor; bosta kalirsa CRITICAL WARNING dogar)
foreach rst_c [get_bd_cells -quiet -filter {VLNV =~ "*proc_sys_reset*"}] {
    set eri [get_bd_pins -quiet $rst_c/ext_reset_in]
    if {[llength $eri] && ![llength [get_bd_nets -quiet -of $eri]]} {
        set plrst [get_bd_pins -quiet versal_cips_0/pl0_resetn]
        if {[llength $plrst]} { connect_bd_net $plrst $eri }
    }
}

# ---- adresler + dogrulama -----------------------------------
assign_bd_address
validate_bd_design
regenerate_bd_layout
save_bd_design

make_wrapper -files [get_files sistem.bd] -top
add_files -norecurse [file join $work_dizin demo_versal.gen sources_1 bd sistem hdl sistem_wrapper.v]
update_compile_order -fileset sources_1

puts "TAMAM: demo_versal projesi kuruldu ($board_adi). Timer yolu: $timer_yolu"
puts "BD hucre sayisi: [llength [get_bd_cells]]"
close_project
