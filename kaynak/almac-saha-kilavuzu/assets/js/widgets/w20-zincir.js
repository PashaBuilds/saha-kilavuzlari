/* W-20 — Uçtan uca zincir oyun alanı (capstone)
   Senaryo → ön uç (Friis) → ADC (kuantizasyon + jitter) → DDC (NCO, filtre, ↓M) → tespit (CFAR) → FFT
   Her durakta mini zaman/frekans görünümü + canlı sinyal pasaportu + PDW çıktısı.
   Bir parametreyi değiştir, etkisinin zincir boyunca yayılmasını izle. */
WK.kaydet("w20", function (w) {
  var S = w.S, sn = S.sinyal || {}, ou = S.on_uc || {}, ad = S.adc || {}, dd = S.ddc || {}, ts = S.tespit || {}, ff = S.fft || {};
  var kaskadRef = (ou.kaskad || []).map(function (b) { return { ad: b.ad, kazanc_db: b.kazanc_db, nf_db: b.nf_db }; });

  var k1 = WK.grup(w, "Senaryo");
  WK.kaydirici(w, { ad: "seviye", etiket: "giriş seviyesi", min: -110, max: -20, adim: 1, deger: sn.seviye_dbm_giris || -60, birim: "dBm" });
  WK.kaydirici(w, { ad: "pw", etiket: "darbe genişliği", min: 0.1e-6, max: 5e-6, adim: 0.1e-6, deger: sn.pw_s || 1e-6, olcek: 1e-6, birim: "µs" });
  WK.kaydirici(w, { ad: "fofs", etiket: "RF ofseti (9.4 GHz'e göre)", min: -100e6, max: 100e6, adim: 1e6, deger: 0, olcek: 1e6, birim: "MHz" });
  WK.secim(w, { ad: "mop", etiket: "darbe içi modülasyon", secenekler: [["yok", "yok (sabit)"], ["lfm", "LFM 10 MHz"]], deger: "yok", metin: true });
  WK.onay(w, { ad: "ikinci", etiket: "ikinci emiter (+30 MHz, −20 dB)", deger: false });
  k1();
  var k2 = WK.grup(w, "Ön uç");
  WK.kaydirici(w, { ad: "nf", etiket: "sistem NF bütçesi", min: 2, max: 14, adim: 0.5, deger: ou.nf_toplam_db || 6, birim: "dB" });
  WK.kaydirici(w, { ad: "kazanc", etiket: "toplam kazanç", min: 20, max: 60, adim: 1, deger: ou.kazanc_toplam_db || 40, birim: "dB" });
  k2();
  var k3 = WK.grup(w, "ADC");
  WK.kaydirici(w, { ad: "bit", etiket: "çözünürlük", min: 8, max: 16, adim: 1, deger: ad.bit || 14, birim: "bit", tamsayi: true });
  WK.kaydirici(w, { ad: "jitter", etiket: "saat jitter'ı", min: 20e-15, max: 1000e-15, adim: 10e-15, deger: ad.jitter_s || 100e-15, olcek: 1e-15, birim: "fs" });
  k3();
  var k4 = WK.grup(w, "DDC");
  WK.kaydirici(w, { ad: "ncoOfs", etiket: "NCO ofseti (600 MHz'e göre)", min: -20e6, max: 20e6, adim: 0.5e6, deger: 0, olcek: 1e6, birim: "MHz" });
  WK.secim(w, { ad: "dec", etiket: "decimation", secenekler: [[4, "↓4 → 600 MSPS"], [8, "↓8 → 300 MSPS"], [16, "↓16 → 150 MSPS"]], deger: dd.decimation_toplam || 8 });
  k4();
  var k5 = WK.grup(w, "Tespit / FFT");
  WK.kaydirici(w, { ad: "pfaExp", etiket: "hedef Pfa = 10^−x", min: 3, max: 9, adim: 1, deger: 6, tamsayi: true, goster: function (v) { return "1e−" + v; } });
  WK.kaydirici(w, { ad: "nref", etiket: "CFAR N", min: 8, max: 32, adim: 8, deger: ts.n_ref || 16, tamsayi: true });
  WK.secim(w, { ad: "nfft", etiket: "FFT N", secenekler: [[256, "256"], [512, "512"], [1024, "1024"], [2048, "2048"]], deger: ff.n || 1024 });
  k5();

  var pZaman = WK.panel(w, 200), pSpek = WK.panel(w, 220), pPasaport = document.createElement("div");
  pPasaport.className = "w-pasaport-tablo";
  w.cizim.appendChild(pPasaport);

  var fsAdc = ad.fs_hz || 2400e6, ncoRef = dd.nco_hz || 600e6, lo = ou.lo_hz || 7.6e9, rfRef = sn.rf_hz || 9.4e9;

  function ciz() {
    var p = w.param;
    var fsOut = fsAdc / p.dec, bw = fsOut; // kompleks çıkış bandı = fs_out
    // --- seviyeler
    var tabanGiris = DSP.gurultuTabaniDbm(bw, p.nf);            // giriş referanslı, DDC bandında
    var snrGiris = p.seviye - tabanGiris;                       // tek darbe, işlem kazancı dahil (bant = DDC bandı)
    var adcFs = ad.tam_olcek_dbm || 4;
    var sinyalAdc = p.seviye + p.kazanc;                        // ADC girişinde dBm
    var dbfs = sinyalAdc - adcFs;
    var snrQ = DSP.snrKuantizasyon(p.bit) - DSP.islemKazanci(fsAdc, bw) * 0 ; // tam ölçek referanslı
    var fIn = fsAdc - (rfRef + p.fofs - lo);                     // IF → alias (evrik): 2400 − 1800 = 600
    var snrJ = DSP.snrJitter(rfRef + p.fofs - lo, p.jitter);     // jitter IF frekansında etkir
    var adcTabanDbfs = -DSP.snrBirlestir([DSP.snrKuantizasyon(p.bit), snrJ]);  // ADC gürültü tabanı (Nyquist bandında), dBFS
    var termalTabanDbfs = tabanGiris + p.kazanc - adcFs + DSP.islemKazanci(fsAdc, bw); // termal taban ADC'de, Nyquist bandına göre
    var adcTabanBantDbfs = adcTabanDbfs - DSP.islemKazanci(fsAdc, bw);     // DDC bandına indirgenmiş ADC tabanı
    var toplamTabanDbfs = DSP.db10(DSP.lin10(termalTabanDbfs - DSP.islemKazanci(fsAdc, bw)) + DSP.lin10(adcTabanBantDbfs));
    var snrCikis = dbfs - toplamTabanDbfs;
    var kirpma = dbfs > 0;
    // --- tespit
    var pfa = Math.pow(10, -p.pfaExp), alfa = DSP.caCfarAlfa(p.nref, pfa), esikSigma = DSP.rayleighEsik(pfa);
    var pd = DSP.pdSwerling0(snrCikis, pfa);
    var far = DSP.far(pfa, fsOut);
    var pwOrnek = p.pw * fsOut;
    // --- FFT
    var binHz = fsOut / p.nfft, gozlemS = p.nfft / fsOut, fftKazanc = DSP.fftIslemKazanci(p.nfft);
    var pencereKaybi = gozlemS > p.pw ? DSP.db10(p.pw / gozlemS) : 0;    // darbe pencereden kısa → SNR kaybı
    var snrFft = snrCikis + fftKazanc + pencereKaybi;
    // --- baseband konumu
    var fBb = -(p.fofs) - p.ncoOfs; // evrik: RF +Δ → alias −Δ; NCO ofseti düşer
    var rfGeri = lo + (fsAdc - (fBb + ncoRef + p.ncoOfs));
    // --- zaman domeni simülasyonu (kısa: 2048 örnek @ fs_out)
    var n = 2048, rnd = DSP.prng(5), gAmp = Math.pow(10, snrCikis / 20);
    var sig = DSP.darbeKompleks({ n: n, fs: fsOut, pw: p.pw, pri: 0, f0: fBb, genlik: gAmp, mop: p.mop === "lfm" ? "lfm" : "yok", chirpBw: 10e6, gecikme: 1.5e-6 });
    if (p.ikinci) { var s2 = DSP.darbeKompleks({ n: n, fs: fsOut, pw: p.pw * 1.7, pri: 0, f0: fBb + 30e6, genlik: gAmp * 0.1, gecikme: 3.2e-6 }); for (var k = 0; k < n; k++) { sig.i[k] += s2.i[k]; sig.q[k] += s2.q[k]; } }
    DSP.gurultuEkle(sig, 1, rnd);
    var guc = DSP.guc(sig.i, sig.q);
    // Uzun darbe (300 örnek) N=16'lık CA penceresini doldurup kendini maskeler (B23);
    // bu yüzden zincirde kapılı (darbe varken donan) gürültü kestirimi + α kullanılır.
    var kg = DSP.kapiliGurultuKestirimi(guc, alfa, 64);
    var cf = { esik: kg.esik };
    var pdw = DSP.darbeFsm(guc, cf.esik, { fs: fsOut, histerezisDb: 3, minPw: 4 });
    // --- çizim: zaman
    WK.temizle(pZaman);
    var gz = WK.grafik(pZaman, { W: 640, H: 200, xmin: 0, xmax: n / fsOut * 1e6, ymin: -10, ymax: Math.max(30, snrCikis + 12), kenar: { sol: 46, sag: 12, ust: 22, alt: 30 } });
    gz.eksenler({ xAd: "zaman (µs) — DDC çıkışı, " + WK.kisaSayi(fsOut) + "SPS", yAd: "güç (dB / σ²)", baslik: "Zaman kolu: güç zarfı (mavi), kapılı CFAR eşiği α·N̂ (altın), tespit (yeşil bant)", xAdet: 7, yAdet: 5 });
    var xs = [], ys = [], es = [], adim = Math.max(1, Math.floor(n / 800));
    for (k = 0; k < n; k += adim) { xs.push(k / fsOut * 1e6); ys.push(DSP.db10(guc[k])); es.push(DSP.db10(cf.esik[k])); }
    pdw.forEach(function (d) { gz.bant(d.toa_s * 1e6, (d.toa_s + d.pw_s) * 1e6, "w-dolgu-yesil"); });
    gz.cizgi(xs, ys, "w-cizgi-sinyal"); gz.cizgi(xs, es, "w-cizgi-altin");
    // --- çizim: spektrum
    WK.temizle(pSpek);
    var N = p.nfft, seg = sig.i.length >= N ? 0 : 0;
    var bas = Math.max(0, Math.round(1.5e-6 * fsOut) - Math.floor(N / 4));
    var si = sig.i.subarray(bas, bas + N), sq = sig.q.subarray(bas, bas + N);
    if (si.length < N) { si = sig.i.subarray(0, N); sq = sig.q.subarray(0, N); }
    var sp = DSP.spektrumDbfs(si, sq, "hann");
    var gs = WK.grafik(pSpek, { W: 640, H: 220, xmin: -fsOut / 2e6, xmax: fsOut / 2e6, ymin: -40, ymax: Math.max(20, snrCikis + 10), kenar: { sol: 46, sag: 12, ust: 22, alt: 30 } });
    gs.eksenler({ xAd: "baseband frekans (MHz) — bin " + WK.kisaSayi(binHz) + "Hz", yAd: "dB (σ² = 0 dB)", baslik: "Frekans kolu: darbeyi içeren " + N + " noktalık Hann FFT", xAdet: 6, yAdet: 5 });
    var fx = [], fy = [], ref = DSP.db10(1 / N) ; // gürültü σ²=1 → bin başına 1/N (ENBW hariç)
    for (k = 0; k < N; k++) { fx.push((k - N / 2) * fsOut / N / 1e6); fy.push(sp[k] - ref - DSP.db10(1.5)); }
    gs.alan(fx, fy, -40, "w-dolgu-sinyal"); gs.cizgi(fx, fy, "w-cizgi-sinyal");
    gs.yatay(0, "w-cizgi-gri", "gürültü tabanı (bin başına)");
    gs.dikey(fBb / 1e6, "w-cizgi-altin", "beklenen " + (fBb / 1e6).toFixed(1) + " MHz");
    // --- pasaport tablosu
    var d0 = pdw[0];
    var satir = function (durak, alan, frek, tip, fs, bit, hiz, snr) {
      return "<tr><td>" + durak + "</td><td>" + alan + "</td><td>" + frek + "</td><td>" + tip + "</td><td>" + fs + "</td><td>" + bit + "</td><td>" + hiz + "</td><td>" + snr + "</td></tr>";
    };
    var pasaport = '<div class="tablo-kap"><table><thead><tr><th>Durak</th><th>Alan</th><th>Frekans</th><th>Tip</th><th>fs</th><th>Bit</th><th>Veri hızı</th><th>SNR / seviye</th></tr></thead><tbody>' +
      satir("Anten", "analog RF", WK.fmtHz(rfRef + p.fofs), "reel", "—", "—", "—", p.seviye + " dBm") +
      satir("Ön uç çıkışı", "analog IF", WK.fmtHz(rfRef + p.fofs - lo), "reel", "—", "—", "—", sinyalAdc.toFixed(1) + " dBm · NF " + p.nf + " dB") +
      satir("ADC çıkışı", "sayısal", WK.fmtHz(fIn) + (fIn !== rfRef + p.fofs - lo ? " (evrik)" : ""), "reel", WK.kisaSayi(fsAdc) + "SPS", p.bit, (fsAdc * p.bit / 1e9).toFixed(1) + " Gbps", dbfs.toFixed(1) + " dBFS · ADC taban " + adcTabanDbfs.toFixed(1) + " dBFS") +
      satir("DDC çıkışı", "sayısal", "baseband " + (fBb / 1e6).toFixed(1) + " MHz", "kompleks I/Q", WK.kisaSayi(fsOut) + "SPS", "16+16", (fsOut * 32 / 1e9).toFixed(1) + " Gbps", (snrCikis >= 0 ? "+" : "") + snrCikis.toFixed(1) + " dB") +
      satir("Tespit", "sayısal", "—", "bayrak + güç", WK.kisaSayi(fsOut) + "SPS", "1 + 20", "—", "Pd " + (pd * 100).toFixed(0) + "% · Pfa 1e−" + p.pfaExp + " · " + WK.kisaSayi(far) + " FA/s") +
      satir("FFT", "sayısal", "bin " + WK.kisaSayi(binHz) + "Hz", "büyüklük", N + " nokta / " + (gozlemS * 1e6).toFixed(2) + " µs", "18", "—", "SNR_fft " + snrFft.toFixed(1) + " dB" + (pencereKaybi < 0 ? " (pencere kaybı " + pencereKaybi.toFixed(1) + " dB)" : "")) +
      satir("PDW", "yazılım", d0 ? WK.fmtHz(rfGeri) : "—", "128 bit", "darbe/s", "128", d0 ? "128 bit/darbe" : "—", d0 ? "TOA " + (d0.toa_s * 1e6).toFixed(3) + " µs · PW " + (d0.pw_s * 1e6).toFixed(3) + " µs · PA " + d0.pa_dbfs.toFixed(1) + " dB" : "tespit yok") +
      "</tbody></table></div>";
    pPasaport.innerHTML = pasaport;
    var sonuc = {};
    sonuc["gürültü tabanı (giriş, B=" + WK.kisaSayi(bw) + "Hz)"] = tabanGiris.toFixed(1) + " dBm";
    WK.sonucYaz(w, Object.assign(sonuc, {
      "hassasiyet (Pd≈0.9)": (tabanGiris + 13.2).toFixed(1) + " dBm",
      "ADC girişi": (kirpma ? "!" : "") + dbfs.toFixed(1) + " dBFS" + (kirpma ? " KIRPMA" : ""),
      "jitter SNR": snrJ.toFixed(1) + " dB",
      "çıkış SNR": (snrCikis < 13 ? "!" : "+") + snrCikis.toFixed(1) + " dB",
      "CFAR α": alfa.toFixed(2),
      "Pd": (pd < 0.9 ? "!" : "+") + (pd * 100).toFixed(1) + " %",
      "darbe/örnek": Math.round(pwOrnek) + " örnek",
      "PDW sayısı": String(pdw.length),
      "RF geri hesap": d0 ? WK.fmtHz(rfGeri) : "—"
    }));
  }
  return {
    ciz: ciz,
    presetler: [
      { ad: "Referans senaryo", param: { seviye: sn.seviye_dbm_giris || -60, pw: sn.pw_s || 1e-6, fofs: 0, mop: "yok", ikinci: false, nf: ou.nf_toplam_db || 6, kazanc: ou.kazanc_toplam_db || 40, bit: ad.bit || 14, jitter: ad.jitter_s || 100e-15, ncoOfs: 0, dec: 8, pfaExp: 6, nref: 16, nfft: 1024 } },
      { ad: "Zayıf darbe (−75 dBm)", param: { seviye: -75, pw: 1e-6, fofs: 0, mop: "yok", ikinci: false, nf: 6, kazanc: 40, bit: 14, jitter: 100e-15, ncoOfs: 0, dec: 8, pfaExp: 6, nref: 16, nfft: 1024 } },
      { ad: "Kısa darbe + uzun FFT", param: { seviye: -60, pw: 0.2e-6, fofs: 0, mop: "yok", ikinci: false, nf: 6, kazanc: 40, bit: 14, jitter: 100e-15, ncoOfs: 0, dec: 8, pfaExp: 6, nref: 16, nfft: 2048 } },
      { ad: "Kötü saat (800 fs)", param: { seviye: -40, pw: 1e-6, fofs: 0, mop: "yok", ikinci: false, nf: 6, kazanc: 40, bit: 14, jitter: 800e-15, ncoOfs: 0, dec: 8, pfaExp: 6, nref: 16, nfft: 1024 } },
      { ad: "Doyum (kazanç 58 dB)", param: { seviye: -40, pw: 1e-6, fofs: 0, mop: "yok", ikinci: false, nf: 6, kazanc: 58, bit: 14, jitter: 100e-15, ncoOfs: 0, dec: 8, pfaExp: 6, nref: 16, nfft: 1024 } },
      { ad: "İki emiter + LFM", param: { seviye: -55, pw: 1e-6, fofs: 5e6, mop: "lfm", ikinci: true, nf: 6, kazanc: 40, bit: 14, jitter: 100e-15, ncoOfs: 0, dec: 8, pfaExp: 6, nref: 16, nfft: 1024 } }
    ]
  };
});
