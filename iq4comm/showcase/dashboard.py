"""Offline HTML dashboard for the iQuant4 developer-alpha showcase."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from html import escape
import json
from pathlib import Path
from typing import Any, Mapping
import webbrowser

from iq4comm._version import __version__

from ._artifacts import prepare_output_directory, write_json


@dataclass(frozen=True, slots=True)
class ShowcaseDashboardResult:
    """Paths and summary data produced by the showcase dashboard."""

    output_directory: Path
    html_path: Path
    standalone_html_path: Path
    data_path: Path
    json_path: Path
    summary: dict[str, Any]
    browser_opened: bool


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Required showcase artifact is missing: {path}. "
            "Run 'iq4comm showcase all' first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _receiver_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = list(payload.get("rows", []))
    if not rows:
        raise ValueError("Receiver-family results contain no rows.")
    winners = [str(row["winner"]) for row in rows]
    winner_counts = Counter(winners)
    final_row = rows[-1]
    final_winner = str(final_row["winner"])
    final_receiver = final_row["receivers"][final_winner]
    all_bers = [
        float(receiver["conditional_ber"])
        for row in rows
        for receiver in row["receivers"].values()
    ]
    return {
        "distance_count": len(rows),
        "minimum_distance_km": float(rows[0]["distance_km"]),
        "maximum_distance_km": float(final_row["distance_km"]),
        "winner_sequence": winners,
        "winner_counts": dict(sorted(winner_counts.items())),
        "unique_winners": sorted(winner_counts),
        "final_winner": final_winner,
        "final_winner_conditional_ber": float(
            final_receiver["conditional_ber"]
        ),
        "minimum_conditional_ber": min(all_bers),
        "rows": rows,
    }


def _cat_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = list(payload.get("rows", []))
    if not rows:
        raise ValueError("Lossy-cat results contain no rows.")
    initial = rows[0]
    final = rows[-1]
    initial_negativity = float(initial["wigner_negativity"])
    final_negativity = float(final["wigner_negativity"])
    reduction = max(0.0, initial_negativity - final_negativity)
    reduction_percent = (
        100.0 * reduction / initial_negativity
        if initial_negativity > 0.0
        else 0.0
    )
    return {
        "state_count": len(rows),
        "initial_transmissivity": float(initial["transmissivity"]),
        "final_transmissivity": float(final["transmissivity"]),
        "initial_wigner_negativity": initial_negativity,
        "final_wigner_negativity": final_negativity,
        "wigner_negativity_reduction": reduction,
        "wigner_negativity_reduction_percent": reduction_percent,
        "final_purity": float(final["purity"]),
        "rows": rows,
    }


def _tomography_summary(payload: dict[str, Any]) -> dict[str, Any]:
    status = str(payload.get("status", "unknown"))
    fidelity = payload.get("fidelity")
    return {
        "status": status,
        "fidelity": None if fidelity is None else float(fidelity),
        "probability_rmse": payload.get("probability_rmse"),
        "vectorization_error": payload.get("vectorization_error"),
        "solver_status": payload.get("solver_status"),
        "reason": payload.get("reason"),
    }


def showcase_dashboard_payload(
    output_directory: str | Path,
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable summary from showcase artifacts."""
    root = Path(output_directory).expanduser().resolve()
    receiver = _read_json(
        root / "receiver_family" / "receiver_family_results.json"
    )
    cat = _read_json(root / "lossy_cat" / "lossy_cat_metrics.json")
    tomography_path = root / "sign_free_tomography" / "tomography_summary.json"
    tomography = (
        _read_json(tomography_path)
        if tomography_path.is_file()
        else {
            "status": "not-requested",
            "reason": "The tomography showcase was not generated.",
        }
    )
    return {
        "dashboard": "iQuant4 developer-alpha showcase",
        "version": __version__,
        "product": "iQuant4Comm",
        "active_packages": ["iqcore", "iq4comm"],
        "roadmap": [
            {"branch": "iQuant4Comm", "status": "active"},
            {"branch": "iQuant4Compute", "status": "planned"},
            {"branch": "iQuant4Sense", "status": "planned"},
            {"branch": "iQuant4Photonics", "status": "planned"},
        ],
        "offline_ready": True,
        "receiver_family": _receiver_summary(receiver),
        "lossy_cat": _cat_summary(cat),
        "sign_free_tomography": _tomography_summary(tomography),
    }


def _format_scientific(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}e}"


def _format_decimal(value: Any, digits: int = 4) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}"


def _artifact_links(paths: tuple[tuple[str, str], ...]) -> str:
    return "".join(
        f'<a class="artifact" href="{escape(path, quote=True)}">'
        f"{escape(label)}</a>"
        for label, path in paths
    )


def _receiver_rows(summary: dict[str, Any]) -> str:
    output: list[str] = []
    for row in summary["rows"]:
        receiver_cells: list[str] = []
        for family in ("PNR", "Homodyne", "Heterodyne"):
            receiver = row["receivers"][family]
            receiver_cells.append(
                "<td>"
                f"<strong>{escape(family)}</strong><br>"
                f"BER {_format_scientific(receiver['conditional_ber'])}<br>"
                f"P<sub>acc</sub> {_format_decimal(receiver['acceptance_probability'])}"
                "</td>"
            )
        winner = escape(str(row["winner"]))
        output.append(
            "<tr>"
            f"<td>{float(row['distance_km']):.1f}</td>"
            f"<td>{float(row['transmittance']):.4f}</td>"
            + "".join(receiver_cells)
            + f'<td><span class="winner">{winner}</span></td>'
            + "</tr>"
        )
    return "".join(output)


def _cat_rows(summary: dict[str, Any]) -> str:
    return "".join(
        "<tr>"
        f"<td>{float(row['transmissivity']):.2f}</td>"
        f"<td>{_format_decimal(row['mean_photon_number'])}</td>"
        f"<td>{_format_decimal(row['purity'])}</td>"
        f"<td>{_format_decimal(row['wigner_negativity'], 6)}</td>"
        f"<td>{_format_decimal(row['wigner_normalization'], 6)}</td>"
        "</tr>"
        for row in summary["rows"]
    )


def _render_dashboard(summary: dict[str, Any], title: str) -> str:
    receiver = summary["receiver_family"]
    cat = summary["lossy_cat"]
    tomography = summary["sign_free_tomography"]
    tomography_completed = tomography["status"] == "completed"
    tomography_metric = (
        _format_decimal(tomography["fidelity"], 6)
        if tomography_completed
        else escape(str(tomography["status"]))
    )
    tomography_visual = (
        '<img src="sign_free_tomography/tomography_reconstruction.png" '
        'alt="Sign-free tomography reconstruction">'
        if tomography_completed
        else (
            '<div class="notice">Tomography status: '
            f'<strong>{escape(str(tomography["status"]))}</strong>. '
            f'{escape(str(tomography.get("reason") or "No figure was generated."))}'
            "</div>"
        )
    )
    receiver_links = _artifact_links(
        (
            ("Text report", "receiver_family/receiver_family_report.txt"),
            ("CSV data", "receiver_family/receiver_family_results.csv"),
            ("JSON data", "receiver_family/receiver_family_results.json"),
            ("BER figure", "receiver_family/receiver_family_ber.png"),
        )
    )
    cat_links = _artifact_links(
        (
            ("CSV data", "lossy_cat/lossy_cat_metrics.csv"),
            ("JSON data", "lossy_cat/lossy_cat_metrics.json"),
            ("Wigner figure", "lossy_cat/lossy_cat_wigner.png"),
        )
    )
    tomography_links = _artifact_links(
        (("JSON summary", "sign_free_tomography/tomography_summary.json"),)
        + (
            (("Reconstruction figure", "sign_free_tomography/tomography_reconstruction.png"),)
            if tomography_completed
            else ()
        )
    )

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<style>
:root {{ color-scheme: dark; --bg:#07111f; --line:#24364d; --text:#ecf5ff;
--muted:#9db0c6; --accent:#65e4d1; --accent2:#76a8ff; --good:#7cf29a;
--shadow:0 18px 45px rgba(0,0,0,.28); }}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family:Inter,Segoe UI,Arial,sans-serif; background:
radial-gradient(circle at 20% 0%,#123254 0,transparent 34%), var(--bg);
color:var(--text); line-height:1.55; }}
a {{ color:var(--accent); }}
.container {{ width:min(1180px,92vw); margin:auto; }}
.hero {{ padding:72px 0 38px; }}
.eyebrow {{ text-transform:uppercase; letter-spacing:.18em; color:var(--accent);
font-weight:700; font-size:.78rem; }}
h1 {{ font-size:clamp(2.3rem,6vw,4.8rem); line-height:1; margin:.35rem 0 1rem; }}
.subtitle {{ max-width:780px; color:var(--muted); font-size:1.1rem; }}
.badge {{ display:inline-block; padding:.36rem .7rem; border:1px solid var(--line);
border-radius:999px; color:var(--good); background:rgba(124,242,154,.07); }}
.grid {{ display:grid; gap:18px; grid-template-columns:repeat(4,minmax(0,1fr)); }}
.card,.section {{ background:linear-gradient(145deg,rgba(18,36,58,.97),rgba(9,22,38,.97));
border:1px solid var(--line); border-radius:18px; box-shadow:var(--shadow); }}
.card {{ padding:22px; }} .card .value {{ font-size:1.85rem; font-weight:800; }}
.card .label {{ color:var(--muted); font-size:.9rem; }}
.section {{ margin:24px 0; padding:28px; }} .section h2 {{ margin-top:0; font-size:1.7rem; }}
.two {{ display:grid; grid-template-columns:1.1fr .9fr; gap:24px; align-items:start; }}
img {{ width:100%; border-radius:12px; border:1px solid var(--line); background:white; }}
table {{ width:100%; border-collapse:collapse; margin-top:18px; font-size:.9rem; }}
th,td {{ text-align:left; border-bottom:1px solid var(--line); padding:10px 8px; }}
th {{ color:var(--accent2); }} .winner {{ color:var(--good); font-weight:800; }}
.artifacts {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
.artifact {{ text-decoration:none; padding:.48rem .7rem; border:1px solid var(--line);
border-radius:9px; background:#0a1728; }}
.notice {{ padding:24px; border:1px dashed var(--line); border-radius:12px; color:var(--muted); }}
.pillars {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:20px; }}
.pillar {{ padding:16px; border-left:3px solid var(--accent); background:rgba(101,228,209,.05); }}
footer {{ color:var(--muted); padding:34px 0 50px; font-size:.9rem; }}
@media (max-width:900px) {{ .grid {{grid-template-columns:repeat(2,1fr)}} .two {{grid-template-columns:1fr}} }}
@media (max-width:560px) {{ .grid,.pillars {{grid-template-columns:1fr}} .section {{padding:20px}} table {{font-size:.78rem}} }}
</style>
</head>
<body>
<header class="hero"><div class="container">
<div class="eyebrow">iQuant4 Developer Alpha · v{escape(summary['version'])}</div>
<h1>{escape(title)}</h1>
<p class="subtitle">An offline, reproducible view of <code>iqcore</code> and
<code>iq4comm</code>: receiver optimization, nonclassical-state loss analysis,
and sign-free quantum-state reconstruction.</p>
<span class="badge">Offline dashboard · no external assets</span>
<div class="pillars">
<div class="pillar"><strong>Solutions</strong><br><span class="label">Receiver selection, loss analysis, state reconstruction.</span></div>
<div class="pillar"><strong>Convenience</strong><br><span class="label">One command produces figures, data, reports, and this page.</span></div>
<div class="pillar"><strong>Experience</strong><br><span class="label">Visual scientific outputs that can be explored immediately.</span></div>
</div></div></header>
<main class="container">
<section class="section"><h2>One platform, four quantum directions</h2>
<div class="grid">
<div class="card"><div class="value">Comm</div><div class="label">iQuant4Comm · active</div></div>
<div class="card"><div class="value">Compute</div><div class="label">iQuant4Compute · planned</div></div>
<div class="card"><div class="value">Sense</div><div class="label">iQuant4Sense · planned</div></div>
<div class="card"><div class="value">Photonics</div><div class="label">iQuant4Photonics · planned</div></div>
</div></section>
<section class="grid">
<div class="card"><div class="value">{receiver['distance_count']}</div><div class="label">fiber distances evaluated</div></div>
<div class="card"><div class="value">{escape(receiver['final_winner'])}</div><div class="label">winner at {receiver['maximum_distance_km']:.0f} km</div></div>
<div class="card"><div class="value">{cat['wigner_negativity_reduction_percent']:.1f}%</div><div class="label">Wigner-negativity reduction</div></div>
<div class="card"><div class="value">{tomography_metric}</div><div class="label">tomography fidelity / status</div></div>
</section>
<section class="section"><div class="two"><div>
<h2>Receiver-family optimization</h2>
<p>PNR, homodyne, and heterodyne receiver families are optimized under a common
minimum-acceptance constraint. The final point selects
<strong>{escape(receiver['final_winner'])}</strong> with conditional BER
<strong>{_format_scientific(receiver['final_winner_conditional_ber'])}</strong>.</p>
<div class="artifacts">{receiver_links}</div></div>
<img src="receiver_family/receiver_family_ber.png" alt="Optimized receiver-family BER comparison"></div>
<table><thead><tr><th>Distance</th><th>T</th><th>PNR</th><th>Homodyne</th><th>Heterodyne</th><th>Winner</th></tr></thead>
<tbody>{_receiver_rows(receiver)}</tbody></table></section>
<section class="section"><div class="two"><div>
<h2>Loss-degraded cat state</h2>
<p>The even-cat state is propagated through a bosonic pure-loss channel.
Integrated Wigner negativity falls from <strong>{cat['initial_wigner_negativity']:.6f}</strong>
to <strong>{cat['final_wigner_negativity']:.6f}</strong>, exposing how attenuation
suppresses nonclassical interference.</p>
<div class="artifacts">{cat_links}</div></div>
<img src="lossy_cat/lossy_cat_wigner.png" alt="Loss-degraded even-cat Wigner functions"></div>
<table><thead><tr><th>η</th><th>Mean photons</th><th>Purity</th><th>Negativity</th><th>Normalization</th></tr></thead>
<tbody>{_cat_rows(cat)}</tbody></table></section>
<section class="section"><div class="two"><div>
<h2>Sign-free quantum tomography</h2>
<p>Status: <strong>{escape(str(tomography['status']))}</strong>. The workflow
constructs sign-free quadrature histograms, validates the vectorized
measurement map, and solves a positive-semidefinite density-matrix
reconstruction when CVXPY is available.</p>
<div class="artifacts">{tomography_links}</div></div>{tomography_visual}</div></section>
<section class="section"><h2>Scope and interpretation</h2>
<p>This developer-alpha dashboard presents numerical models under their
documented conventions and truncations. It is not a hardware certification,
finite-key security proof, or claim of composable QKD security.</p>
<div class="artifacts"><a class="artifact" href="showcase_manifest.json">Showcase manifest</a>
<a class="artifact" href="dashboard_summary.json">Dashboard summary</a></div></section>
</main><footer><div class="container">Generated locally by iQuant4Comm v{escape(summary['version'])}. Relative artifact links keep the page portable.</div></footer>
</body></html>
'''


def _standalone_dashboard(html: str, root: Path) -> str:
    """Embed showcase PNG figures so the HTML can be shared as one file."""
    import base64

    relative_paths = (
        "receiver_family/receiver_family_ber.png",
        "lossy_cat/lossy_cat_wigner.png",
        "sign_free_tomography/tomography_reconstruction.png",
    )
    output = html
    for relative_path in relative_paths:
        image_path = root / relative_path
        if not image_path.is_file():
            continue
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        output = output.replace(
            f'src="{relative_path}"',
            f'src="data:image/png;base64,{encoded}"',
        )
    return output


def build_showcase_dashboard(
    output_directory: str | Path,
    *,
    title: str = "iQuant4 Developer Alpha Showcase",
    manifest: Mapping[str, Any] | None = None,
    open_browser: bool = False,
) -> ShowcaseDashboardResult:
    """Generate folder-relative and standalone offline HTML dashboards."""
    root = prepare_output_directory(output_directory)
    summary = showcase_dashboard_payload(root, manifest=manifest)
    json_path = write_json(root / "dashboard_summary.json", summary)
    data_path = write_json(root / "dashboard_data.json", summary)
    html_path = root / "index.html"
    html = _render_dashboard(summary, title)
    html_path.write_text(html, encoding="utf-8")
    standalone_html_path = root / "iQuant4_showcase_standalone.html"
    standalone_html_path.write_text(
        _standalone_dashboard(html, root),
        encoding="utf-8",
    )
    browser_opened = bool(webbrowser.open(html_path.as_uri())) if open_browser else False
    return ShowcaseDashboardResult(
        output_directory=root,
        html_path=html_path,
        standalone_html_path=standalone_html_path,
        data_path=data_path,
        json_path=json_path,
        summary=summary,
        browser_opened=browser_opened,
    )


def open_showcase_dashboard(path: str | Path) -> bool:
    """Open an existing dashboard or build one from a showcase directory."""
    candidate = Path(path).expanduser().resolve()
    if candidate.is_file():
        html_path = candidate
    else:
        root = prepare_output_directory(candidate)
        html_path = root / "index.html"
        if not html_path.is_file():
            html_path = build_showcase_dashboard(root).html_path
    return bool(webbrowser.open(html_path.as_uri()))


__all__ = [
    "ShowcaseDashboardResult",
    "build_showcase_dashboard",
    "open_showcase_dashboard",
    "showcase_dashboard_payload",
]
