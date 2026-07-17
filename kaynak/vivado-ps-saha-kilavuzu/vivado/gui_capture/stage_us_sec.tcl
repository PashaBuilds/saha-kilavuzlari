# stage_us_sec.tcl — secim sahneleri (GUI Tcl konsolundan source edilir)
# Kullanim: source .../stage_us_sec.tcl ; sonra asagidaki proc'lardan biri:
#   sec_irq    — interrupt zinciri netlerini secer (shot-05)
#   sec_gpio   — axi_gpio_led hucresini secer (shot-07)
#   sec_ps     — ps_ultra hucresini secer (shot-08 oncesi)
#   sec_temizle — secimi kaldirir

proc sec_temizle {} { select_bd_objects -clear_selection }

proc sec_irq {} {
    select_bd_objects -clear_selection
    select_bd_objects [get_bd_nets {irq_concat_dout axi_timer_0_interrupt axi_uartlite_dbg_interrupt axi_gpio_led_ip2intc_irpt}]
    puts "SECILDI: interrupt zinciri netleri"
}

proc sec_gpio {} {
    select_bd_objects -clear_selection
    select_bd_objects [get_bd_cells axi_gpio_led]
    puts "SECILDI: axi_gpio_led"
}

proc sec_ps {} {
    select_bd_objects -clear_selection
    select_bd_objects [get_bd_cells ps_ultra]
    puts "SECILDI: ps_ultra"
}
puts "sec_* proc'lari yuklendi."
