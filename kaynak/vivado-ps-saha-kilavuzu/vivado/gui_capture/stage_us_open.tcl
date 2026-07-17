# stage_us_open.tcl — Demo 1 GUI oturumu acilisi
# Kullanim: vivado -mode tcl -source vivado/gui_capture/stage_us_open.tcl
# Proje + BD acilir, layout tazelenir, GUI baslar. KAYIT YAPILMAZ.
set repo [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
open_project [file join $repo vivado work demo_ultrascale demo_ultrascale.xpr]
open_bd_design [get_files sistem.bd]
regenerate_bd_layout
start_gui
puts "HAZIR: demo_ultrascale GUI acik. Kaydetme yok; cikista Don't Save."
