"""Build a publishable static preview for the iQuant4 developer alpha.

The preview combines the installed documentation portal with optional showcase
artifacts under one offline-ready directory.  It does not require a web server
or remote assets, making it suitable for local review and GitHub Pages.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import json
from pathlib import Path
from typing import Any
import webbrowser

from iq4comm._version import __version__
from iq4comm.documentation import build_documentation_portal
from iq4comm.showcase import run_alpha_showcase
from iq4comm.showcase.dashboard import showcase_dashboard_payload


@dataclass(frozen=True, slots=True)
class PublicPreviewResult:
    """Artifacts produced by :func:`build_public_preview`."""

    output_directory: Path
    index_path: Path
    documentation_directory: Path
    showcase_directory: Path | None
    manifest_path: Path
    page_count: int
    showcase_generated: bool
    browser_opened: bool


def _metric(value: Any, digits: int = 4) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}"


def _scientific(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{digits}e}"


def _landing_page(
    *,
    documentation_pages: int,
    documentation_symbols: int,
    showcase_summary: dict[str, Any] | None,
) -> str:
    if showcase_summary is None:
        receiver_card = """
        <article class="metric-card muted-card">
          <span class="label">Showcase</span>
          <strong>Not generated</strong>
          <small>Build again without <code>--skip-showcase</code>.</small>
        </article>
        """
        showcase_action = '<a class="button" href="docs/guides.html">Explore workflow guides</a>'
        showcase_section = """
        <section id="showcase">
          <div class="section-heading"><span>Flagship workflows</span><h2>Generate the scientific showcase when ready.</h2></div>
          <p class="lead">The portal can bundle receiver optimization, lossy cat-state analysis, and optional sign-free tomography into one shareable site.</p>
          <pre><code>iq4comm portal build --output-dir public_preview --include-tomography</code></pre>
        </section>
        """
    else:
        receiver = showcase_summary["receiver_family"]
        cat = showcase_summary["lossy_cat"]
        tomography = showcase_summary["sign_free_tomography"]
        winners = ", ".join(receiver.get("unique_winners", [])) or "—"
        tomography_fidelity = tomography.get("fidelity")
        receiver_card = f"""
        <article class="metric-card">
          <span class="label">Receiver winners</span>
          <strong>{escape(winners)}</strong>
          <small>{int(receiver.get('distance_count', 0))} evaluated distances</small>
        </article>
        """
        tomography_text = (
            f"Fidelity {_metric(tomography_fidelity, 6)}"
            if tomography.get("status") == "completed"
            else escape(str(tomography.get("status", "not requested")))
        )
        showcase_action = '<a class="button" href="showcase/index.html">Explore the showcase</a>'
        showcase_section = f"""
        <section id="showcase">
          <div class="section-heading"><span>Flagship workflows</span><h2>Inspect reproducible scientific outputs.</h2></div>
          <div class="workflow-grid">
            <article class="workflow-card"><span>01</span><h3>Receiver-family optimization</h3><p>Compare optimized PNR, homodyne, and heterodyne receivers over fiber distance.</p><div class="fact">Best observed BER: {_scientific(receiver.get('minimum_conditional_ber'))}</div></article>
            <article class="workflow-card"><span>02</span><h3>Loss-degraded cat state</h3><p>Track purity, photon number, and Wigner negativity as transmissivity decreases.</p><div class="fact">Negativity reduction: {_metric(cat.get('wigner_negativity_reduction_percent'), 2)}%</div></article>
            <article class="workflow-card"><span>03</span><h3>Sign-free tomography</h3><p>Reconstruct a quantum state from sign-free quadrature measurements using vectorized SDP tomography.</p><div class="fact">{tomography_text}</div></article>
          </div>
          <div class="actions"><a class="button primary" href="showcase/index.html">Open showcase dashboard</a><a class="button" href="showcase/showcase_manifest.json">View manifest</a></div>
        </section>
        """

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>iQuant4 Developer Alpha</title>
<link rel="stylesheet" href="portal.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="index.html"><span class="brand-mark">iQ4</span><span><strong>iQuant4</strong><small>Developer Alpha · v{escape(__version__)}</small></span></a>
  <nav><a href="#platform">Platform</a><a href="#showcase">Showcase</a><a href="docs/index.html">Documentation</a><a href="roadmap.html">Roadmap</a></nav>
  <button id="theme-button" aria-label="Toggle theme">◐</button>
</header>
<main>
<section class="hero">
  <div class="eyebrow">Quantum engineering workspace</div>
  <h1>Build, compare, and explain quantum systems with one shared foundation.</h1>
  <p class="lead"><strong>iqcore</strong> provides reusable quantum states, operators, measurements, channels, phase-space analysis, and tomography. <strong>iQuant4Comm</strong> adds communication sources, fiber channels, receiver families, metrics, and optimization.</p>
  <div class="actions"><a class="button primary" href="docs/quickstart.html">Start in five minutes</a>{showcase_action}</div>
  <div class="metrics">
    <article class="metric-card"><span class="label">Version</span><strong>{escape(__version__)}</strong><small>Developer alpha</small></article>
    <article class="metric-card"><span class="label">Documentation</span><strong>{documentation_pages} pages</strong><small>{documentation_symbols} public API symbols</small></article>
    {receiver_card}
  </div>
</section>
<section id="platform">
  <div class="section-heading"><span>Active platform</span><h2>Two packages, one dependency direction.</h2></div>
  <div class="package-grid">
    <article class="package-card"><div class="icon">∿</div><h3>iqcore</h3><p>Application-independent quantum science for all current and future iQuant4 branches.</p><ul><li>States and density matrices</li><li>Operators and optical transformations</li><li>Measurements, phase space, and tomography</li></ul><a href="docs/iqcore_api.html">Browse iqcore API →</a></article>
    <article class="package-card"><div class="icon">⇄</div><h3>iq4comm</h3><p>The first active product branch for optical and quantum communication research.</p><ul><li>Coherent sources and fiber channels</li><li>PNR, homodyne, and heterodyne receivers</li><li>Metrics, optimization, CLI, and reports</li></ul><a href="docs/iq4comm_api.html">Browse iq4comm API →</a></article>
  </div>
</section>
{showcase_section}
<section>
  <div class="section-heading"><span>Product roadmap</span><h2>Solutions, convenience, and experiences.</h2></div>
  <div class="value-grid"><article><h3>Solutions</h3><p>Scientifically grounded building blocks and end-to-end workflows.</p></article><article><h3>Convenience</h3><p>Installable packages, CLI commands, diagnostics, reports, and reproducible artifacts.</p></article><article><h3>Experiences</h3><p>Visual dashboards and documentation that make quantum behavior easier to inspect and communicate.</p></article></div>
  <div class="actions"><a class="button" href="roadmap.html">View the four-branch roadmap</a><a class="button" href="docs/limitations.html">Read scope and limitations</a></div>
</section>
<section class="notice"><strong>Developer-alpha scope.</strong> The platform uses truncated Fock spaces and idealized or asymptotic models in several places. It is a research and engineering toolkit, not a claim of complete device realism or composable security.</section>
</main>
<footer><span>iQuant4 developer alpha · v{escape(__version__)}</span><span>Apache-2.0 · offline-ready static preview</span></footer>
<script src="portal.js"></script>
</body>
</html>'''


def _roadmap_page(*, showcase_generated: bool) -> str:
    showcase_link = (
        '<a href="showcase/index.html">Showcase</a>'
        if showcase_generated
        else '<a href="docs/guides.html">Workflow guides</a>'
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark light"><title>iQuant4 Roadmap</title><link rel="stylesheet" href="portal.css"></head>
<body><header class="site-header"><a class="brand" href="index.html"><span class="brand-mark">iQ4</span><span><strong>iQuant4</strong><small>Four-branch roadmap</small></span></a><nav><a href="index.html">Overview</a><a href="docs/index.html">Documentation</a>{showcase_link}</nav><button id="theme-button" aria-label="Toggle theme">◐</button></header>
<main><section class="hero compact"><div class="eyebrow">iQuant4 roadmap</div><h1>One shared engine. Four application branches.</h1><p class="lead"><strong>iqcore</strong> is the common foundation. iQuant4Comm is active today; Compute, Sense, and Photonics are documented future branches.</p></section>
<section><div class="branch-grid"><article class="branch active"><span>Active</span><h2>iQuant4Comm</h2><p>Optical and quantum communications, receiver optimization, channels, QKD, and DSP.</p></article><article class="branch"><span>Planned</span><h2>iQuant4Compute</h2><p>Quantum computing, circuits, simulation, algorithms, and error correction.</p></article><article class="branch"><span>Planned</span><h2>iQuant4Sense</h2><p>Quantum sensing, imaging, estimation, and metrology.</p></article><article class="branch"><span>Planned</span><h2>iQuant4Photonics</h2><p>Photonic devices, components, integrated systems, and inverse design.</p></article></div></section>
<section class="notice"><strong>Dependency rule.</strong> Product branches may depend on <code>iqcore</code>. <code>iqcore</code> must never depend on a product branch.</section></main><footer><span>iQuant4 roadmap · v{escape(__version__)}</span></footer><script src="portal.js"></script></body></html>'''


_STYLE = r''':root{color-scheme:dark;--bg:#07111f;--surface:#0d1d31;--surface2:#142942;--line:#29415f;--text:#eef7ff;--muted:#9fb3ca;--accent:#63e2d0;--accent2:#80abff;--good:#84f3a1;--shadow:0 18px 48px rgba(0,0,0,.28)}:root[data-theme="light"]{color-scheme:light;--bg:#eef4fb;--surface:#fff;--surface2:#e8f0f9;--line:#c6d5e5;--text:#142337;--muted:#536b84;--accent:#087c70;--accent2:#285fb1;--good:#16763c;--shadow:0 14px 35px rgba(32,62,94,.12)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,"Segoe UI",Arial,sans-serif;line-height:1.62}a{color:var(--accent)}.site-header{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:26px;padding:15px clamp(20px,5vw,72px);border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--bg) 90%,transparent);backdrop-filter:blur(14px)}.brand{display:flex;align-items:center;gap:11px;color:var(--text);text-decoration:none;margin-right:auto}.brand-mark{display:grid;place-items:center;width:47px;height:47px;border-radius:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#07111f;font-weight:900}.brand strong,.brand small{display:block}.brand small{font-size:.72rem;color:var(--muted)}nav{display:flex;gap:18px}nav a{color:var(--muted);text-decoration:none}nav a:hover{color:var(--text)}#theme-button{padding:8px 11px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--text);cursor:pointer}main{max-width:1240px;margin:auto;padding:0 clamp(20px,5vw,72px) 80px}.hero{padding:94px 0 72px}.hero.compact{padding-bottom:36px}.hero h1{max-width:1050px;margin:14px 0 20px;font-size:clamp(2.7rem,7vw,6.4rem);line-height:.98;letter-spacing:-.055em}.lead{max-width:900px;color:var(--muted);font-size:1.14rem}.eyebrow,.section-heading span{color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.17em;font-size:.75rem}.actions{display:flex;gap:11px;flex-wrap:wrap;margin-top:28px}.button{display:inline-block;padding:11px 16px;border:1px solid var(--line);border-radius:11px;text-decoration:none}.button.primary{background:var(--accent);color:#07111f;border-color:var(--accent);font-weight:800}.metrics,.package-grid,.workflow-grid,.value-grid,.branch-grid{display:grid;gap:16px}.metrics{grid-template-columns:repeat(3,1fr);margin-top:52px}.metric-card,.package-card,.workflow-card,.value-grid article,.branch{padding:22px;border:1px solid var(--line);border-radius:17px;background:var(--surface);box-shadow:var(--shadow)}.metric-card strong,.metric-card small,.metric-card span{display:block}.metric-card strong{font-size:1.3rem;margin:6px 0}.metric-card small,.label{color:var(--muted)}.muted-card{opacity:.75}section{margin:44px 0 78px}.section-heading h2{margin:7px 0 25px;font-size:clamp(2rem,4vw,3.6rem);line-height:1.08;letter-spacing:-.035em}.package-grid{grid-template-columns:repeat(2,1fr)}.package-card .icon{font-size:2.3rem;color:var(--accent)}.package-card li,.package-card p,.workflow-card p,.value-grid p,.branch p{color:var(--muted)}.workflow-grid{grid-template-columns:repeat(3,1fr)}.workflow-card>span{font-size:.75rem;color:var(--accent);font-weight:900}.fact{margin-top:18px;padding-top:14px;border-top:1px solid var(--line);color:var(--good);font-weight:800}.value-grid{grid-template-columns:repeat(3,1fr)}.branch-grid{grid-template-columns:repeat(2,1fr)}.branch>span{padding:4px 9px;border-radius:999px;background:rgba(128,171,255,.13);color:var(--accent2);font-size:.67rem;font-weight:800;text-transform:uppercase}.branch.active>span{background:rgba(132,243,161,.13);color:var(--good)}.notice{padding:21px;border:1px solid var(--line);border-left:4px solid var(--accent2);border-radius:13px;background:var(--surface)}pre{padding:18px;overflow:auto;border:1px solid var(--line);border-radius:13px;background:#081524}code{font-family:"Cascadia Code",Consolas,monospace}footer{display:flex;justify-content:space-between;gap:12px;padding:26px clamp(20px,5vw,72px);border-top:1px solid var(--line);color:var(--muted);font-size:.82rem}@media(max-width:900px){nav{display:none}.metrics,.workflow-grid,.value-grid{grid-template-columns:1fr}.package-grid,.branch-grid{grid-template-columns:1fr}.hero{padding-top:64px}.hero h1{font-size:clamp(2.6rem,14vw,4.6rem)}}'''

_SCRIPT = r'''(function(){const root=document.documentElement;const saved=localStorage.getItem("iq4-portal-theme");if(saved)root.dataset.theme=saved;const button=document.getElementById("theme-button");if(button)button.addEventListener("click",()=>{const next=root.dataset.theme==="light"?"dark":"light";root.dataset.theme=next;localStorage.setItem("iq4-portal-theme",next)})})();'''


def build_public_preview(
    output_directory: str | Path,
    *,
    include_showcase: bool = True,
    include_tomography: bool = False,
    require_cvxpy: bool = False,
    open_browser: bool = False,
) -> PublicPreviewResult:
    """Build a complete offline/public-preview site.

    The output is suitable for local review and static hosting.  Documentation
    is always generated.  Showcase artifacts may be omitted for a fast docs-only
    build, or generated with optional tomography.
    """
    root = Path(output_directory).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    documentation = build_documentation_portal(root / "docs")
    showcase_directory: Path | None = None
    showcase_summary: dict[str, Any] | None = None
    if include_showcase:
        showcase_directory = root / "showcase"
        run_alpha_showcase(
            showcase_directory,
            include_tomography=include_tomography,
            require_cvxpy=require_cvxpy,
            include_dashboard=True,
        )
        showcase_summary = showcase_dashboard_payload(showcase_directory)

    (root / "portal.css").write_text(_STYLE, encoding="utf-8")
    (root / "portal.js").write_text(_SCRIPT, encoding="utf-8")
    index = root / "index.html"
    index.write_text(
        _landing_page(
            documentation_pages=documentation.page_count,
            documentation_symbols=documentation.symbol_count,
            showcase_summary=showcase_summary,
        ),
        encoding="utf-8",
    )
    (root / "roadmap.html").write_text(
        _roadmap_page(showcase_generated=include_showcase), encoding="utf-8"
    )
    (root / "404.html").write_text(index.read_text(encoding="utf-8"), encoding="utf-8")
    (root / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (root / ".nojekyll").write_text("", encoding="utf-8")

    pages = [
        "index.html",
        "roadmap.html",
        "404.html",
        "docs/index.html",
    ]
    if include_showcase:
        pages.append("showcase/index.html")
    manifest = {
        "portal": "iQuant4 public developer-alpha preview",
        "version": __version__,
        "offline_ready": True,
        "static_hosting_ready": True,
        "active_packages": ["iqcore", "iq4comm"],
        "documentation": {
            "path": "docs/index.html",
            "page_count": documentation.page_count,
            "symbol_count": documentation.symbol_count,
        },
        "showcase": {
            "generated": include_showcase,
            "path": "showcase/index.html" if include_showcase else None,
            "tomography_requested": bool(include_tomography),
        },
        "pages": pages,
        "assets": ["portal.css", "portal.js", "robots.txt", ".nojekyll"],
    }
    manifest_path = root / "portal_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    opened = bool(webbrowser.open(index.as_uri())) if open_browser else False
    return PublicPreviewResult(
        output_directory=root,
        index_path=index,
        documentation_directory=documentation.output_directory,
        showcase_directory=showcase_directory,
        manifest_path=manifest_path,
        page_count=len(pages),
        showcase_generated=bool(include_showcase),
        browser_opened=opened,
    )


def open_public_preview(path: str | Path) -> bool:
    """Open an existing public-preview index in the default browser."""
    target = Path(path).expanduser().resolve()
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        raise FileNotFoundError(target)
    return bool(webbrowser.open(target.as_uri()))


__all__ = [
    "PublicPreviewResult",
    "build_public_preview",
    "open_public_preview",
]
