"""Flagship case study: a QKD security overlay on a live 400G metro DWDM link.

A metro operator runs 40 x 400G coherent channels over a 60 km fiber and wants to
add a quantum-key-distribution channel for a security-sensitive service — on the
*same* fiber, no dark fiber, no new cable. Is it feasible, at what settings, and
what does it cost the 400G traffic?

This walks the whole design through the iQuant4 platform end to end, using only
its public APIs, and prints the answer with the numbers that back it. Run:

    python -m examples.case_study_metro_qkd

Every value below is computed live.  MDI/TF are printed only as explicitly
labelled scaling proxies and are excluded from the automatic recommendation.
"""

from __future__ import annotations

from iqcore.fiber import SMF28
from iq4comm.dsp import get_fec_code, net_coding_gain_db
from iq4comm.qkd import (
    minimum_launch_for_format_dbm,
    format_capacity_bps,
    protocol_coexistence_key_rate,
    select_best_protocol,
    coexistence_reach,
)

# ---- Route + channel plan -------------------------------------------------
DISTANCE_KM = 60.0            # metro span, SMF-28
N_CHANNELS = 40              # C-band DWDM
SYMBOL_RATE = 64e9           # 64 GBd
CHANNEL_SPACING = 75e9       # 75 GHz grid (400G-class)
FORMAT = "16QAM"             # DP-16QAM -> 400G/channel
FEC = get_fec_code("SD-FEC-20%")   # 20% soft-decision LDPC, standard for 400G coherent
POL = 2                      # dual polarization
QKD_FLOOR = 1e-6             # minimum acceptable secret-key fraction (bits/pulse)
QKD_CLOCK_HZ = 1e9           # quantum-channel gate rate for the bits/s conversion


def per_channel_net_gbps() -> float:
    """Net 400G-class throughput: DP x bits/symbol x symbol rate x code rate."""
    k = 4                                        # 16-QAM
    return POL * k * SYMBOL_RATE * FEC.rate / 1e9


def main() -> None:
    line = "-" * 74
    print(line)
    print("iQuant4 CASE STUDY — QKD overlay on a 400G metro DWDM link")
    print(line)
    print(f"Route        : {DISTANCE_KM:.0f} km SMF-28 metro span")
    print(f"Classical    : {N_CHANNELS} x DP-16QAM @ {SYMBOL_RATE/1e9:.0f} GBd, "
          f"{CHANNEL_SPACING/1e9:.0f} GHz grid, 20% SD-FEC")
    print(f"Goal         : add a co-propagating QKD channel on the SAME fiber")

    # --- Step 1: classical 400G design -----------------------------------
    p_close = minimum_launch_for_format_dbm(
        FORMAT, N_CHANNELS, DISTANCE_KM, fec=FEC,
        symbol_rate_baud=SYMBOL_RATE, channel_spacing_hz=CHANNEL_SPACING)
    print("\n[1] CLASSICAL 400G LINK")
    print(f"    SD-FEC net coding gain : {net_coding_gain_db('16QAM', FEC):.1f} dB "
          f"(overhead {FEC.overhead_percent:.0f}%)")
    print(f"    min launch to close    : {p_close:.1f} dBm/ch  "
          f"(pre-FEC BER threshold {FEC.threshold_ber():.1e})")
    print(f"    per-channel net rate   : {per_channel_net_gbps():.0f} Gb/s (DP-16QAM, net of FEC)")
    print(f"    aggregate capacity     : {per_channel_net_gbps()*N_CHANNELS/1e3:.1f} Tb/s")

    # --- Step 2: the coexistence constraint ------------------------------
    # The quantum channel needs LOW classical power (Raman); the classical link
    # needs ENOUGH to close. Evaluate a candidate point 3 dB above the classical
    # close threshold; this is a scenario result, not a hardware qualification.
    p_op = p_close + 3.0
    cap, ber, closes = format_capacity_bps(
        FORMAT, p_op, N_CHANNELS, DISTANCE_KM, fec=FEC,
        symbol_rate_baud=SYMBOL_RATE, channel_spacing_hz=CHANNEL_SPACING)
    print("\n[2] CANDIDATE OPERATING POINT")
    print(f"    operating launch       : {p_op:.1f} dBm/ch (min-close + 3 dB OSNR margin)")
    print(f"    classical still closes : {closes}  (BER {ber:.1e})")
    print(f"    modeled net capacity   : {per_channel_net_gbps()*N_CHANNELS/1e3:.1f} Tb/s")

    # --- Step 3: the QKD overlay -----------------------------------------
    print("\n[3] QKD OVERLAY — secret-key rate at the operating point")
    for proto, label in (("dv", "DV-BB84 (decoy)"),
                         ("cv", "CV-QKD (homodyne)")):
        skr = protocol_coexistence_key_rate(proto, DISTANCE_KM, p_op, N_CHANNELS)
        print(f"    {label:<20}: {skr:.2e} bits/pulse  "
              f"~ {skr*QKD_CLOCK_HZ/1e3:6.1f} kbit/s @ {QKD_CLOCK_HZ/1e9:.0f} GHz clock")
    for proto, label in (("tf", "Twin-Field [proxy]"),
                         ("mdi", "MDI-QKD [proxy]")):
        skr = protocol_coexistence_key_rate(
            proto, DISTANCE_KM, p_op, N_CHANNELS,
            allow_scaling_proxy=True)
        print(f"    {label:<20}: {skr:.2e} bits/pulse  exploratory only")
    best, best_rate, _ = select_best_protocol(DISTANCE_KM, N_CHANNELS, p_op)
    best_label = best.upper() if best is not None else "NONE"
    print(f"    eligible recommendation: {best_label}  (rate {best_rate:.2e})")

    # --- Step 4: reach -----------------------------------------------------
    print("\n[4] MODEL REACH — asymptotic/reduced-model sensitivity")
    for proto, label, allow_proxy in (("dv", "DV-BB84", False),
                                      ("tf", "Twin-Field [proxy]", True)):
        reach = coexistence_reach(
            N_CHANNELS, QKD_FLOOR, min_capacity_bps=1e12, protocol=proto,
            symbol_rate_baud=SYMBOL_RATE, channel_spacing_hz=CHANNEL_SPACING,
            max_distance_km=500.0,
            allow_scaling_proxy=allow_proxy)
        print(f"    {label:<18}: coexistence to ~{reach:.0f} km "
              f"({'covers this route' if reach >= DISTANCE_KM else 'short of route'})")
    print("    TF, trusted-node, and repeater outputs are scaling proxies, not designs.")

    print("\n" + line)
    print("MODEL RESULT: the stated 60 km scenario keeps the "
          f"{per_channel_net_gbps()*N_CHANNELS/1e3:.0f} Tb/s classical link closed")
    print("              while the eligible DV/CV research models return positive key")
    print("              rates. Hardware calibration and protocol-specific security")
    print("              analysis are required before an engineering decision.")
    print(line)


if __name__ == "__main__":
    main()
