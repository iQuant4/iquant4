"""BER demo for the iQuant4 communications branch.

Prints theory-vs-simulation BER for the standard formats, and closes the loop
from a fiber link: OSNR (from iqcore.fiber.Link) -> Eb/N0 -> BER.

Run:
    python -m examples.ber_demo
"""

from __future__ import annotations

import numpy as np

from iq4comm.dsp import ber_theory, monte_carlo_ber, osnr_db_to_ebn0_db
from iqcore.fiber import Amplifier, Link, SMF28


def main() -> None:
    rng = np.random.default_rng(2025)
    print("BER: theory vs Monte-Carlo (AWGN)\n")
    print(f"{'format':>7} {'Eb/N0':>7} {'theory':>11} {'sim':>11}")
    for fmt, ebn0 in [("BPSK", 6.0), ("QPSK", 6.0), ("16QAM", 12.0), ("64QAM", 18.0)]:
        mc = monte_carlo_ber(fmt, ebn0, num_bits=2_000_000, rng=rng).ber
        print(f"{fmt:>7} {ebn0:>6.1f}dB {ber_theory(fmt, ebn0):>11.2e} {mc:>11.2e}")

    # Close the loop: build a link, read its OSNR, convert to BER.
    print("\nFiber link -> OSNR -> BER (QPSK, 32 GBd):\n")
    print(f"{'spans':>6} {'reach_km':>9} {'OSNR_dB':>8} {'Eb/N0_dB':>9} {'BER':>11}")
    for n in (4, 8, 12, 16, 20):
        link = Link()
        for _ in range(n):
            link.span(SMF28, 80.0).amplifier(
                Amplifier(gain_db=SMF28.loss_db(80.0), noise_figure_db=5.0))
        osnr = link.osnr_db(1e-3)
        ebn0 = osnr_db_to_ebn0_db(osnr, 32e9, bits_per_symbol=2)
        print(f"{n:>6} {link.total_length_km:>9.0f} {osnr:>8.2f} {ebn0:>9.2f} "
              f"{ber_theory('QPSK', ebn0):>11.2e}")


if __name__ == "__main__":
    main()
