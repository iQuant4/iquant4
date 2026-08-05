# Getting Started — Design a Coexistence Link

This walkthrough takes you from a bare fiber to a full classical-plus-quantum
operating point in a handful of lines. Every snippet is runnable as-is against
the installed package; the printed numbers are what you should see.

> **Install:** `pip install -e ".[dev]"` in a Python 3.10+ virtual environment.
> The physics needs only NumPy / SciPy.

---

## 1. Describe the fiber once

Everything in iQuant4 hangs off one physical description of the fiber. The
built-in `SMF28` preset is standard single-mode fiber; `transmissivity` is the
power that survives a span — the *same* number the quantum branch consumes.

```python
from iqcore.fiber import SMF28

print(SMF28.loss_db(60))          # 12.0  (dB over 60 km @ 0.2 dB/km)
print(SMF28.transmissivity(60))   # 0.0631
```

## 2. Close a classical 400G-class link

`format_capacity_bps` tells you whether a modulation format closes over a route
at a given launch power, and the capacity it delivers. Here: 40 DWDM channels of
16-QAM over 60 km at −6 dBm/channel.

```python
from iq4comm.qkd import format_capacity_bps

capacity, ber, closes = format_capacity_bps("16QAM", -6, 40, 60)
print(closes, capacity / 1e12, "Tb/s", ber)   # True 5.1 Tb/s 1.8e-90
```

Add a real forward-error-correcting code to decide closure against its *computed*
threshold and charge its overhead honestly:

```python
from iq4comm.dsp import get_fec_code

fec = get_fec_code("SD-FEC-20%")               # 20% soft-decision LDPC
capacity, ber, closes = format_capacity_bps("16QAM", -6, 40, 60, fec=fec)
print(capacity / 1e12, "Tb/s net of overhead")  # 4.3 Tb/s
```

## 3. Add a quantum channel on the same fiber

Now put a QKD channel alongside the classical traffic. The classical power drives
spontaneous-Raman noise into the quantum channel, so the secret-key rate depends
on the launch power you chose above:

```python
from iq4comm.qkd import protocol_coexistence_key_rate

skr = protocol_coexistence_key_rate("dv", 60, -18, 40)   # DV-BB84, -18 dBm/ch
print(skr, "bits/pulse")                                 # 7.55e-04
```

Lower launch → less Raman → more key. That tension is the whole design problem.

## 4. Let the platform find the operating point

You do not have to sweep by hand. `optimize_launch_power` maximises classical
capacity subject to a minimum secret-key rate, and tells you whether the QKD
constraint is what limits you:

```python
from iq4comm.qkd import optimize_launch_power

op = optimize_launch_power(60, 40, 1e-6, protocol="dv")   # need >= 1e-6 bits/pulse
print(op.feasible, op.launch_dbm, op.qkd_constraint_binds)
# True  -16.4  True   -> feasible; QKD security sets the launch power
```

And `select_best_protocol` picks the best QKD protocol for the route:

```python
from iq4comm.qkd import select_best_protocol

best, rate, rates = select_best_protocol(60, 40, -18)
print(best, rates)
# cv {'dv': 0.0008, 'cv': 0.0062, 'mdi': 0.0004, 'tf': 0.0051}
```

Here **CV-QKD** wins — and it reuses the same coherent receiver as the classical
channels, which is why it is attractive for a coherent metro network.

## 5. Check the reach

How far does the overlay scale before it needs a trusted node or a repeater?

```python
from iq4comm.qkd import coexistence_reach

reach_km = coexistence_reach(40, 1e-6, 1e12, protocol="tf")   # Twin-Field
print(reach_km, "km")                                          # 155.0
```

## 6. Everything at once

`system_operating_point` folds *every* knob — distance, loading, launch, format,
roll-off, FEC, ROADM count, protocol — into one call returning both outputs:

```python
from iq4comm.qkd import system_operating_point
from iq4comm.dsp import PulseShape, get_fec_code

op = system_operating_point(
    distance_km=60, n_channels=40, launch_dbm_per_channel=-21,
    fmt="16QAM", pulse=PulseShape("rrc", 0.2),
    fec=get_fec_code("SD-FEC-20%"), n_roadms=0, qkd_protocol="dv")

print(op.classical_closes, op.capacity_tbps, op.secret_key_rate)
```

## Where to go next

- **Interactive:** open [`explorer/iquant4_explorer.html`](../explorer/iquant4_explorer.html)
  and drag the knobs — it runs the same physics in the browser.
- **The full story:** [`docs/case_study_metro_qkd.md`](case_study_metro_qkd.md)
  designs a QKD overlay on a live 400G metro link end to end.
- **Trust the numbers:** [`VALIDATION.md`](../VALIDATION.md) benchmarks every model.
- **Reproduce the case study:** `python -m examples.case_study_metro_qkd`.
