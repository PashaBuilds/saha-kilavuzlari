# stage_relayout_us.tcl — ultrascale BD layout'unu secim temizlenmis
# halde yeniden export eder (tam otomatik; GUI acilir, export alinir, kapanir).
# Kullanim: vivado -mode tcl -source vivado/gui_capture/stage_relayout_us.tcl
set repo [file normalize [file join [file dirname [file normalize [info script]]] .. ..]]
set od [file join $repo assets bd-exports]
open_project [file join $repo vivado work demo_ultrascale demo_ultrascale.xpr]
open_bd_design [get_files sistem.bd]
regenerate_bd_layout
start_gui
# secim temizleme yalniz GUI baglaminda calisir
catch { select_bd_objects -clear_selection }
if {[catch {write_bd_layout -force -format svg -orientation landscape [file join $od ultrascale-bd-full.svg]} e]} {puts "SVGERR $e"} else {puts "SVGOK"}
if {[catch {write_bd_layout -force -format pdf -orientation landscape [file join $od ultrascale-bd-full.pdf]} e]} {puts "PDFERR $e"} else {puts "PDFOK"}
close_project
stop_gui
exit
