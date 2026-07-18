# ============================================================
# impl_bitstream.tcl — Demo 3'u sentez+implementasyon+bitstream'e
# kosturur ve MMI dosyasini uretir.
#
# NEDEN GEREKLI: write_mem_info (MMI), BRAM'lerin YERLESTIRILMIS
# konumlarini yazar — bu da implementasyon ister. MMI + updatemem,
# "yazilimi guncelle ama sentezi TEKRARLAMA" akisinin anahtaridir
# (Bolum 9'da anlatilir). Diger demo'larin aksine burada bitstream
# uretiyoruz; kucuk MB sistemi icin sure makuldur.
#
# Kullanim:
#   vivado -mode batch -source vivado/microblaze/impl_bitstream.tcl
#
# Ciktilar:
#   assets/reports/microblaze-sistem.mmi        (gercek MMI)
#   assets/reports/microblaze-utilization.txt   (MB kac LUT tutuyor?)
#   vivado/work/demo_microblaze/.../sistem_wrapper.bit
# ============================================================

set script_dizin [file dirname [file normalize [info script]]]
set repo         [file normalize [file join $script_dizin .. ..]]
set rapor_dizin  [file join $repo assets reports]

open_project [file join $repo vivado work demo_microblaze demo_microblaze.xpr]
update_compile_order -fileset sources_1

launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1

if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {
    puts "HATA: implementasyon tamamlanamadi: [get_property STATUS [get_runs impl_1]]"
    exit 1
}

open_run impl_1
write_mem_info -force [file join $rapor_dizin microblaze-sistem.mmi]
report_utilization -file [file join $rapor_dizin microblaze-utilization.txt]

puts "MMI      : $rapor_dizin/microblaze-sistem.mmi"
puts "Kullanim : $rapor_dizin/microblaze-utilization.txt"
puts "Bitstream: [get_property DIRECTORY [get_runs impl_1]]/sistem_wrapper.bit"
puts "IMPL TAMAM."
close_project
