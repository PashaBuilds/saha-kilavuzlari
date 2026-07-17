# stage_versal_open.tcl — Demo 2 GUI oturumu acilisi
# Kullanim: vivado -mode tcl -source vivado/gui_capture/stage_versal_open.tcl
set repo [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
open_project [file join $repo vivado work demo_versal demo_versal.xpr]
open_bd_design [get_files sistem.bd]
regenerate_bd_layout
start_gui
puts "HAZIR: demo_versal GUI acik. Kaydetme yok; cikista Don't Save."
