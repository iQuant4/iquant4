# Case Study — A QKD Security Overlay on a Live 400G Metro DWDM Link

**The problem.** A metro network operator runs 40 × 400G coherent channels over a
60 km fiber between two sites. A regulated customer now needs
quantum-secure key exchange for a subset of that traffic. Laying new dark fiber
is expensive and slow. **Can the operator add a QKD channel on the *same* fiber,
co-propagating with the 40 × 400G traffic — and if so, what does it cost the
400G service?**

This is exactly the question the iQuant4 coexistence engine exists to answer, and
every number below is computed live by the platform (reproduce with
`python -m examples.case_study_metro_qkd`; the underlying models are benchmarked
in `VALIDATION.md`).

---

## The design, in four steps

**1 · The classical 400G link.** 40 channels of DP-16QAM at 64 GBd on a 75 GHz
grid, with 20% soft-decision FEC (11.3 dB net coding gain) — a standard 400G
coherent line. On a 60 km SMF-28 span this link is **not** power-starved: it
closes (pre-FEC BER under the 2×10⁻² SD-FEC threshold) at a launch power as low as
**−24 dBm/channel**. Per channel that is 427 Gb/s net; across 40 channels,
**17.1 Tb/s** aggregate.

**2 · The coexistence constraint.** The quantum channel's enemy is spontaneous
Raman scattering from the classical channels, which scales with total launch
power — so QKD wants the classical power *low*, while the classical link needs it
*high enough to close*. The key realization the platform surfaces: on this route
those two requirements do **not** conflict. Operating at **−21 dBm/channel**
(the close point plus 3 dB of OSNR margin) keeps the 400G link fully closed while
sitting far below the power where the quantum channel dies.

**3 · The QKD overlay.** At that operating point, the co-propagating quantum
channel delivers a healthy secret-key rate — and the platform lets you compare
protocols on the actual route:

| Protocol | Secret-key rate | ≈ throughput @ 1 GHz clock | Note |
|---|---|---|---|
| DV-BB84 (decoy) | 1.75×10⁻³ bits/pulse | ~1.75 Mbit/s | standard, deployable today |
| CV-QKD (homodyne) | 9.60×10⁻³ bits/pulse | ~9.6 Mbit/s | **reuses the same coherent Rx as the 400G channels** |
| Twin-Field | 6.29×10⁻³ bits/pulse | ~6.3 Mbit/s | best reach |
| MDI-QKD | 1.45×10⁻³ bits/pulse | ~1.45 Mbit/s | untrusted relay |

CV-QKD is the standout for a coherent metro network: it detects with the *same
homodyne front-end* already deployed for the 400G channels, so the overlay reuses
existing hardware.

**4 · Reach.** The coexistence optimizer reports how far this overlay scales
before it needs help: **DV-BB84 to ~123 km**, **Twin-Field to ~157 km** — both
comfortably cover this 60 km route with headroom for longer metro rings. Beyond
that, the platform also models trusted-node relays and quantum repeaters (which
break the direct-transmission reach limit entirely).

---

## The verdict

On this 60 km metro route the operator can carry **17 Tb/s of 400G traffic and a
multi-Mbit/s quantum-secure key channel on one fiber** — and the quantum overlay
is **essentially free**, because the 400G link closes with several dB of margin
below the power at which the quantum channel would be swamped. No new fiber, no
capacity sacrifice.

That last sentence is the whole pitch for the coexistence engine: it turns "can
we even do this?" into a concrete operating point, a protocol choice, a reach
number, and a cost — computed from one physical description of the fiber, with
the models benchmarked against published measurements. It is the difference
between selling a *claim* and selling a *design*.

---

*Assumptions & caveats:* single-fiber co-propagation; Raman coefficient calibrated
to da Silva et al. JLT 2014 (factor-of-a-few uncertainty — recalibrate to the
operator's hardware for a firm quote); 1 GHz quantum-channel clock assumed for the
bits/s figures; dual-polarization assumed for the 400G rate. Figure:
`case_study_hero.png`.
