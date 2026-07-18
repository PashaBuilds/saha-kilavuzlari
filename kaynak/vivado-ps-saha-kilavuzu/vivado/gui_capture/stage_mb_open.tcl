# stage_mb_open.tcl — Demo 3 (MicroBlaze) GUI oturumu acilisi
# Kullanim: vivado -mode tcl -source vivado/gui_capture/stage_mb_open.tcl
set repo [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
open_project [file join $repo vivado work demo_microblaze demo_microblaze.xpr]
open_bd_design [get_files sistem.bd]
regenerate_bd_layout
start_gui
puts "HAZIR: demo_microblaze GUI acik. Kaydetme yok; cikista Don't Save."
