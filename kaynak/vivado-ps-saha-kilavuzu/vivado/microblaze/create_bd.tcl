# ============================================================
# create_bd.tcl — Demo 3: MicroBlaze soft-core sistemi (PL'de islemci)
#
# Hedef: KC705 (Kintex-7) board part'i; yoksa sirayla VC707 /
# AC701 / Nexys A7-100T'ye duser. PS'siz bir kartta islemcinin
# kendisi de PL'e sentezlenen bir IP'dir — bolumun ana dersi.
#
# Icerik:
#   - MicroBlaze + MDM (debug) + 64KB LMB local memory (BRAM)
#   - clk_wiz (kart saati -> 100 MHz) + proc_sys_reset
#   - AXI cevre birimleri: uartlite, iic, quad_spi, gpio(LED),
#     timer, bram_ctrl + blk_mem_gen (ek veri BRAM'i)
#   - axi_intc + concat: kesmeler MB'nin TEK interrupt girisine
#
# Kullanim:
#   vivado -mode batch -source vivado/microblaze/create_bd.tcl
#
# Cikti: vivado/work/demo_microblaze/demo_microblaze.xpr ("sistem" BD)
# ============================================================

set script_dizin [file dirname [file normalize [info script]]]
set work_dizin   [file normalize [file join $script_dizin .. work demo_microblaze]]

# ---- board secimi -------------------------------------------
# AC701 (Artix-7 xc7a200t) one alinir: WebPACK lisansi kapsar —
# implementasyon + bitstream + MMI uretimi lisanssiz makinede de kosar.
# (KC705/VC707 icin ayrica Vivado lisansi gerekir.)
set board ""
set board_adi ""
foreach {aday etiket} {*ac701* AC701 *nexys-a7-100t* NexysA7 *kc705* KC705 *vc707* VC707} {
    set bulunan [get_board_parts -quiet -latest_file_version $aday]
    if {[llength $bulunan]} {
        set board [lindex $bulunan 0]
        set board_adi $etiket
        break
    }
}
if {$board eq ""} {
    puts "HATA: uygun board part bulunamadi (kc705/vc707/ac701/nexys)."
    exit 1
}
set part [get_property PART_NAME $board]
puts "SECILEN BOARD: $board_adi ($board) — part: $part"

# ---- proje --------------------------------------------------
create_project -force demo_microblaze $work_dizin -part $part
set_property board_part $board [current_project]
set_property target_language Verilog [current_project]

create_bd_design "sistem"

proc vlnv_bul {ip_adi} {
    set defs [get_ipdefs -quiet "xilinx.com:ip:${ip_adi}:*"]
    if {![llength $defs]} { set defs [get_ipdefs -quiet -all "xilinx.com:ip:${ip_adi}:*"] }
    if {![llength $defs]} { error "IP bulunamadi: $ip_adi" }
    return [lindex [lsort $defs] end]
}

# ---- MicroBlaze + blok otomasyonu ---------------------------
# Otomasyon: MB + MDM + 64KB LMB BRAM + clk_wiz + proc_sys_reset
# + AXI interconnect + axi_intc kurar (GUI'deki Run Block Automation).
set mb [create_bd_cell -type ip -vlnv [vlnv_bul microblaze] microblaze_0]
apply_bd_automation -rule xilinx.com:bd_rule:microblaze -config { \
    axi_intc {1} axi_periph {Enabled} cache {None} \
    clk {New Clocking Wizard (100 MHz)} debug_module {Debug Only} \
    ecc {None} local_mem {64KB} preset {None} \
} $mb

puts "MB otomasyonu sonrasi hucreler:"
foreach c [get_bd_cells] { puts "  $c  ([get_property VLNV $c])" }

# Kart saatini clk_wiz'e bagla (KC705: 200 MHz diferansiyel sistem saati)
if {[catch {
    apply_board_connection -board_interface sys_diff_clock \
        -ip_intf clk_wiz_1/CLK_IN1_D -diagram "sistem"
    puts "KART: sys_diff_clock -> clk_wiz_1/CLK_IN1_D"
} h_clk]} { puts "clk kart baglanti notu: $h_clk" }

# clk_wiz reset girisini pasif tut (power-on reset yeterli; kart butonu
# bilerek baglanmadi — deterministik ve validate-temiz kurulum)
set sabit0 [create_bd_cell -type ip -vlnv [vlnv_bul xlconstant] sabit_sifir]
set_property -dict [list CONFIG.CONST_WIDTH {1} CONFIG.CONST_VAL {0}] $sabit0
if {[llength [get_bd_pins -quiet clk_wiz_1/reset]]} {
    connect_bd_net [get_bd_pins sabit_sifir/dout] [get_bd_pins clk_wiz_1/reset]
}
foreach rst_c [get_bd_cells -quiet -filter {VLNV =~ "*proc_sys_reset*"}] {
    set eri [get_bd_pins -quiet $rst_c/ext_reset_in]
    if {[llength $eri] && ![llength [get_bd_nets -quiet -of $eri]]} {
        connect_bd_net [get_bd_pins sabit_sifir/dout] $eri
    }
}

# ---- AXI cevre birimleri ------------------------------------
set uart  [create_bd_cell -type ip -vlnv [vlnv_bul axi_uartlite]  axi_uartlite_0]
set iic   [create_bd_cell -type ip -vlnv [vlnv_bul axi_iic]       axi_iic_0]
set spi   [create_bd_cell -type ip -vlnv [vlnv_bul axi_quad_spi]  axi_quad_spi_0]
set gpio  [create_bd_cell -type ip -vlnv [vlnv_bul axi_gpio]      axi_gpio_led]
set timer [create_bd_cell -type ip -vlnv [vlnv_bul axi_timer]     axi_timer_0]
set bramc [create_bd_cell -type ip -vlnv [vlnv_bul axi_bram_ctrl] axi_bram_ctrl_0]

set_property -dict [list CONFIG.C_BAUDRATE {115200} CONFIG.C_DATA_BITS {8}] $uart
set_property CONFIG.C_INTERRUPT_PRESENT {1} $gpio
set_property CONFIG.SINGLE_PORT_BRAM {1} $bramc

# AXI baglanti otomasyonu: her kole MB'nin Periph yoluna
foreach kole {axi_uartlite_0/S_AXI axi_iic_0/S_AXI axi_quad_spi_0/AXI_LITE \
              axi_gpio_led/S_AXI axi_timer_0/S_AXI axi_bram_ctrl_0/S_AXI} {
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config [list \
        Clk_master {Auto} Clk_slave {Auto} Clk_xbar {Auto} \
        Master {/microblaze_0 (Periph)} Slave "/$kole" \
        ddr_seg {Auto} intc_ip {Auto} master_apm {0} \
    ] [get_bd_intf_pins $kole]
}

# BRAM denetleyicisinin arkasina blok RAM
if {[catch {
    apply_bd_automation -rule xilinx.com:bd_rule:bram_cntlr \
        -config {BRAM "Auto"} [get_bd_intf_pins axi_bram_ctrl_0/BRAM_PORTA]
} sonuc]} {
    puts "BRAM otomasyonu olmadi ($sonuc); elle bagliyorum."
    set bram [create_bd_cell -type ip -vlnv [vlnv_bul blk_mem_gen] axi_bram]
    set_property CONFIG.Memory_Type {Single_Port_RAM} $bram
    connect_bd_intf_net [get_bd_intf_pins axi_bram_ctrl_0/BRAM_PORTA] \
                        [get_bd_intf_pins axi_bram/BRAM_PORTA]
}

# ---- board arayuzleri ---------------------------------------
proc kart_bagla {iface ip_intf} {
    if {[llength [get_board_part_interfaces -quiet $iface]]} {
        if {[catch {
            apply_board_connection -board_interface $iface -ip_intf $ip_intf -diagram "sistem"
            puts "KART: $iface -> $ip_intf"
        } h]} { puts "KART baglanti notu ($iface): $h" }
        return 1
    }
    return 0
}

if {![kart_bagla rs232_uart "axi_uartlite_0/UART"]} {
    make_bd_intf_pins_external [get_bd_intf_pins axi_uartlite_0/UART]
    puts "UART harici porta cikarildi."
}
if {![kart_bagla iic_main "axi_iic_0/IIC"]} {
    make_bd_intf_pins_external [get_bd_intf_pins axi_iic_0/IIC]
    puts "IIC harici porta cikarildi."
}
set led_ok 0
foreach aday {led_8bits led_4bits gpio_led} {
    if {[kart_bagla $aday "axi_gpio_led/GPIO"]} { set led_ok 1; break }
}
if {!$led_ok} {
    set_property -dict [list CONFIG.C_GPIO_WIDTH {8} CONFIG.C_ALL_OUTPUTS {1}] $gpio
    make_bd_intf_pins_external [get_bd_intf_pins axi_gpio_led/GPIO]
    puts "GPIO harici porta cikarildi."
}
set spi_ok 0
foreach aday {spi_flash qspi_flash} {
    if {[kart_bagla $aday "axi_quad_spi_0/SPI_0"]} { set spi_ok 1; break }
}
if {!$spi_ok} {
    make_bd_intf_pins_external [get_bd_intf_pins axi_quad_spi_0/SPI_0]
    puts "SPI harici porta cikarildi."
}

# ---- kesmeler: concat -> axi_intc -> MB'nin tek girisi ------
# MB otomasyonu axi_intc'yi kurup MB'ye baglar; kaynak demetini biz kurariz.
set intc [get_bd_cells -quiet microblaze_0_axi_intc]
if {![llength $intc]} { set intc [get_bd_cells -quiet -filter {VLNV =~ "*axi_intc*"}] }
set concat_irq [get_bd_cells -quiet microblaze_0_xlconcat]
if {![llength $concat_irq]} {
    set concat_irq [create_bd_cell -type ip -vlnv [vlnv_bul xlconcat] microblaze_0_xlconcat]
    connect_bd_net [get_bd_pins $concat_irq/dout] [get_bd_pins $intc/intr]
}
set_property CONFIG.NUM_PORTS {5} $concat_irq
connect_bd_net [get_bd_pins axi_timer_0/interrupt]      [get_bd_pins $concat_irq/In0]
connect_bd_net [get_bd_pins axi_uartlite_0/interrupt]   [get_bd_pins $concat_irq/In1]
connect_bd_net [get_bd_pins axi_iic_0/iic2intc_irpt]    [get_bd_pins $concat_irq/In2]
connect_bd_net [get_bd_pins axi_quad_spi_0/ip2intc_irpt] [get_bd_pins $concat_irq/In3]
connect_bd_net [get_bd_pins axi_gpio_led/ip2intc_irpt]  [get_bd_pins $concat_irq/In4]

# quad SPI cekirdek saati: AXI saatiyle ayni kaynaktan
set spi_clk [get_bd_pins -quiet axi_quad_spi_0/ext_spi_clk]
if {[llength $spi_clk] && ![llength [get_bd_nets -quiet -of $spi_clk]]} {
    set axi_clk_net [get_bd_nets -of [get_bd_pins axi_quad_spi_0/s_axi_aclk]]
    connect_bd_net -net $axi_clk_net $spi_clk
}

# ---- adresler + dogrulama -----------------------------------
assign_bd_address
validate_bd_design
regenerate_bd_layout
save_bd_design

make_wrapper -files [get_files sistem.bd] -top
add_files -norecurse [file join $work_dizin demo_microblaze.gen sources_1 bd sistem hdl sistem_wrapper.v]
update_compile_order -fileset sources_1

puts "TAMAM: demo_microblaze projesi kuruldu ($board_adi)."
puts "BD hucre sayisi: [llength [get_bd_cells]]"
close_project
