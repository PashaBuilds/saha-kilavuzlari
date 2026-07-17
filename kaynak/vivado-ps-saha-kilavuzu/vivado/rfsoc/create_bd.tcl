# ============================================================
# create_bd.tcl — Demo 1: UltraScale+ PS ogretici blok dizayni
#
# Hedef: ZCU111 (RFSoC) board part'i; makinede yoksa ZCU102'ye
# (MPSoC) duser. PS IP (zynq_ultra_ps_e) her iki ailede aynidir;
# kilavuz bunu Bolum 4'te acikca not eder.
#
# Kullanim:
#   vivado -mode batch -source vivado/rfsoc/create_bd.tcl
#
# Cikti: vivado/work/demo_ultrascale/demo_ultrascale.xpr
#        icinde "sistem" adli blok dizayn.
#
# Kural: proje GUI'de elle degistirilmez; tek kaynak bu scripttir.
# ============================================================

set script_dizin [file dirname [file normalize [info script]]]
set work_dizin   [file normalize [file join $script_dizin .. work demo_ultrascale]]

# ---- board secimi: once ZCU111, yoksa ZCU102 ----------------
set board ""
set board_adi ""
foreach {aday etiket} {*zcu111* ZCU111 *zcu102* ZCU102} {
    set bulunan [get_board_parts -quiet -latest_file_version $aday]
    if {[llength $bulunan]} {
        set board [lindex $bulunan 0]
        set board_adi $etiket
        break
    }
}
if {$board eq ""} {
    puts "HATA: ZCU111 veya ZCU102 board part'i bulunamadi."
    puts "Xilinx Board Store'dan board file kurulumu icin vivado/README.md'ye bakin."
    exit 1
}
set part [get_property PART_NAME $board]
puts "SECILEN BOARD: $board_adi ($board) — part: $part"

# ---- proje -------------------------------------------------
create_project -force demo_ultrascale $work_dizin -part $part
set_property board_part $board [current_project]
set_property target_language Verilog [current_project]

create_bd_design "sistem"

# ---- yardimci: ipdefs'ten tam vlnv bul ----------------------
proc vlnv_bul {ip_adi} {
    set defs [get_ipdefs -quiet "xilinx.com:ip:${ip_adi}:*"]
    if {![llength $defs]} { set defs [get_ipdefs -quiet -all "xilinx.com:ip:${ip_adi}:*"] }
    if {![llength $defs]} { error "IP bulunamadi: $ip_adi" }
    return [lindex [lsort $defs] end]
}

# ---- PS: zynq_ultra_ps_e + board preset ---------------------
set ps [create_bd_cell -type ip -vlnv [vlnv_bul zynq_ultra_ps_e] ps_ultra]
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset "1"} $ps

# Yazilim-ilgili PS ayarlarini netlestir:
#  - M_AXI_HPM0_FPD acik (PL cevre birimlerine giden ana master kapi)
#  - M_AXI_HPM1_FPD kapali (tek kapidan okunabilir ornek icin)
#  - pl_ps_irq0 acik (PL -> PS interrupt grubu)
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
    CONFIG.PSU__USE__M_AXI_GP1 {0} \
    CONFIG.PSU__USE__M_AXI_GP2 {0} \
    CONFIG.PSU__USE__IRQ0 {1} \
] $ps

# ---- PL cevre birimleri -------------------------------------
set gpio  [create_bd_cell -type ip -vlnv [vlnv_bul axi_gpio]      axi_gpio_led]
set timer [create_bd_cell -type ip -vlnv [vlnv_bul axi_timer]     axi_timer_0]
set uart  [create_bd_cell -type ip -vlnv [vlnv_bul axi_uartlite]  axi_uartlite_dbg]
set bramc [create_bd_cell -type ip -vlnv [vlnv_bul axi_bram_ctrl] axi_bram_ctrl_0]

# GPIO: interrupt uretebilsin (kesme yolculugu dersinde kullanilacak)
set_property CONFIG.C_INTERRUPT_PRESENT {1} $gpio
# UARTLITE: klasik debug konsol ayari
set_property -dict [list CONFIG.C_BAUDRATE {115200} CONFIG.C_DATA_BITS {8}] $uart
# BRAM denetleyici: tek port, okunabilir ornek
set_property CONFIG.SINGLE_PORT_BRAM {1} $bramc

# ---- AXI baglanti otomasyonu (GUI'deki Run Connection Automation) ----
foreach kole {axi_gpio_led/S_AXI axi_timer_0/S_AXI axi_uartlite_dbg/S_AXI axi_bram_ctrl_0/S_AXI} {
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config [list \
        Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} \
        Master {/ps_ultra/M_AXI_HPM0_FPD} Slave "/$kole" \
        ddr_seg {Auto} intc_ip {New AXI SmartConnect} master_apm {0} \
    ] [get_bd_intf_pins $kole]
}

# ---- BRAM: denetleyicinin arkasina blok RAM tak -------------
if {[catch {
    apply_bd_automation -rule xilinx.com:bd_rule:bram_cntlr \
        -config {BRAM "Auto"} [get_bd_intf_pins axi_bram_ctrl_0/BRAM_PORTA]
} sonuc]} {
    puts "BRAM otomasyonu olmadi ($sonuc); elle bagliyorum."
    set bram [create_bd_cell -type ip -vlnv [vlnv_bul blk_mem_gen] bram]
    set_property CONFIG.Memory_Type {Single_Port_RAM} $bram
    connect_bd_intf_net [get_bd_intf_pins axi_bram_ctrl_0/BRAM_PORTA] \
                        [get_bd_intf_pins bram/BRAM_PORTA]
}

# ---- GPIO'yu karttaki LED'lere bagla (board flow) -----------
set led_iface ""
foreach aday {led_8bits led_4bits} {
    if {[llength [get_board_part_interfaces -quiet $aday]]} { set led_iface $aday; break }
}
if {$led_iface ne ""} {
    apply_board_connection -board_interface $led_iface -ip_intf "axi_gpio_led/GPIO" -diagram "sistem"
    puts "GPIO -> $led_iface baglandi."
} else {
    puts "LED board interface bulunamadi; GPIO harici port olarak cikariliyor."
    set_property -dict [list CONFIG.C_GPIO_WIDTH {8} CONFIG.C_ALL_OUTPUTS {1}] $gpio
    make_bd_intf_pins_external [get_bd_intf_pins axi_gpio_led/GPIO]
}

# ---- UARTLITE'i PL pinlerine cikar --------------------------
make_bd_intf_pins_external [get_bd_intf_pins axi_uartlite_dbg/UART]
set uart_port [get_bd_intf_ports -quiet UART_0]
if {[llength $uart_port]} { set_property NAME uart_pl $uart_port }

# ---- interrupt zinciri: 3 kaynak -> concat -> pl_ps_irq0 ----
set concat_irq [create_bd_cell -type ip -vlnv [vlnv_bul xlconcat] irq_concat]
set_property CONFIG.NUM_PORTS {3} $concat_irq
connect_bd_net [get_bd_pins axi_timer_0/interrupt]      [get_bd_pins irq_concat/In0]
connect_bd_net [get_bd_pins axi_uartlite_dbg/interrupt] [get_bd_pins irq_concat/In1]
connect_bd_net [get_bd_pins axi_gpio_led/ip2intc_irpt]  [get_bd_pins irq_concat/In2]
connect_bd_net [get_bd_pins irq_concat/dout]            [get_bd_pins ps_ultra/pl_ps_irq0]

# ---- adresler + dogrulama -----------------------------------
assign_bd_address
validate_bd_design
regenerate_bd_layout
save_bd_design

# wrapper (xsa export'u icin gerekli ust modul)
make_wrapper -files [get_files sistem.bd] -top
add_files -norecurse [file join $work_dizin demo_ultrascale.gen sources_1 bd sistem hdl sistem_wrapper.v]
update_compile_order -fileset sources_1

puts "TAMAM: demo_ultrascale projesi kuruldu ($board_adi)."
puts "BD hucre sayisi: [llength [get_bd_cells]]"
close_project
