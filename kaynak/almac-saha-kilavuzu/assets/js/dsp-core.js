/* ============================================================================
   dsp-core.js — ortak DSP çekirdeği (saf JS, bağımlılıksız)
   Tüm widget'lar hesap mantığını buradan alır; widget kodu yalnızca çizer.
   Testler: tests/dsp-core.test.js (node --test). Tarayıcıda window.DSP,
   Node'da module.exports olarak yayımlanır.
   Birim disiplini: frekans Hz, zaman s, güç dBm/dBFS, genlik lineer (tam ölçek = 1).
   ========================================================================== */
(function (kok) {
  "use strict";
  var DSP = {};
  var PI = Math.PI, TAU = 2 * Math.PI;

  /* ------------------------------------------------------------- PRNG / gürültü */
  // Mulberry32: tohumlu, hızlı, deterministik.
  DSP.prng = function (seed) {
    var a = (seed >>> 0) || 0x9E3779B9;
    var r = function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      var t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
    r.seed = seed;
    return r;
  };
  // Box-Muller: ortalama 0, standart sapma sigma olan Gauss örnekleri.
  DSP.gauss = function (rnd, sigma) {
    sigma = sigma === undefined ? 1 : sigma;
    var u1 = rnd() || 1e-12, u2 = rnd();
    return sigma * Math.sqrt(-2 * Math.log(u1)) * Math.cos(TAU * u2);
  };
  // Kompleks beyaz Gauss gürültüsü: her bileşen sigma/√2 → toplam güç sigma².
  DSP.gaussKompleks = function (rnd, sigma) {
    var s = (sigma === undefined ? 1 : sigma) / Math.SQRT2;
    return [DSP.gauss(rnd, s), DSP.gauss(rnd, s)];
  };

  /* --------------------------------------------------------------- dB yardımcıları */
  DSP.db10 = function (x) { return 10 * Math.log10(Math.max(x, 1e-300)); };
  DSP.db20 = function (x) { return 20 * Math.log10(Math.max(x, 1e-300)); };
  DSP.lin10 = function (db) { return Math.pow(10, db / 10); };
  DSP.lin20 = function (db) { return Math.pow(10, db / 20); };
  DSP.dbmToW = function (dbm) { return Math.pow(10, (dbm - 30) / 10); };
  DSP.wToDbm = function (w) { return 10 * Math.log10(w) + 30; };
  DSP.dbmToVrms = function (dbm, R) { return Math.sqrt(DSP.dbmToW(dbm) * (R || 50)); };
  DSP.vrmsToDbm = function (v, R) { return DSP.wToDbm(v * v / (R || 50)); };
  DSP.vppToVrms = function (vpp) { return vpp / (2 * Math.SQRT2); };

  /* --------------------------------------------------------- gürültü / hassasiyet */
  // kTB (dBm/Hz): T = 290 K → −173.98 dBm/Hz
  DSP.KTB_DBM_HZ = 10 * Math.log10(1.380649e-23 * 290 * 1000);
  DSP.gurultuTabaniDbm = function (bwHz, nfDb) { return DSP.KTB_DBM_HZ + DSP.db10(bwHz) + (nfDb || 0); };
  DSP.hassasiyetDbm = function (bwHz, nfDb, snrDb) { return DSP.gurultuTabaniDbm(bwHz, nfDb) + snrDb; };
  // Friis kaskadı: bloklar [{kazanc_db, nf_db}] → {nf_db, kazanc_db, adimlar:[{nf_kum_db, kazanc_kum_db}]}
  DSP.friis = function (bloklar) {
    var F = 0, G = 1, adimlar = [];
    for (var i = 0; i < bloklar.length; i++) {
      var f = DSP.lin10(bloklar[i].nf_db), g = DSP.lin10(bloklar[i].kazanc_db);
      F = i === 0 ? f : F + (f - 1) / G;
      G *= g;
      adimlar.push({ nf_kum_db: DSP.db10(F), kazanc_kum_db: DSP.db10(G) });
    }
    return { nf_db: DSP.db10(F), kazanc_db: DSP.db10(G), adimlar: adimlar };
  };
  // Seviye diyagramı: giriş sinyali ve gürültü tabanı bloktan bloğa (dBm).
  DSP.seviyeDiyagrami = function (bloklar, sinyalDbm, bwHz) {
    var out = [{ ad: "giriş", sinyal: sinyalDbm, gurultu: DSP.gurultuTabaniDbm(bwHz, 0) }];
    var fr = DSP.friis(bloklar), s = sinyalDbm;
    for (var i = 0; i < bloklar.length; i++) {
      s += bloklar[i].kazanc_db;
      out.push({ ad: bloklar[i].ad, sinyal: s, gurultu: DSP.gurultuTabaniDbm(bwHz, 0) + fr.adimlar[i].nf_kum_db + fr.adimlar[i].kazanc_kum_db });
    }
    return out;
  };

  /* ------------------------------------------------------------------ ADC / SNR */
  DSP.snrKuantizasyon = function (bit) { return 6.02 * bit + 1.76; };
  DSP.snrJitter = function (finHz, sigmaS) { return -20 * Math.log10(TAU * finHz * sigmaS); };
  DSP.enob = function (sinadDb) { return (sinadDb - 1.76) / 6.02; };
  // Birden çok SNR bileşenini güç domeninde birleştirir.
  DSP.snrBirlestir = function (snrListeDb) {
    var p = 0;
    for (var i = 0; i < snrListeDb.length; i++) p += DSP.lin10(-snrListeDb[i]);
    return -DSP.db10(p);
  };
  DSP.islemKazanci = function (fsHz, bwHz) { return DSP.db10(fsHz / 2 / bwHz); };
  DSP.fftIslemKazanci = function (N) { return DSP.db10(N / 2); };
  DSP.nsd = function (snrDbfs, fsHz) { return -(snrDbfs + DSP.db10(fsHz / 2)); };

  /* ----------------------------------------------------------- Nyquist katlanma */
  // f (Hz), fs (Hz) → {bolge (1..), alias (0..fs/2), evrik}
  DSP.katla = function (fHz, fsHz) {
    var nyq = fsHz / 2;
    var bolge = Math.floor(fHz / nyq) + 1;
    var r = fHz % fsHz;
    var alias = r > nyq ? fsHz - r : r;
    return { bolge: bolge, alias: alias, evrik: bolge % 2 === 0 };
  };
  // Harmonik ve interleaving spur konumları (katlanmış, Hz)
  DSP.spurHaritasi = function (fHz, fsHz, M) {
    var out = [];
    for (var h = 2; h <= 5; h++) out.push({ ad: "HD" + h, f: DSP.katla(h * fHz, fsHz).alias, kaynak: "harmonik" });
    if (M && M > 1) {
      for (var k = 1; k < M; k++) {
        out.push({ ad: "k·fs/" + M + " (k=" + k + ")", f: DSP.katla(k * fsHz / M, fsHz).alias, kaynak: "offset" });
        out.push({ ad: "±f_in − k·fs/" + M, f: DSP.katla(Math.abs(k * fsHz / M - fHz), fsHz).alias, kaynak: "gain/timing" });
        out.push({ ad: "+f_in + k·fs/" + M, f: DSP.katla(k * fsHz / M + fHz, fsHz).alias, kaynak: "gain/timing" });
      }
    }
    return out;
  };

  /* ------------------------------------------------------------------- NCO / FTW */
  DSP.ftw = function (fHz, fsHz, N) {
    // 2^N büyük olabilir; 64-bit güvenli aralık dışına çıkmamak için N ≤ 48 kabul.
    var v = Math.round(fHz / fsHz * Math.pow(2, N));
    var mod = Math.pow(2, N);
    v = ((v % mod) + mod) % mod;
    return v;
  };
  DSP.ftwHex = function (v, N) {
    var hane = Math.ceil(N / 4);
    var s = v.toString(16).toUpperCase();
    while (s.length < hane) s = "0" + s;
    return "0x" + s;
  };
  DSP.ncoCozunurluk = function (fsHz, N) { return fsHz / Math.pow(2, N); };
  DSP.ncoGercekFrekans = function (ftw, fsHz, N) { return ftw / Math.pow(2, N) * fsHz; };
  // NCO modeli: faz akümülatörü (N bit), faz kırpma (P bit LUT adresi), genlik kuantizasyonu (A bit), dither.
  // Döndürür {i:[], q:[]} — kompleks çıkış, tam ölçek 1.
  DSP.nco = function (opts) {
    var n = opts.n, N = opts.N || 32, P = opts.P || 12, A = opts.A || 16, ftw = opts.ftw;
    var dither = !!opts.dither, rnd = opts.rnd || DSP.prng(7);
    var acc = 0, mod = Math.pow(2, N), lutBoy = Math.pow(2, P), q = Math.pow(2, A - 1);
    var i = new Float64Array(n), qq = new Float64Array(n);
    for (var k = 0; k < n; k++) {
      var fazAcc = acc;
      if (dither) fazAcc = (fazAcc + Math.floor(rnd() * Math.pow(2, N - P))) % mod;
      var adres = Math.floor(fazAcc / mod * lutBoy);         // faz kırpma
      var faz = adres / lutBoy * TAU;
      i[k] = Math.round(Math.cos(faz) * (q - 1)) / q;        // genlik kuantizasyonu
      qq[k] = Math.round(Math.sin(faz) * (q - 1)) / q;
      acc = (acc + ftw) % mod;
    }
    return { i: i, q: qq };
  };
  // Faz kırpma spur'u yaklaşık seviyesi (dBc): ≈ −6.02·P
  DSP.fazKirpmaSpurDbc = function (P) { return -6.02 * P; };

  /* --------------------------------------------------------------- sinyal üreteci */
  // Ortak: fs (Hz), n (örnek), her örnek için t = k/fs. Gerçek çıkış Float64Array.
  DSP.ton = function (n, fsHz, fHz, genlik, fazRad) {
    var x = new Float64Array(n);
    for (var k = 0; k < n; k++) x[k] = (genlik === undefined ? 1 : genlik) * Math.cos(TAU * fHz * k / fsHz + (fazRad || 0));
    return x;
  };
  DSP.tonKompleks = function (n, fsHz, fHz, genlik, fazRad) {
    var i = new Float64Array(n), q = new Float64Array(n), g = genlik === undefined ? 1 : genlik;
    for (var k = 0; k < n; k++) { var p = TAU * fHz * k / fsHz + (fazRad || 0); i[k] = g * Math.cos(p); q[k] = g * Math.sin(p); }
    return { i: i, q: q };
  };
  // Darbe zarfı: PW, PRI, rise/fall (kosinüs kenar). 0..1 arası.
  DSP.darbeZarfi = function (n, fsHz, pwS, priS, riseS, gecikmeS) {
    var z = new Float64Array(n), rise = riseS || 0, t0 = gecikmeS || 0;
    for (var k = 0; k < n; k++) {
      var t = k / fsHz - t0;
      if (t < 0) continue;
      var tt = priS > 0 ? t % priS : t;
      var v = 0;
      if (tt < pwS) {
        v = 1;
        if (rise > 0 && tt < rise) v = 0.5 - 0.5 * Math.cos(PI * tt / rise);
        else if (rise > 0 && tt > pwS - rise) v = 0.5 - 0.5 * Math.cos(PI * (pwS - tt) / rise);
      }
      z[k] = v;
    }
    return z;
  };
  // Darbe içi modülasyon: 'yok' | 'lfm' (chirpBwHz) | 'barker13' | 'barker7'
  var BARKER = { barker7: [1, 1, 1, -1, -1, 1, -1], barker13: [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1] };
  DSP.darbeKompleks = function (opts) {
    var n = opts.n, fs = opts.fs, pw = opts.pw, pri = opts.pri || 0, f0 = opts.f0 || 0, g = opts.genlik === undefined ? 1 : opts.genlik;
    var mop = opts.mop || "yok", bw = opts.chirpBw || 0, rise = opts.rise || 0, t0 = opts.gecikme || 0;
    var zarf = DSP.darbeZarfi(n, fs, pw, pri, rise, t0);
    var i = new Float64Array(n), q = new Float64Array(n);
    for (var k = 0; k < n; k++) {
      if (zarf[k] === 0) continue;
      var t = k / fs - t0, tt = pri > 0 ? t % pri : t;
      var faz = TAU * f0 * (k / fs);
      if (mop === "lfm") faz += PI * (bw / pw) * (tt - pw / 2) * (tt - pw / 2) - PI * bw / pw * (pw / 2) * (pw / 2); // merkezde f0, ±bw/2 süpürme
      else if (BARKER[mop]) { var kod = BARKER[mop]; var cip = Math.min(kod.length - 1, Math.floor(tt / pw * kod.length)); if (kod[cip] < 0) faz += PI; }
      i[k] = g * zarf[k] * Math.cos(faz); q[k] = g * zarf[k] * Math.sin(faz);
    }
    return { i: i, q: q, zarf: zarf };
  };
  // Gerçek (reel) darbe: taşıyıcı f0 ile
  DSP.darbeReel = function (opts) {
    var c = DSP.darbeKompleks(opts);
    return c.i; // cos bileşeni = reel darbe
  };
  // Kompleks diziye gürültü ekle (yerinde). sigma = toplam gürültü rms.
  DSP.gurultuEkle = function (sig, sigma, rnd) {
    rnd = rnd || DSP.prng(11);
    for (var k = 0; k < sig.i.length; k++) { var g = DSP.gaussKompleks(rnd, sigma); sig.i[k] += g[0]; sig.q[k] += g[1]; }
    return sig;
  };
  DSP.gurultuEkleReel = function (x, sigma, rnd) {
    rnd = rnd || DSP.prng(11);
    for (var k = 0; k < x.length; k++) x[k] += DSP.gauss(rnd, sigma);
    return x;
  };
  // Anlık frekans (Hz): faz farkından. Çıkış n-1 uzunlukta.
  DSP.anlikFrekans = function (i, q, fs) {
    var out = new Float64Array(i.length);
    for (var k = 1; k < i.length; k++) {
      var d = Math.atan2(q[k] * i[k - 1] - i[k] * q[k - 1], i[k] * i[k - 1] + q[k] * q[k - 1]);
      out[k] = d / TAU * fs;
    }
    out[0] = out[1] || 0;
    return out;
  };

  /* ------------------------------------------------------------------ kuantizör */
  // x ∈ [-1,1) → N-bit (mid-tread, yuvarlama), clipping; dither: ±1/2 LSB tekdüze.
  DSP.kuantize = function (x, bit, opts) {
    opts = opts || {};
    var q = Math.pow(2, bit - 1), lsb = 1 / q, rnd = opts.rnd || DSP.prng(3);
    var y = new Float64Array(x.length), tasma = 0;
    var mod = opts.mod || "round"; // round | trunc
    for (var k = 0; k < x.length; k++) {
      var v = x[k];
      if (opts.dither) v += (rnd() - 0.5) * lsb;
      var c = mod === "trunc" ? Math.floor(v * q) : Math.round(v * q);
      if (c > q - 1) { c = q - 1; tasma++; }
      if (c < -q) { c = -q; tasma++; }
      y[k] = c / q;
    }
    y.tasma = tasma;
    return y;
  };
  // Sabit nokta yeniden nicemleme: kelimeyi (bit) bit'e indir; mod: round|trunc; tasma: sat|wrap.
  DSP.sabitNokta = function (x, bit, mod, tasma) {
    var q = Math.pow(2, bit - 1), y = new Float64Array(x.length), say = 0;
    for (var k = 0; k < x.length; k++) {
      var c = mod === "trunc" ? Math.floor(x[k] * q) : Math.round(x[k] * q);
      if (c > q - 1 || c < -q) {
        say++;
        if (tasma === "wrap") { c = ((c + q) % (2 * q) + 2 * q) % (2 * q) - q; }
        else c = Math.max(-q, Math.min(q - 1, c));
      }
      y[k] = c / q;
    }
    y.tasma = say;
    return y;
  };
  // Jitter'lı örnekleme: ideal ton yerine t_k = k/fs + j_k anında örnekle.
  DSP.tonJitterli = function (n, fs, f, sigmaS, rnd) {
    rnd = rnd || DSP.prng(5);
    var x = new Float64Array(n);
    for (var k = 0; k < n; k++) x[k] = Math.cos(TAU * f * (k / fs + DSP.gauss(rnd, sigmaS)));
    return x;
  };

  /* ------------------------------------------------------------------- pencereler */
  // simetrik=true → kosinüs pencerelerinde payda N−1 (FIR katsayı tasarımı); varsayılan periyodik (spektral analiz).
  DSP.pencere = function (tip, N, beta, simetrik) {
    var w = new Float64Array(N), k, D = simetrik ? (N - 1) : N;
    var a = { "blackman-harris": [0.35875, 0.48829, 0.14128, 0.01168], "flat-top": [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368] };
    switch (tip) {
      case "rect": for (k = 0; k < N; k++) w[k] = 1; break;
      case "hann": for (k = 0; k < N; k++) w[k] = 0.5 - 0.5 * Math.cos(TAU * k / D); break;
      case "hamming": for (k = 0; k < N; k++) w[k] = 0.54 - 0.46 * Math.cos(TAU * k / D); break;
      case "blackman": for (k = 0; k < N; k++) w[k] = 0.42 - 0.5 * Math.cos(TAU * k / D) + 0.08 * Math.cos(2 * TAU * k / D); break;
      case "blackman-harris": case "flat-top":
        for (k = 0; k < N; k++) { var s = 0; for (var m = 0; m < a[tip].length; m++) s += (m % 2 ? -1 : 1) * a[tip][m] * Math.cos(m * TAU * k / D); w[k] = s; } break;
      case "kaiser": {
        var b = beta === undefined ? 8 : beta, i0b = DSP._i0(b);
        for (k = 0; k < N; k++) { var r = 2 * k / (N - 1) - 1; w[k] = DSP._i0(b * Math.sqrt(Math.max(0, 1 - r * r))) / i0b; }
        break;
      }
      case "chebyshev": {
        // Dolph-Chebyshev, yan lob = -beta dB (varsayılan 80). Frekans domeninde tanım → IDFT.
        var at = beta === undefined ? 80 : beta;
        var r10 = Math.pow(10, at / 20), x0 = Math.cosh(Math.acosh(r10) / (N - 1));
        var W = new Float64Array(N);
        for (k = 0; k < N; k++) {
          var xk = x0 * Math.cos(PI * k / N);
          var ch = Math.abs(xk) <= 1 ? Math.cos((N - 1) * Math.acos(xk)) : Math.cosh((N - 1) * Math.acosh(Math.abs(xk))) * (xk < 0 && (N - 1) % 2 ? -1 : 1);
          W[k] = ch / r10;
        }
        // reel IDFT (simetrik)
        for (var nn = 0; nn < N; nn++) { var s2 = 0; for (k = 0; k < N; k++) s2 += W[k] * Math.cos(TAU * k * (nn - (N - 1) / 2) / N); w[nn] = s2; }
        var mx = 0; for (k = 0; k < N; k++) mx = Math.max(mx, Math.abs(w[k]));
        for (k = 0; k < N; k++) w[k] = Math.abs(w[k]) / mx;
        break;
      }
      default: for (k = 0; k < N; k++) w[k] = 1;
    }
    return w;
  };
  DSP._i0 = function (x) { var s = 1, t = 1, k = 1; do { t *= (x / (2 * k)) * (x / (2 * k)); s += t; k++; } while (t > 1e-12 * s && k < 200); return s; };
  // Pencere metrikleri: coherent gain (CG), ENBW (bin), scalloping loss (dB), en yüksek yan lob (dB), ana lob −3 dB genişliği (bin)
  DSP.pencereMetrik = function (w) {
    var N = w.length, s1 = 0, s2 = 0, k;
    for (k = 0; k < N; k++) { s1 += w[k]; s2 += w[k] * w[k]; }
    var cg = s1 / N, enbw = N * s2 / (s1 * s1);
    // scalloping: yarım bin kaymış tonun kaybı
    var re = 0, im = 0;
    for (k = 0; k < N; k++) { re += w[k] * Math.cos(PI * k / N); im += w[k] * Math.sin(PI * k / N); }
    var scallop = -DSP.db20(Math.sqrt(re * re + im * im) / s1);
    // yan lob: yüksek çözünürlüklü DTFT ile (zero-pad 16x)
    var L = 16, M = N * L, maks = -300, buldukDip = false, ilkDip = 0, b3 = 0;
    var onceki = 0;
    for (var m = 0; m < M / 2; m++) {
      var rr = 0, ii = 0, wf = TAU * m / M;
      for (k = 0; k < N; k++) { rr += w[k] * Math.cos(wf * k); ii -= w[k] * Math.sin(wf * k); }
      var mag = DSP.db20(Math.sqrt(rr * rr + ii * ii) / s1);
      if (!b3 && mag < -3) b3 = 2 * m / L;
      // yan lob araması ana lobun −6 dB altına indikten sonra başlar (flat-top ana lob dalgası yan lob sayılmasın)
      if (!buldukDip) { if (m > 0 && mag > onceki && onceki < -6) { buldukDip = true; ilkDip = m; } }
      if (buldukDip && mag > maks) maks = mag;
      onceki = mag;
      if (m > 12 * L && buldukDip) break;
    }
    return { cg: cg, enbw: enbw, scallop: scallop, yanLobDb: maks, anaLob3dbBin: b3 };
  };

  /* --------------------------------------------------------------------- FFT */
  // Yerinde radix-2 kompleks FFT (re, im Float64Array, uzunluk 2^k). ters=true → IFFT (1/N ölçekli)
  DSP.fft = function (re, im, ters) {
    var n = re.length, i, j, k, m;
    if ((n & (n - 1)) !== 0) throw new Error("FFT: N 2'nin kuvveti olmalı");
    for (i = 1, j = 0; i < n; i++) {
      var bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) { var t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; }
    }
    for (var len = 2; len <= n; len <<= 1) {
      var ang = TAU / len * (ters ? 1 : -1), wr = Math.cos(ang), wi = Math.sin(ang);
      for (i = 0; i < n; i += len) {
        var cr = 1, ci = 0;
        for (j = 0; j < len / 2; j++) {
          var ur = re[i + j], ui = im[i + j];
          var vr = re[i + j + len / 2] * cr - im[i + j + len / 2] * ci;
          var vi = re[i + j + len / 2] * ci + im[i + j + len / 2] * cr;
          re[i + j] = ur + vr; im[i + j] = ui + vi;
          re[i + j + len / 2] = ur - vr; im[i + j + len / 2] = ui - vi;
          var ncr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = ncr;
        }
      }
    }
    if (ters) for (k = 0; k < n; k++) { re[k] /= n; im[k] /= n; }
  };
  // Güç spektrumu (dBFS, tam ölçek sinüs = 0 dBFS). Kompleks giriş; pencere uygulanır, CG ile telafi edilir.
  // Dönüş: Float64Array N (fftshift uygulanmış: −fs/2 … +fs/2). opts.shift=false → 0…fs
  DSP.spektrumDbfs = function (i, q, pencereTip, opts) {
    opts = opts || {};
    var N = i.length, w = DSP.pencere(pencereTip || "rect", N, opts.beta), s1 = 0, k;
    for (k = 0; k < N; k++) s1 += w[k];
    var re = new Float64Array(N), im = new Float64Array(N);
    for (k = 0; k < N; k++) { re[k] = i[k] * w[k]; im[k] = (q ? q[k] : 0) * w[k]; }
    DSP.fft(re, im, false);
    var out = new Float64Array(N);
    var olcek = opts.reel ? 2 / s1 : 1 / s1; // reel sinyalde tek taraflı: ×2
    for (k = 0; k < N; k++) {
      var m = Math.sqrt(re[k] * re[k] + im[k] * im[k]) * olcek;
      var idx = opts.shift === false ? k : (k + N / 2) % N;
      out[idx] = DSP.db20(m);
    }
    return out;
  };
  // Welch ortalaması: kompleks dizi üzerinde segment ortalaması (güç domeninde)
  DSP.spektrumOrtalama = function (i, q, N, pencereTip, segSayi, overlap) {
    var adim = Math.max(1, Math.floor(N * (1 - (overlap || 0))));
    var acc = new Float64Array(N), say = 0;
    for (var s = 0; s + N <= i.length && say < segSayi; s += adim) {
      var sp = DSP.spektrumDbfs(i.subarray(s, s + N), q ? q.subarray(s, s + N) : null, pencereTip);
      for (var k = 0; k < N; k++) acc[k] += DSP.lin10(sp[k]);
      say++;
    }
    for (var k2 = 0; k2 < N; k2++) acc[k2] = DSP.db10(acc[k2] / Math.max(1, say));
    return acc;
  };
  // Spektrum metrikleri: temel ton bin'i çevresinde sinyal gücü; kalan → gürültü+bozulma; SFDR, SNR, SINAD, ENOB.
  DSP.spektrumMetrik = function (spDbfs, opts) {
    opts = opts || {};
    var N = spDbfs.length, k, pk = 0;
    for (k = 1; k < N; k++) if (spDbfs[k] > spDbfs[pk]) pk = k;
    var koruma = opts.koruma || 3, harmonikler = opts.harmonikBin || [];
    var ps = 0, pn = 0, pd = 0, enKotu = -300, enKotuBin = -1;
    for (k = 0; k < N; k++) {
      var p = DSP.lin10(spDbfs[k]);
      if (Math.abs(k - pk) <= koruma) { ps += p; continue; }
      if (opts.dcAtla && Math.abs(k - N / 2) <= 1) continue;
      var harm = false;
      for (var h = 0; h < harmonikler.length; h++) if (Math.abs(k - harmonikler[h]) <= 1) harm = true;
      if (harm) pd += p; else pn += p;
      if (spDbfs[k] > enKotu) { enKotu = spDbfs[k]; enKotuBin = k; }
    }
    var snr = DSP.db10(ps / Math.max(pn, 1e-300)), sinad = DSP.db10(ps / Math.max(pn + pd, 1e-300));
    return { tepeBin: pk, tepeDbfs: spDbfs[pk], snr: snr, sinad: sinad, enob: DSP.enob(sinad), sfdr: spDbfs[pk] - enKotu, spurBin: enKotuBin, spurDbfs: enKotu,
             gurultuTabaniDbfs: DSP.db10(pn / Math.max(1, N - 2 * koruma - 1)) };
  };
  // Parabolik tepe interpolasyonu: (y-1, y0, y+1) dB → kesirli bin ofseti
  DSP.tepeInterpole = function (ym, y0, yp) { var d = ym - 2 * y0 + yp; return d === 0 ? 0 : 0.5 * (ym - yp) / d; };

  /* ---------------------------------------------------------------- FIR / CIC */
  // Pencereli sinc alçak geçiren: fc (Hz), fs, tap sayısı (tek), pencere tipi
  DSP.firTasarla = function (fcHz, fsHz, tap, pencereTip, beta) {
    var h = new Float64Array(tap), w = DSP.pencere(pencereTip || "hamming", tap, beta, true), m = (tap - 1) / 2, s = 0, k;
    var fc = fcHz / fsHz;
    for (k = 0; k < tap; k++) { var x = k - m; h[k] = (x === 0 ? 2 * fc : Math.sin(TAU * fc * x) / (PI * x)) * w[k]; s += h[k]; }
    for (k = 0; k < tap; k++) h[k] /= s;
    return h;
  };
  // Halfband: fc = fs/4, tek tap'ler sıfır, merkez 0.5
  DSP.halfband = function (tap, pencereTip) {
    var h = DSP.firTasarla(0.25, 1, tap, pencereTip || "kaiser", 6), m = (tap - 1) / 2;
    for (var k = 0; k < tap; k++) if (k !== m && (k - m) % 2 === 0) h[k] = 0;
    var s = 0; for (k = 0; k < tap; k++) s += h[k];
    for (k = 0; k < tap; k++) h[k] /= s;
    return h;
  };
  // Katsayı kuantizasyonu
  DSP.katsayiKuantize = function (h, bit) {
    var mx = 0, k; for (k = 0; k < h.length; k++) mx = Math.max(mx, Math.abs(h[k]));
    var q = Math.pow(2, bit - 1) - 1, out = new Float64Array(h.length);
    for (k = 0; k < h.length; k++) out[k] = Math.round(h[k] / mx * q) / q * mx;
    return out;
  };
  // Frekans yanıtı (dB), M nokta, 0..fs/2 (reel katsayı)
  DSP.firYanit = function (h, M) {
    var out = new Float64Array(M);
    for (var m = 0; m < M; m++) {
      var wf = PI * m / M, re = 0, im = 0;
      for (var k = 0; k < h.length; k++) { re += h[k] * Math.cos(wf * k); im -= h[k] * Math.sin(wf * k); }
      out[m] = DSP.db20(Math.sqrt(re * re + im * im));
    }
    return out;
  };
  // Konvolüsyon (reel h, kompleks/reel x). Gecikme telafisi yapılmaz.
  DSP.firUygula = function (x, h) {
    var n = x.length, y = new Float64Array(n);
    for (var k = 0; k < n; k++) { var s = 0; for (var j = 0; j < h.length; j++) { var idx = k - j; if (idx >= 0) s += h[j] * x[idx]; } y[k] = s; }
    return y;
  };
  DSP.firUygulaKompleks = function (sig, h) { return { i: DSP.firUygula(sig.i, h), q: DSP.firUygula(sig.q, h) }; };
  // CIC: R decimation, N kademe, M=1. Yanıt (dB) M nokta 0..fs_in/2; bit büyümesi N·log2(R)
  DSP.cicYanit = function (R, N, M) {
    var out = new Float64Array(M);
    for (var m = 0; m < M; m++) {
      var f = m / (2 * M); // 0..0.5 (fs_in)
      var num = Math.sin(PI * R * f), den = Math.sin(PI * f);
      var g = f === 0 ? 1 : Math.abs(num / den) / R;
      out[m] = DSP.db20(Math.pow(g, N));
    }
    return out;
  };
  DSP.cicBitBuyumesi = function (R, N) { return Math.ceil(N * Math.log2(R)); };
  // Decimation: her M. örneği al
  DSP.decimate = function (x, M) { var n = Math.floor(x.length / M), y = new Float64Array(n); for (var k = 0; k < n; k++) y[k] = x[k * M]; return y; };
  DSP.decimateKompleks = function (sig, M) { return { i: DSP.decimate(sig.i, M), q: DSP.decimate(sig.q, M) }; };
  // Kompleks mixer: reel/kompleks giriş × e^(∓j2π f_nco n / fs). isaret −1 → aşağı çevirim.
  DSP.mixer = function (x_i, x_q, fsHz, fNcoHz, isaret) {
    var n = x_i.length, i = new Float64Array(n), q = new Float64Array(n), s = isaret === undefined ? -1 : isaret;
    for (var k = 0; k < n; k++) {
      var p = s * TAU * fNcoHz * k / fsHz, c = Math.cos(p), sn = Math.sin(p);
      var xi = x_i[k], xq = x_q ? x_q[k] : 0;
      i[k] = xi * c - xq * sn; q[k] = xi * sn + xq * c;
    }
    return { i: i, q: q };
  };
  // Tam DDC: reel giriş → mix → FIR → decimate. Dönüş: ara noktalar dahil.
  DSP.ddc = function (x, fsHz, fNcoHz, fcHz, M, tap, isaret) {
    var mix = DSP.mixer(x, null, fsHz, fNcoHz, isaret);
    var h = DSP.firTasarla(fcHz, fsHz, tap || 63, "kaiser", 7);
    var fil = DSP.firUygulaKompleks(mix, h);
    var dec = DSP.decimateKompleks(fil, M);
    return { mix: mix, fil: fil, dec: dec, h: h, fsOut: fsHz / M };
  };

  /* -------------------------------------------------------------- zarf / tespit */
  DSP.guc = function (i, q) { var p = new Float64Array(i.length); for (var k = 0; k < i.length; k++) p[k] = i[k] * i[k] + q[k] * q[k]; return p; };
  DSP.zarf = function (i, q) { var p = new Float64Array(i.length); for (var k = 0; k < i.length; k++) p[k] = Math.sqrt(i[k] * i[k] + q[k] * q[k]); return p; };
  // alpha-max + beta-min: (1, 1/2), (1, 1/4), (15/16, 15/32)...
  DSP.alphaMaxBetaMin = function (i, q, alpha, beta) {
    var out = new Float64Array(i.length);
    for (var k = 0; k < i.length; k++) { var a = Math.abs(i[k]), b = Math.abs(q[k]); var mx = Math.max(a, b), mn = Math.min(a, b); out[k] = alpha * mx + beta * mn; }
    return out;
  };
  DSP.kayanOrtalama = function (x, L) {
    var y = new Float64Array(x.length), s = 0;
    for (var k = 0; k < x.length; k++) { s += x[k]; if (k >= L) s -= x[k - L]; y[k] = s / Math.min(L, k + 1); }
    return y;
  };
  // Rayleigh: zarf eşiği (σ cinsinden) verilen Pfa için; σ = I/Q bileşen standart sapması
  DSP.rayleighEsik = function (pfa) { return Math.sqrt(-2 * Math.log(pfa)); };
  DSP.rayleighPfa = function (esikSigma) { return Math.exp(-esikSigma * esikSigma / 2); };
  // Kare yasa dedektör (güç) için eşik: P_esik/σ² = −ln Pfa (üstel dağılım, ortalama güç = 2σ²... normalize: güç/2σ²)
  // Marcum Q ile Pd (Rician zarf): Pd = Q1(√(2·SNR), T/σ). Basit seri toplamı.
  DSP.marcumQ1 = function (a, b) {
    // Q1(a,b) = exp(-(a²+b²)/2) Σ_{k≥0} (a/b)^k I_k(ab)  (b > a); sayısal integral yaklaşımı daha sağlam:
    // Q1(a,b) = ∫_b^∞ x exp(-(x²+a²)/2) I0(ax) dx — Simpson ile.
    if (b <= 0) return 1;
    var ust = Math.max(b + 12, a + 12), n = 2000, h = (ust - b) / n, s = 0;
    for (var k = 0; k <= n; k++) {
      var x = b + k * h;
      var ln = Math.log(x) - (x * x + a * a) / 2 + DSP._lnI0(a * x);
      var v = Math.exp(ln);
      s += (k === 0 || k === n) ? v : (k % 2 ? 4 * v : 2 * v);
    }
    return Math.min(1, s * h / 3);
  };
  DSP._lnI0 = function (x) { if (x < 20) return Math.log(DSP._i0(x)); return x - 0.5 * Math.log(TAU * x) + Math.log(1 + 1 / (8 * x)); };
  // Tek darbe, bilinmeyen fazlı sinyal (Swerling 0): Pd(snr_db, pfa)
  DSP.pdSwerling0 = function (snrDb, pfa) { var snr = DSP.lin10(snrDb); return DSP.marcumQ1(Math.sqrt(2 * snr), DSP.rayleighEsik(pfa)); };
  // Albersheim: hedef Pd, Pfa, N darbe → gereken SNR (dB)
  DSP.albersheim = function (pd, pfa, N) {
    N = N || 1;
    var A = Math.log(0.62 / pfa), B = Math.log(pd / (1 - pd));
    return -5 * Math.log10(N) + (6.2 + 4.54 / Math.sqrt(N + 0.44)) * Math.log10(A + 0.12 * A * B + 1.7 * B);
  };
  // Yanlış alarm oranı (1/s): Pfa × karar hızı
  DSP.far = function (pfa, kararHz) { return pfa * kararHz; };

  /* -------------------------------------------------------------------- CFAR */
  // CA-CFAR çarpanı (kare yasa, N referans hücre): α = N (Pfa^(−1/N) − 1)
  DSP.caCfarAlfa = function (N, pfa) { return N * (Math.pow(pfa, -1 / N) - 1); };
  // OS-CFAR çarpanı: Pfa = Π_{i=0}^{k-1} (N−i)/(N−i+α) → α için ikiye bölme
  DSP.osCfarAlfa = function (N, k, pfa) {
    var f = function (a) { var p = 1; for (var i = 0; i < k; i++) p *= (N - i) / (N - i + a); return p; };
    var lo = 0, hi = 1e4;
    for (var it = 0; it < 200; it++) { var mid = (lo + hi) / 2; if (f(mid) > pfa) lo = mid; else hi = mid; }
    return (lo + hi) / 2;
  };
  // CFAR çalıştır: guc dizisi (kare yasa), tip CA|GO|SO|OS, N (toplam referans), G (guard/taraf), alfa, k (OS sırası)
  // Dönüş {esik: Float64Array, tespit: Uint8Array}
  DSP.cfar = function (guc, tip, N, G, alfa, k) {
    var n = guc.length, esik = new Float64Array(n), tespit = new Uint8Array(n), yarim = N / 2;
    for (var c = 0; c < n; c++) {
      var sol = [], sag = [];
      for (var j = 1; j <= yarim; j++) {
        var a = c - G - j, b = c + G + j;
        if (a >= 0) sol.push(guc[a]); if (b < n) sag.push(guc[b]);
      }
      var z;
      if (tip === "OS") { var t = sol.concat(sag).sort(function (x, y) { return x - y; }); z = t[Math.min(t.length - 1, Math.max(0, (k || Math.round(0.75 * N)) - 1))] * N; }
      else {
        var sS = 0, sG = 0, i2;
        for (i2 = 0; i2 < sol.length; i2++) sS += sol[i2];
        for (i2 = 0; i2 < sag.length; i2++) sG += sag[i2];
        var mS = sol.length ? sS / sol.length : 0, mG = sag.length ? sG / sag.length : 0;
        if (tip === "GO") z = Math.max(mS, mG) * N;
        else if (tip === "SO") z = Math.min(mS, mG) * N;
        else z = sS + sG; // CA: toplam
        if (tip === "CA" && (sol.length + sag.length) < N) z = z * N / Math.max(1, sol.length + sag.length);
      }
      esik[c] = alfa * z / N; // hücre başına ortalama × α
      tespit[c] = guc[c] > esik[c] ? 1 : 0;
    }
    return { esik: esik, tespit: tespit };
  };

  // Kapılı (gated) gürültü kestirimi: üstel ortalama, darbe varken dondurulur.
  // guc: kare yasa; alfa: eşik çarpanı; tau: zaman sabiti (örnek). Dönüş {esik, tahmin}.
  DSP.kapiliGurultuKestirimi = function (guc, alfa, tau) {
    var n = guc.length, esik = new Float64Array(n), tahmin = new Float64Array(n);
    var k, ilk = Math.min(n, Math.max(8, tau)), m = 0;
    for (k = 0; k < ilk; k++) m += guc[k];
    m = m / ilk; var a = 1 / tau;
    for (k = 0; k < n; k++) {
      var e = alfa * m;
      esik[k] = e; tahmin[k] = m;
      if (guc[k] < e) m += a * (guc[k] - m);   // darbe yokken güncelle, varken dondur
    }
    return { esik: esik, tahmin: tahmin };
  };

  /* --------------------------------------------------------------- darbe FSM / PDW */
  // guc: kare yasa örnekleri; esik: sabit sayı veya dizi; hister: dB; minPw: örnek; fs: Hz
  // Dönüş: [{toa_s, pw_s, pa_dbfs, pa_lin, bas, son, kirpildi}]
  DSP.darbeFsm = function (guc, esik, opts) {
    opts = opts || {};
    var fs = opts.fs || 1, hister = DSP.lin10(-(opts.histerezisDb || 0)), minPw = opts.minPw || 1, maxPw = opts.maxPw || Infinity;
    var durum = "IDLE", bas = 0, tepe = 0, pdw = [], say = 0;
    var esikAl = typeof esik === "number" ? function () { return esik; } : function (k) { return esik[k]; };
    for (var k = 0; k < guc.length; k++) {
      var e = esikAl(k);
      if (durum === "IDLE") {
        if (guc[k] > e) { durum = "IN"; bas = k; tepe = guc[k]; say = 1; }
      } else {
        tepe = Math.max(tepe, guc[k]);
        say++;
        if (guc[k] < e * hister || say >= maxPw) {
          var pw = k - bas;
          if (pw >= minPw) pdw.push({ toa_s: bas / fs, pw_s: pw / fs, pa_lin: tepe, pa_dbfs: DSP.db10(tepe), bas: bas, son: k, kirpildi: say >= maxPw, ornek: pw });
          durum = "IDLE";
        }
      }
    }
    return pdw;
  };
  // Darbe içi frekans ölçümü: anlık frekans ortalaması (kenarlar hariç)
  DSP.darbeFrekansi = function (i, q, bas, son, fs) {
    var af = DSP.anlikFrekans(i.subarray(bas, son), q.subarray(bas, son), fs), s = 0, n = 0;
    var kes = Math.max(1, Math.floor((son - bas) * 0.1));
    for (var k = kes; k < af.length - kes; k++) { s += af[k]; n++; }
    return n ? s / n : 0;
  };
  // Chirp eğimi (Hz/s): anlık frekansa doğrusal uydurma
  DSP.chirpEgimi = function (i, q, bas, son, fs) {
    var af = DSP.anlikFrekans(i.subarray(bas, son), q.subarray(bas, son), fs), n = 0, sx = 0, sy = 0, sxx = 0, sxy = 0;
    var kes = Math.max(1, Math.floor((son - bas) * 0.1));
    for (var k = kes; k < af.length - kes; k++) { var x = k / fs; sx += x; sy += af[k]; sxx += x * x; sxy += x * af[k]; n++; }
    return n > 1 ? (n * sxy - sx * sy) / (n * sxx - sx * sx) : 0;
  };
  // TOA'nın eşik geçişine bağlı kayması (time walk): kosinüs kenarlı darbede eşik seviyesine göre gecikme
  DSP.timeWalk = function (riseS, esikOran) { return riseS / PI * Math.acos(1 - 2 * Math.max(0.001, Math.min(0.999, esikOran))); };

  /* ------------------------------------------------------------- CRLB sezgileri */
  // Tek ton frekans kestirimi CRLB (Hz, rms): σ_f ≈ √(12 / ((2π)² SNR N (N²−1))) · fs  (SNR lineer, N örnek)
  DSP.crlbFrekans = function (snrDb, N, fs) { var snr = DSP.lin10(snrDb); return Math.sqrt(12 / (TAU * TAU * snr * N * (N * N - 1))) * fs; };
  // TOA hatası (rms) ≈ t_rise / √(2·SNR)
  DSP.toaHatasi = function (riseS, snrDb) { return riseS / Math.sqrt(2 * DSP.lin10(snrDb)); };

  /* ------------------------------------------------------- ek yardımcılar (QA turu) */
  // I/Q kazanç (dB) ve faz (derece) dengesizliğinden image seviyesi (dBc): IRR = |1 − g·e^{jφ}|² / |1 + g·e^{jφ}|²
  DSP.iqImageDbc = function (kazancDb, fazDeg) {
    var g = DSP.lin20(kazancDb), f = fazDeg * PI / 180;
    var pay = 1 + g * g - 2 * g * Math.cos(f), payda = 1 + g * g + 2 * g * Math.cos(f);
    return DSP.db10(pay / payda);
  };
  // Bir [fa, fb] bandının 1. Nyquist bölgesine katlanmış [min, max] aralığı (bölge sınırı geçiyorsa 0..fs/2'ye genişler)
  DSP.bantKatla = function (fa, fb, fs) {
    var a = DSP.katla(fa, fs), b = DSP.katla(fb, fs);
    if (a.bolge !== b.bolge) return { min: 0, max: fs / 2, bolunmus: true };
    return { min: Math.min(a.alias, b.alias), max: Math.max(a.alias, b.alias), evrik: a.evrik, bolunmus: false };
  };
  // Jacobsen kesirli tepe kestirimi: üç kompleks bin (k−1, k, k+1) → δ ∈ (−0.5, 0.5)
  DSP.jacobsen = function (rm, im_, r0, i0, rp, ip) {
    var nr = rm - rp, ni = im_ - ip, dr = 2 * r0 - rm - rp, di = 2 * i0 - im_ - ip;
    var d = dr * dr + di * di;
    return d === 0 ? 0 : -(nr * dr + ni * di) / d;
  };
  // OS-CFAR: k'ıncı sıra istatistiğinin beklenen değeri (birim ortalama gürültüde) = Σ_{i<k} 1/(N−i)
  DSP.osOrtalamaKat = function (N, k) { var s = 0; for (var i = 0; i < k; i++) s += 1 / (N - i); return s; };

  /* ---------------------------------------------------------------- yardımcılar */
  DSP.linspace = function (a, b, n) { var o = new Float64Array(n); for (var k = 0; k < n; k++) o[k] = a + (b - a) * k / (n - 1); return o; };
  DSP.maks = function (x) { var m = -Infinity; for (var k = 0; k < x.length; k++) if (x[k] > m) m = x[k]; return m; };
  DSP.min = function (x) { var m = Infinity; for (var k = 0; k < x.length; k++) if (x[k] < m) m = x[k]; return m; };
  DSP.ortalama = function (x) { var s = 0; for (var k = 0; k < x.length; k++) s += x[k]; return s / x.length; };
  DSP.medyan = function (x) { var t = Array.prototype.slice.call(x).sort(function (a, b) { return a - b; }); var m = t.length >> 1; return t.length % 2 ? t[m] : (t[m - 1] + t[m]) / 2; };
  DSP.rms = function (x) { var s = 0; for (var k = 0; k < x.length; k++) s += x[k] * x[k]; return Math.sqrt(s / x.length); };
  DSP.sinc = function (x) { return x === 0 ? 1 : Math.sin(PI * x) / (PI * x); };
  DSP.birimFormat = function (hz) {
    var a = Math.abs(hz);
    if (a >= 1e9) return (hz / 1e9).toFixed(3).replace(/\.?0+$/, "") + " GHz";
    if (a >= 1e6) return (hz / 1e6).toFixed(3).replace(/\.?0+$/, "") + " MHz";
    if (a >= 1e3) return (hz / 1e3).toFixed(3).replace(/\.?0+$/, "") + " kHz";
    return hz.toFixed(2).replace(/\.?0+$/, "") + " Hz";
  };
  DSP.sureFormat = function (s) {
    var a = Math.abs(s);
    if (a >= 1) return s.toFixed(3) + " s";
    if (a >= 1e-3) return (s * 1e3).toFixed(3) + " ms";
    if (a >= 1e-6) return (s * 1e6).toFixed(3) + " µs";
    if (a >= 1e-9) return (s * 1e9).toFixed(2) + " ns";
    return (s * 1e12).toFixed(1) + " ps";
  };

  if (typeof module !== "undefined" && module.exports) module.exports = DSP;
  else kok.DSP = DSP;
})(typeof window !== "undefined" ? window : this);
