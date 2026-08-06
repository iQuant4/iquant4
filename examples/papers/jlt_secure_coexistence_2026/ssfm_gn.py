"""GN-model vs split-step-Fourier (SSFM) cross-check of the NLI power law.

Loads the fiber with a Gaussian-modulated WDM comb (the GN model's own signal
assumption), propagates with and without the Kerr term, and measures the
center-channel nonlinear-interference (NLI) variance versus launch power. Tests
(i) the cubic law P_NLI ~ eta P^3 and (ii) the coefficient against the GN
closed form, at powers spanning P_sec and P_GN.
"""
import numpy as np
from iqcore.fiber import SMF28
from iqcore.fiber.propagation import TimeGrid, propagate
from iq4comm.dsp.gn_model import nli_coefficient

rng = np.random.default_rng(1234)

NCH = 8
DF_HZ = 50e9
RS = 32e9
L = 80.0
SPS = 16                       # samples per symbol
NSYM = 1024
fs_hz = RS * SPS               # sample rate
dt_ps = 1e12 / fs_hz
N = NSYM * SPS
grid = TimeGrid(num_points=N, dt_ps=dt_ps)
t = np.arange(N) * dt_ps       # ps
freqs = np.fft.fftfreq(N, d=dt_ps) * 1e12   # Hz

# channel center frequencies (no channel at DC), pick nearest-to-center as victim
ch_offsets = (np.arange(NCH) - (NCH - 1) / 2.0) * DF_HZ
victim = int(np.argmin(np.abs(ch_offsets)))


def rrc(nsym, sps, beta=0.2):
    N_ = nsym * sps
    f = np.fft.fftfreq(N_, d=1.0 / sps)          # in symbol-rate units
    H = np.zeros(N_)
    a = np.abs(f)
    H[a <= (1 - beta) / 2] = 1.0
    mid = (a > (1 - beta) / 2) & (a <= (1 + beta) / 2)
    H[mid] = 0.5 * (1 + np.cos(np.pi / beta * (a[mid] - (1 - beta) / 2)))
    return np.sqrt(H)


RRC = rrc(NSYM, SPS, 0.2)


def build_field(p_ch_w):
    """Gaussian-modulated WDM comb at per-channel power p_ch_w (sqrt(W) envelope)."""
    field = np.zeros(N, dtype=complex)
    for off in ch_offsets:
        sym = (rng.standard_normal(NSYM) + 1j * rng.standard_normal(NSYM)) / np.sqrt(2)
        up = np.zeros(N, dtype=complex); up[::SPS] = sym
        shaped = np.fft.ifft(np.fft.fft(up) * RRC)
        shaped *= np.sqrt(p_ch_w) / np.sqrt(np.mean(np.abs(shaped) ** 2))
        field += shaped * np.exp(2j * np.pi * off * (t * 1e-12))
    return field


def center_band_power(x):
    """Power of x within the victim channel's Rs-wide band."""
    X = np.fft.fft(x)
    band = np.abs(freqs - ch_offsets[victim]) <= RS / 2
    return np.sum(np.abs(X[band]) ** 2) / N ** 2 * N  # Parseval-normalized power


def nli_variance(p_ch_w):
    a0 = build_field(p_ch_w)
    lin = propagate(a0, grid, SMF28, L, include_nonlinearity=False)
    nl = propagate(a0, grid, SMF28, L, include_nonlinearity=True)
    # best-fit complex gain removing linear/SPM-mean phase+amplitude
    Xl = np.fft.fft(lin.field); Xn = np.fft.fft(nl.field)
    band = np.abs(freqs - ch_offsets[victim]) <= RS / 2
    g = np.vdot(Xl[band], Xn[band]) / np.vdot(Xl[band], Xl[band])
    resid = np.fft.ifft(np.where(band, Xn - g * Xl, 0.0))
    p_nli = np.mean(np.abs(resid) ** 2) * (N / np.sum(band))  # power in the band
    p_sig = center_band_power(lin.field)
    return p_nli, p_sig


eta_gn = nli_coefficient(SMF28, L, 1, RS, NCH * DF_HZ)
loss_lin = 10 ** (-SMF28.attenuation_db_per_km * L / 10)

print(f"eta_GN (closed form) = {eta_gn:.4g} /W^2   victim ch offset "
      f"{ch_offsets[victim]/1e9:.0f} GHz")
print(f"{'P_ch dBm':>9}{'P_NLI (W)':>13}{'P_NLI/P^3':>13}{'exponent':>10}")
powers_dbm = np.array([-21.5, -18.0, -13.2, -8.0, -2.9])
res = []
for pdbm in powers_dbm:
    p = 1e-3 * 10 ** (pdbm / 10)
    pn, ps = nli_variance(p)
    # refer NLI to launch (undo span loss) for comparison with launch-referred eta P^3
    pn_launch = pn / loss_lin
    res.append((p, pn_launch))
    print(f"{pdbm:>9.1f}{pn_launch:>13.3e}{pn_launch/p**3:>13.3e}")

# fit exponent and coefficient (log-log)
P = np.array([r[0] for r in res]); PN = np.array([r[1] for r in res])
A = np.vstack([np.log(P), np.ones_like(P)]).T
slope, intercept = np.linalg.lstsq(A, np.log(PN), rcond=None)[0]
eta_ssfm = np.exp(intercept)
print(f"\nSSFM NLI power-law exponent = {slope:.3f}  (GN predicts 3.000)")
print(f"eta_SSFM (fit at exponent-3 intercept) = {eta_ssfm:.4g} /W^2")
print(f"eta_SSFM / eta_GN = {eta_ssfm/eta_gn:.3f}  ({10*np.log10(eta_ssfm/eta_gn):+.2f} dB)")
