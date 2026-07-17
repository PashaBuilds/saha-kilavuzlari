# stage_versal_sec.tcl — Versal secim sahneleri
#   sec_cips_noc — CIPS<->NoC arasi arayuz netlerini secer (shot-28)
#   sec_cips     — versal_cips_0 hucresini secer (shot-22 oncesi)
#   sec_noc      — axi_noc_0 hucresini secer (shot-25 oncesi)
#   sec_temizle  — secimi kaldirir

proc sec_temizle {} { select_bd_objects -clear_selection }

proc sec_cips_noc {} {
    select_bd_objects -clear_selection
    set netler {}
    foreach n [get_bd_intf_nets] {
        set pinler [get_bd_intf_pins -quiet -of $n]
        set cips 0; set noc 0
        foreach p $pinler {
            if {[string match "/versal_cips_0/*" $p]} { set cips 1 }
            if {[string match "/axi_noc_0/*" $p]}     { set noc 1 }
        }
        if {$cips && $noc} { lappend netler $n }
    }
    if {[llength $netler]} {
        select_bd_objects $netler
        puts "SECILDI: [llength $netler] CIPS-NoC arayuz neti"
    } else {
        puts "UYARI: CIPS-NoC neti bulunamadi"
    }
}

proc sec_cips {} {
    select_bd_objects -clear_selection
    select_bd_objects [get_bd_cells versal_cips_0]
    puts "SECILDI: versal_cips_0"
}

proc sec_noc {} {
    select_bd_objects -clear_selection
    select_bd_objects [get_bd_cells axi_noc_0]
    puts "SECILDI: axi_noc_0"
}
puts "sec_* proc'lari yuklendi."
