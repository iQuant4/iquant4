"""Validation of the WDM grids against ITU-T G.694.1 / G.694.2 references."""

from __future__ import annotations

import pytest

from iqcore.fiber import (
    DWDMGrid,
    CWDMGrid,
    WDMComb,
    WDMChannel,
    CWDM_WAVELENGTHS_NM,
    dwdm_frequency_hz,
    frequency_to_wavelength_nm,
    wavelength_nm_to_frequency_hz,
)


def test_dwdm_anchor_channel():
    """Channel 0 is the 193.1 THz anchor at ~1552.52 nm (ITU-T G.694.1)."""
    grid = DWDMGrid(spacing_ghz=100.0)
    assert grid.frequency_thz(0) == pytest.approx(193.1, abs=1e-9)
    assert grid.wavelength_nm(0) == pytest.approx(1552.524, abs=1e-3)


def test_dwdm_reference_channels_100ghz():
    """Known ITU 100 GHz grid points."""
    grid = DWDMGrid(spacing_ghz=100.0)
    # +1 channel -> 193.2 THz -> 1551.72 nm
    assert grid.frequency_thz(1) == pytest.approx(193.2, abs=1e-9)
    assert grid.wavelength_nm(1) == pytest.approx(1551.721, abs=1e-3)
    # -8 channels -> 192.3 THz -> 1558.98 nm
    assert grid.frequency_thz(-8) == pytest.approx(192.3, abs=1e-9)
    assert grid.wavelength_nm(-8) == pytest.approx(1558.983, abs=1e-3)


def test_dwdm_spacing_and_validation():
    grid50 = DWDMGrid(spacing_ghz=50.0)
    # 50 GHz step between adjacent channels.
    assert (grid50.frequency_hz(1) - grid50.frequency_hz(0)) == pytest.approx(50e9)
    with pytest.raises(ValueError):
        DWDMGrid(spacing_ghz=37.5)  # not a standard spacing


def test_dwdm_nearest_index_round_trip():
    grid = DWDMGrid(spacing_ghz=50.0)
    for n in (-40, -3, 0, 12, 44):
        assert grid.nearest_index(frequency_hz=grid.frequency_hz(n)) == n
        assert grid.nearest_index(wavelength_nm=grid.wavelength_nm(n)) == n


def test_dwdm_c_band_channel_count():
    """A 100 GHz grid yields ~44 channels across the 1530-1565 nm C-band."""
    grid = DWDMGrid(spacing_ghz=100.0)
    chans = grid.c_band_channels()
    assert all(c.in_c_band() for c in chans)
    assert 40 <= len(chans) <= 48
    # Frequencies strictly increasing after sorting.
    freqs = [c.frequency_hz for c in chans]
    assert freqs == sorted(freqs)


def test_cwdm_standard_grid():
    """CWDM is 18 channels, 1271..1611 nm, 20 nm spacing (ITU-T G.694.2)."""
    assert CWDM_WAVELENGTHS_NM[0] == 1271.0
    assert CWDM_WAVELENGTHS_NM[-1] == 1611.0
    assert len(CWDM_WAVELENGTHS_NM) == 18
    diffs = [CWDM_WAVELENGTHS_NM[i + 1] - CWDM_WAVELENGTHS_NM[i]
             for i in range(len(CWDM_WAVELENGTHS_NM) - 1)]
    assert all(d == pytest.approx(20.0) for d in diffs)

    grid = CWDMGrid()
    assert grid.nearest_index(1549.0) == grid.nearest_index(1551.0)  # -> 1551 ch
    assert grid.wavelength_nm(grid.nearest_index(1551.0)) == 1551.0


def test_frequency_wavelength_inverse():
    for lam in (1271.0, 1550.0, 1611.0):
        f = wavelength_nm_to_frequency_hz(lam)
        assert frequency_to_wavelength_nm(f) == pytest.approx(lam, rel=1e-12)


def test_wdm_channel_power_and_band():
    ch = WDMChannel(frequency_hz=dwdm_frequency_hz(0, 100.0), power_w=1e-3)
    assert ch.power_dbm == pytest.approx(0.0)
    assert ch.in_c_band()
    assert ch.wavelength_nm == pytest.approx(1552.524, abs=1e-3)


def test_wdm_comb_aggregate():
    """A uniform comb sums per-channel power correctly (dBm addition)."""
    grid = DWDMGrid(spacing_ghz=50.0)
    comb = WDMComb.uniform(grid, start=-20, stop=19, power_dbm_per_channel=0.0)
    assert comb.num_channels == 40
    # 40 channels x 1 mW = 40 mW -> 16.02 dBm.
    assert comb.total_power_dbm == pytest.approx(16.02, abs=0.02)
    # Occupied bandwidth = 39 * 50 GHz.
    assert comb.occupied_bandwidth_hz == pytest.approx(39 * 50e9)
