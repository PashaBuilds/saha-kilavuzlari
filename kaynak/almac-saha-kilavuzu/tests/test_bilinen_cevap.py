# -*- coding: utf-8 -*-
"""KICKOFF §10.4 bilinen-cevap kontrolleri — Python tarafı (gen_figures.py ile
aynı formüller). Çalıştır: python -m unittest discover -s tests"""
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = json.loads((ROOT / "data" / "scenario.json").read_text(encoding="utf-8"))
B = S["turetilmis_beklenen"]

def ktb_dbm_hz(T=290.0):
    return 10 * math.log10(1.380649e-23 * T * 1000)

def friis(bloklar):
    F, G = 0.0, 1.0
    for i, b in enumerate(bloklar):
        f, g = 10 ** (b["nf_db"] / 10), 10 ** (b["kazanc_db"] / 10)
        F = f if i == 0 else F + (f - 1) / G
        G *= g
    return 10 * math.log10(F)

class BilinenCevap(unittest.TestCase):
    def test_ktb(self):
        self.assertAlmostEqual(ktb_dbm_hz(), B["ktb_dbm_hz"], delta=0.05)

    def test_gurultu_tabani(self):
        v = ktb_dbm_hz() + 10 * math.log10(S["ddc"]["cikis_bant_mhz"] * 2 * 1e6) + S["on_uc"]["nf_toplam_db"]
        self.assertAlmostEqual(v, B["gurultu_tabani_dbm"], delta=0.05)

    def test_hassasiyet(self):
        v = B["gurultu_tabani_dbm"] + S["tespit"]["tespit_snr_db"]
        self.assertAlmostEqual(v, B["hassasiyet_dbm"], delta=0.05)

    def test_snr_14bit(self):
        self.assertAlmostEqual(6.02 * S["adc"]["bit"] + 1.76, B["snr_ideal_14bit_db"], delta=0.01)

    def test_jitter(self):
        v = -20 * math.log10(2 * math.pi * 1e9 * 100e-15)
        self.assertAlmostEqual(v, B["jitter_snr_1ghz_100fs_db"], delta=0.05)

    def test_alias(self):
        fs, f = S["adc"]["fs_hz"], S["on_uc"]["if_hz"]
        nyq = fs / 2
        bolge = int(f // nyq) + 1
        r = f % fs
        alias = fs - r if r > nyq else r
        self.assertEqual(bolge, S["adc"]["nyquist_bolgesi"])
        self.assertAlmostEqual(alias, S["adc"]["alias_hz"])
        self.assertEqual(bolge % 2 == 0, S["adc"]["spektrum_evrik"])

    def test_ftw(self):
        N = S["ddc"]["akumulator_bit"]
        ftw = round(S["ddc"]["nco_hz"] / S["adc"]["fs_hz"] * 2 ** N)
        self.assertEqual(ftw, S["ddc"]["ftw"])
        self.assertEqual("0x%08X" % ftw, B["ftw_hex"])
        self.assertAlmostEqual(S["adc"]["fs_hz"] / 2 ** N, B["nco_cozunurluk_hz"], delta=0.001)

    def test_islem_kazanci(self):
        v = 10 * math.log10((S["adc"]["fs_hz"] / 2) / (S["ddc"]["cikis_fs_msps"] * 1e6))
        self.assertAlmostEqual(v, B["islem_kazanci_1200_300_db"], delta=0.01)

    def test_fft_bin(self):
        self.assertAlmostEqual(S["ddc"]["cikis_fs_msps"] * 1e6 / S["fft"]["n"] / 1e3, B["fft_bin_khz"], delta=0.01)

    def test_rayleigh(self):
        self.assertAlmostEqual(math.sqrt(-2 * math.log(S["tespit"]["pfa"])), B["rayleigh_esik_sigma"], delta=0.002)

    def test_ca_cfar(self):
        N, pfa = S["tespit"]["n_ref"], S["tespit"]["pfa"]
        self.assertAlmostEqual(N * (pfa ** (-1 / N) - 1), B["ca_cfar_alfa"], delta=0.05)

    def test_friis_ornek(self):
        self.assertAlmostEqual(friis([{"kazanc_db": 20, "nf_db": 2}, {"kazanc_db": -7, "nf_db": 10}]), B["friis_ornek_db"], delta=0.03)

    def test_friis_senaryo(self):
        self.assertAlmostEqual(friis(S["on_uc"]["kaskad"]), S["on_uc"]["nf_friis_db"], delta=0.1)

    def test_ana_lob(self):
        self.assertAlmostEqual(2 / S["sinyal"]["pw_s"] / 1e6, B["ana_lob_null_null_mhz"], delta=0.01)

    def test_hann_enbw(self):
        N = 1024
        w = [0.5 - 0.5 * math.cos(2 * math.pi * k / N) for k in range(N)]
        enbw = N * sum(x * x for x in w) / sum(w) ** 2
        self.assertAlmostEqual(enbw, B["hann_enbw"], delta=0.01)

    def test_veri_hizlari(self):
        self.assertAlmostEqual(S["adc"]["fs_msps"] * S["adc"]["bit"] / 1000, S["adc"]["veri_hizi_gbps_14bit"], delta=0.01)
        self.assertAlmostEqual(S["ddc"]["cikis_fs_msps"] * 32 / 1000, S["ddc"]["cikis_veri_hizi_gbps"], delta=0.01)
        self.assertEqual(round(S["sinyal"]["pw_s"] * S["ddc"]["cikis_fs_msps"] * 1e6), S["ddc"]["darbe_ornek_sayisi"])

if __name__ == "__main__":
    unittest.main()
