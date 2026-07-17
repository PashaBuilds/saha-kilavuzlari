# stage_export_layout.tcl — GUI oturumunda BD layout SVG/PDF export'u
# (write_bd_layout batch modda calismaz; GUI Tcl konsolundan source edilir)
# Acik olan projenin BD'sini assets/bd-exports/ altina verir.
# Kullanim (GUI Tcl konsolu):
#   set ad ultrascale   ;# veya versal
#   source vivado/gui_capture/stage_export_layout.tcl
if {![info exists ad]} { set ad [file rootname [file tail [current_project]]] }
set repo [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
set hedef_svg [file join $repo assets bd-exports "$ad-bd-full.svg"]
set hedef_pdf [file join $repo assets bd-exports "$ad-bd-full.pdf"]
if {[catch { write_bd_layout -force -format svg -orientation landscape $hedef_svg } h1]} {
    puts "SVG olmadi: $h1"
} else { puts "SVG: $hedef_svg" }
if {[catch { write_bd_layout -force -format pdf -orientation landscape $hedef_pdf } h2]} {
    puts "PDF olmadi: $h2"
} else { puts "PDF: $hedef_pdf" }
