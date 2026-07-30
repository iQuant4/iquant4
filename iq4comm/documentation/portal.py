"""Build an offline documentation portal from installed iQuant4 packages.

The portal is intentionally generated from package introspection and embedded
content. It therefore works from an installed wheel, requires no web server,
and does not load remote assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Iterable
import webbrowser

from iq4comm._version import __version__


CORE_MODULES = (
    "iqcore.states",
    "iqcore.operators",
    "iqcore.measurements",
    "iqcore.optics",
    "iqcore.channels",
    "iqcore.phase_space",
    "iqcore.metrics",
    "iqcore.tomography",
    "iqcore.visualization",
)

COMM_MODULES = (
    "iq4comm",
    "iq4comm.sources",
    "iq4comm.channels",
    "iq4comm.models",
    "iq4comm.receivers",
    "iq4comm.metrics",
    "iq4comm.optimization",
    "iq4comm.analysis",
    "iq4comm.showcase",
    "iq4comm.portal",
)


@dataclass(frozen=True, slots=True)
class DocumentationPortalResult:
    """Artifacts created by :func:`build_documentation_portal`."""

    output_directory: Path
    index_path: Path
    iqcore_api_path: Path
    iq4comm_api_path: Path
    manifest_path: Path
    search_index_path: Path
    page_count: int
    symbol_count: int
    browser_opened: bool


def _kind(value: Any) -> str:
    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value) or inspect.isbuiltin(value):
        return "function"
    return "object"


def _signature(value: Any) -> str:
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return ""


def _summary(value: Any) -> str:
    documentation = inspect.getdoc(value) or "No public documentation is available."
    return documentation.split("\n\n", 1)[0].replace("\n", " ")


def _module_inventory(module_name: str) -> dict[str, Any]:
    """Return a JSON-serializable inventory for one public module."""
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {
            "module": module_name,
            "status": "unavailable",
            "reason": f"{type(exc).__name__}: {exc}",
            "summary": "",
            "symbols": [],
        }

    symbols: list[dict[str, str]] = []
    for name in list(getattr(module, "__all__", [])):
        if not hasattr(module, name):
            continue
        value = getattr(module, name)
        symbols.append(
            {
                "name": name,
                "kind": _kind(value),
                "signature": _signature(value),
                "summary": _summary(value),
            }
        )
    return {
        "module": module_name,
        "status": "available",
        "reason": None,
        "summary": inspect.getdoc(module) or "Public module namespace.",
        "symbols": symbols,
    }


def documentation_payload() -> dict[str, Any]:
    """Return the installed-package documentation model."""
    core = [_module_inventory(name) for name in CORE_MODULES]
    communications = [_module_inventory(name) for name in COMM_MODULES]
    return {
        "portal": "iQuant4 developer-alpha documentation",
        "version": __version__,
        "offline_ready": True,
        "active_packages": ["iqcore", "iq4comm"],
        "roadmap": [
            {"branch": "iQuant4Comm", "status": "active"},
            {"branch": "iQuant4Compute", "status": "planned"},
            {"branch": "iQuant4Sense", "status": "planned"},
            {"branch": "iQuant4Photonics", "status": "planned"},
        ],
        "iqcore": core,
        "iq4comm": communications,
    }


def _nav(active: str) -> str:
    pages = (
        ("index.html", "Overview"),
        ("quickstart.html", "Quick start"),
        ("guides.html", "Flagship workflows"),
        ("iqcore_api.html", "iqcore API"),
        ("iq4comm_api.html", "iq4comm API"),
        ("limitations.html", "Scope and limitations"),
    )
    return "".join(
        f'<a class="nav-link{" active" if path == active else ""}" '
        f'href="{path}">{escape(label)}</a>'
        for path, label in pages
    )


def _layout(title: str, active: str, body: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>{escape(title)} · iQuant4</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="shell">
<aside class="sidebar" id="sidebar">
<a class="brand" href="index.html">
<span class="brand-mark">iQ4</span>
<span><strong>iQuant4</strong><small>Developer Alpha Documentation</small></span>
</a>
<div class="version">v{escape(__version__)}</div>
<label class="search-box">
<span>Search API and guides</span>
<input id="search-input" type="search" placeholder="State, receiver, tomography…" autocomplete="off">
</label>
<div id="search-results" class="search-results" hidden></div>
<nav>{_nav(active)}</nav>
</aside>
<main>
<header class="topbar">
<button id="menu-button" class="icon-button" aria-label="Toggle navigation">☰</button>
<div class="breadcrumb">iQuant4 / {escape(title)}</div>
<button id="theme-button" class="icon-button" aria-label="Toggle theme">◐</button>
</header>
<article class="content">{body}</article>
<footer>iQuant4 developer alpha · offline documentation · v{escape(__version__)}</footer>
</main>
</div>
<script src="search_index.js"></script>
<script src="site.js"></script>
</body>
</html>'''


def _module_cards(modules: Iterable[dict[str, Any]]) -> str:
    output: list[str] = []
    for module in modules:
        name = str(module["module"])
        if module["status"] != "available":
            output.append(
                '<section class="module-section">'
                f'<h2><code>{escape(name)}</code></h2>'
                '<div class="notice warning"><strong>Unavailable in this '
                f'build.</strong> {escape(str(module["reason"]))}</div></section>'
            )
            continue
        cards = []
        for symbol in module["symbols"]:
            signature = str(symbol["signature"])
            cards.append(
                '<div class="api-card">'
                f'<span class="kind">{escape(str(symbol["kind"]))}</span>'
                f'<h3><code>{escape(str(symbol["name"]))}{escape(signature)}</code></h3>'
                f'<p>{escape(str(symbol["summary"]))}</p>'
                "</div>"
            )
        output.append(
            '<section class="module-section">'
            f'<h2><code>{escape(name)}</code></h2>'
            f'<p>{escape(str(module["summary"]))}</p>'
            f'<div class="api-grid">{"".join(cards) or "<p>No exported symbols.</p>"}</div>'
            "</section>"
        )
    return "".join(output)


def _index_page(payload: dict[str, Any]) -> str:
    branch_cards = "".join(
        '<div class="branch-card">'
        f'<span class="status {escape(str(branch["status"]))}">{escape(str(branch["status"]))}</span>'
        f'<h3>{escape(str(branch["branch"]))}</h3>'
        "</div>"
        for branch in payload["roadmap"]
    )
    body = f'''
<div class="hero">
<div class="eyebrow">iQuant4 Developer Alpha · v{escape(__version__)}</div>
<h1>Build with a shared quantum-engineering foundation.</h1>
<p class="lead"><strong>iqcore</strong> provides reusable quantum states,
operators, measurements, optical transformations, phase-space tools, metrics,
and tomography. <strong>iQuant4Comm</strong> is the first active product branch,
adding coherent sources, fiber channels, receiver families, optimization,
diagnostics, reports, and reproducible showcases.</p>
<div class="actions"><a class="button primary" href="quickstart.html">Start in five minutes</a>
<a class="button" href="guides.html">Explore flagship workflows</a></div>
</div>
<section><h2>Two active packages</h2><div class="two-column">
<div class="feature"><div class="feature-icon">∿</div><h3>iqcore</h3><p>Application-independent scientific building blocks for present and future iQuant4 branches.</p><a href="iqcore_api.html">Browse the core API →</a></div>
<div class="feature"><div class="feature-icon">⇄</div><h3>iq4comm</h3><p>Communication-specific sources, channels, receivers, metrics, optimization, and user workflows.</p><a href="iq4comm_api.html">Browse the communications API →</a></div>
</div></section>
<section><h2>Product roadmap</h2><div class="branch-grid">{branch_cards}</div></section>
<section><h2>Value roadmap</h2><div class="three-column">
<div class="value-card"><h3>Solutions</h3><p>Scientifically grounded receiver, channel, loss, phase-space, and reconstruction workflows.</p></div>
<div class="value-card"><h3>Convenience</h3><p>Installable packages, typed APIs, CLI commands, diagnostics, machine-readable artifacts, and automated tests.</p></div>
<div class="value-card"><h3>Experiences</h3><p>Visual dashboards and reproducible demonstrations that make quantum behavior easier to inspect and explain.</p></div>
</div></section>
<section class="notice"><strong>Alpha scope.</strong> This release uses truncated Fock spaces and idealized or asymptotic models in several places. It is a research and engineering toolkit, not a claim of complete physical-device or composable-security coverage.</section>
'''
    return _layout("Overview", "index.html", body)


def _quickstart_page() -> str:
    body = r'''
<h1>Five-minute quick start</h1>
<p class="lead">Install the distribution, inspect a nonclassical state, and evaluate a communication receiver.</p>
<h2>Install from a source checkout</h2>
<pre><code>python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,tomography]"
.\.venv\Scripts\python.exe -m iq4comm doctor</code></pre>
<h2>Inspect a cat state with iqcore</h2>
<pre><code class="language-python">import numpy as np
import iqcore as iq

state = iq.states.even_cat_state(alpha=1.5, cutoff=30)
grid = np.linspace(-5.0, 5.0, 151)
wigner = iq.phase_space.wigner_function(state, grid, grid)

print(iq.metrics.mean_photon_number(state))
print(iq.phase_space.wigner_negativity(wigner, grid, grid))</code></pre>
<h2>Evaluate a receiver with iq4comm</h2>
<pre><code class="language-python">import iq4comm as iqc

source = iqc.BinaryCoherentSource(mu_0=2.0, mu_1=8.0)
channel = iqc.FiberChannel(attenuation_db_per_km=0.2)

state_0 = channel.propagate(
    mu=source.mean_photon_number(0),
    alpha=source.amplitude(0),
    distance_km=20.0,
)
state_1 = channel.propagate(
    mu=source.mean_photon_number(1),
    alpha=source.amplitude(1),
    distance_km=20.0,
)

receiver = iqc.ErasurePNRReceiver(lower_threshold=1, upper_threshold=3)
print(receiver.analytical_metrics(state_0, state_1))</code></pre>
<h2>Generate all flagship outputs</h2>
<pre><code>iq4comm showcase all --output-dir showcase_output
Start-Process .\showcase_output\index.html</code></pre>
'''
    return _layout("Quick start", "quickstart.html", body)


def _guides_page() -> str:
    body = r'''
<h1>Flagship workflows</h1>
<div class="workflow-grid">
<div class="workflow"><span>01</span><h2>Receiver-family optimization</h2><p>Optimize and compare PNR, homodyne, and heterodyne receiver families under one fiber channel and acceptance constraint.</p><pre><code>iq4comm receiver-family --distances 0 20 40 60</code></pre></div>
<div class="workflow"><span>02</span><h2>Loss-degraded cat state</h2><p>Apply bosonic pure loss, visualize the Wigner function, and quantify mean photon number, purity, and negativity.</p><pre><code>iq4comm showcase lossy-cat --output-dir showcase_output</code></pre></div>
<div class="workflow"><span>03</span><h2>Sign-free tomography</h2><p>Generate absolute-quadrature observations and reconstruct a physical density matrix with a vectorized SDP.</p><pre><code>iq4comm showcase tomography --output-dir showcase_output --require-cvxpy</code></pre></div>
<div class="workflow"><span>04</span><h2>Offline showcase dashboard</h2><p>Combine the flagship workflows into shareable HTML, CSV, JSON, text, and PNG artifacts.</p><pre><code>iq4comm showcase all --output-dir showcase_output</code></pre></div>
</div>
'''
    return _layout("Flagship workflows", "guides.html", body)


def _limitations_page() -> str:
    body = r'''
<h1>Scope and limitations</h1>
<p class="lead">The developer alpha is designed for transparent research and engineering workflows, not for hiding model assumptions.</p>
<h2>Numerical scope</h2><ul><li>Bosonic states use truncated Fock spaces.</li><li>High-energy, strongly squeezed, or highly displaced states require convergence studies.</li><li>Wigner normalization depends on grid extent and resolution.</li><li>SDP reconstruction depends on solver tolerances and available backends.</li></ul>
<h2>Physical scope</h2><ul><li>Several source, channel, and detector models are idealized.</li><li>The fiber layer does not yet provide a complete temporal, dispersive, nonlinear, and polarization-resolved link model.</li><li>Device imperfections and multimode effects are not universally included.</li></ul>
<h2>Security scope</h2><p>Receiver BER, mutual information, or attack-specific key-rate calculations are not equivalent to a general composable QKD security proof. Security results must state protocol assumptions, adversarial models, finite-key treatment, reconciliation assumptions, and implementation imperfections.</p>
<h2>API stability</h2><p>Version <code>0.1.0a1</code> is an alpha release. Documented namespaces are intentional, but signatures may still change before a stable release. Legacy root modules are temporary compatibility wrappers.</p>
'''
    return _layout("Scope and limitations", "limitations.html", body)


def _api_page(title: str, active: str, modules: Iterable[dict[str, Any]]) -> str:
    body = (
        f"<h1>{escape(title)}</h1>"
        "<p class=\"lead\">Generated from intentional public exports and runtime signatures. "
        "Only symbols declared by the package API are listed.</p>"
        + _module_cards(modules)
    )
    return _layout(title, active, body)


def _search_records(payload: dict[str, Any]) -> list[dict[str, str]]:
    records = [
        {"title": "Overview", "url": "index.html", "text": "iQuant4 iqcore iq4comm solutions convenience experiences roadmap"},
        {"title": "Quick start", "url": "quickstart.html", "text": "installation cat state fiber receiver showcase"},
        {"title": "Flagship workflows", "url": "guides.html", "text": "receiver optimization lossy cat Wigner tomography dashboard"},
        {"title": "Scope and limitations", "url": "limitations.html", "text": "truncation physical security API limitations"},
    ]
    for package_key, page in (("iqcore", "iqcore_api.html"), ("iq4comm", "iq4comm_api.html")):
        for module in payload[package_key]:
            records.append(
                {
                    "title": str(module["module"]),
                    "url": page,
                    "text": " ".join(
                        str(symbol["name"]) + " " + str(symbol["summary"])
                        for symbol in module.get("symbols", [])
                    ),
                }
            )
    return records


def _write_assets(output: Path) -> None:
    (output / "style.css").write_text(_STYLE, encoding="utf-8")
    (output / "site.js").write_text(_SCRIPT, encoding="utf-8")


def build_documentation_portal(
    output_directory: str | Path,
    *,
    open_browser: bool = False,
) -> DocumentationPortalResult:
    """Generate a complete offline portal from installed public APIs."""
    output = Path(output_directory).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    payload = documentation_payload()
    pages = {
        "index.html": _index_page(payload),
        "quickstart.html": _quickstart_page(),
        "guides.html": _guides_page(),
        "iqcore_api.html": _api_page("iqcore API", "iqcore_api.html", payload["iqcore"]),
        "iq4comm_api.html": _api_page("iq4comm API", "iq4comm_api.html", payload["iq4comm"]),
        "limitations.html": _limitations_page(),
    }
    for name, text in pages.items():
        (output / name).write_text(text, encoding="utf-8")
    _write_assets(output)

    search_records = _search_records(payload)
    search_path = output / "search_index.json"
    search_path.write_text(
        json.dumps(search_records, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output / "search_index.js").write_text(
        "window.IQ4_DOCUMENTATION_SEARCH = "
        + json.dumps(search_records, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )

    symbol_count = sum(
        len(module.get("symbols", []))
        for group in (payload["iqcore"], payload["iq4comm"])
        for module in group
    )
    manifest = {
        "portal": payload["portal"],
        "version": payload["version"],
        "offline_ready": True,
        "pages": sorted(pages),
        "assets": ["style.css", "site.js", "search_index.js"],
        "search_index": "search_index.json",
        "symbol_count": symbol_count,
        "active_packages": payload["active_packages"],
    }
    manifest_path = output / "documentation_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    index = output / "index.html"
    opened = webbrowser.open(index.as_uri()) if open_browser else False
    return DocumentationPortalResult(
        output_directory=output,
        index_path=index,
        iqcore_api_path=output / "iqcore_api.html",
        iq4comm_api_path=output / "iq4comm_api.html",
        manifest_path=manifest_path,
        search_index_path=search_path,
        page_count=len(pages),
        symbol_count=symbol_count,
        browser_opened=bool(opened),
    )


def open_documentation_portal(path: str | Path) -> bool:
    """Open an existing documentation index in the default browser."""
    target = Path(path).expanduser().resolve()
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        raise FileNotFoundError(target)
    return bool(webbrowser.open(target.as_uri()))


_STYLE = r''':root { color-scheme:dark; --bg:#07111f; --surface:#0d1d31; --surface2:#142942; --line:#29415f; --text:#eef7ff; --muted:#9fb3ca; --accent:#63e2d0; --accent2:#80abff; --good:#84f3a1; --warning:#ffd178; --code:#081524; --shadow:0 18px 48px rgba(0,0,0,.28); }
:root[data-theme="light"] { color-scheme:light; --bg:#eef4fb; --surface:#fff; --surface2:#e8f0f9; --line:#c6d5e5; --text:#142337; --muted:#536b84; --accent:#087c70; --accent2:#285fb1; --good:#16763c; --warning:#9a6200; --code:#f2f6fa; --shadow:0 14px 35px rgba(32,62,94,.12); }
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,"Segoe UI",Arial,sans-serif;line-height:1.62} a{color:var(--accent)} .shell{display:grid;grid-template-columns:300px minmax(0,1fr);min-height:100vh}.sidebar{height:100vh;position:sticky;top:0;overflow-y:auto;padding:24px 20px;border-right:1px solid var(--line);background:linear-gradient(180deg,var(--surface),var(--bg))}.brand{display:flex;align-items:center;gap:12px;color:var(--text);text-decoration:none}.brand-mark{display:grid;place-items:center;width:50px;height:50px;border-radius:15px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#07111f;font-weight:900}.brand small,.brand strong{display:block}.brand small{color:var(--muted);font-size:.72rem}.version{margin:16px 0;padding:7px;border:1px solid var(--line);border-radius:999px;text-align:center;color:var(--good);font-size:.78rem}.search-box span{display:block;font-size:.74rem;color:var(--muted);margin-bottom:5px}.search-box input{width:100%;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--surface2);color:var(--text)}.search-results{margin-top:8px;padding:6px;border:1px solid var(--line);border-radius:10px;background:var(--surface);box-shadow:var(--shadow)}.search-results a{display:block;padding:8px;border-radius:7px;text-decoration:none}.search-results a:hover{background:var(--surface2)}.search-results strong,.search-results small{display:block}.search-results small{color:var(--muted)}nav{margin-top:22px}.nav-link{display:block;padding:9px;color:var(--muted);text-decoration:none;border-left:2px solid transparent;border-radius:0 8px 8px 0}.nav-link:hover,.nav-link.active{color:var(--text);background:var(--surface2);border-left-color:var(--accent)}main{min-width:0}.topbar{height:58px;position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;padding:0 28px;border-bottom:1px solid var(--line);background:var(--bg)}.breadcrumb{color:var(--muted);font-size:.84rem}.icon-button{padding:7px 10px;border:1px solid var(--line);border-radius:9px;background:var(--surface);color:var(--text);cursor:pointer}#menu-button{display:none}.content{max-width:1080px;margin:auto;padding:52px 48px 80px}.content h1{font-size:clamp(2.2rem,5vw,4.3rem);line-height:1.04;letter-spacing:-.04em}.content h2{margin-top:46px;border-top:1px solid var(--line);padding-top:18px}.content p,.content li{color:var(--muted)}.lead{font-size:1.12rem;max-width:820px}.eyebrow{color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.16em;font-size:.75rem}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:25px}.button{display:inline-block;padding:11px 15px;border:1px solid var(--line);border-radius:10px;text-decoration:none}.button.primary{background:var(--accent);color:#07111f;border-color:var(--accent);font-weight:800}.two-column,.three-column,.branch-grid,.workflow-grid{display:grid;gap:16px}.two-column{grid-template-columns:repeat(2,1fr)}.three-column{grid-template-columns:repeat(3,1fr)}.branch-grid{grid-template-columns:repeat(4,1fr)}.workflow-grid{grid-template-columns:repeat(2,1fr)}.feature,.value-card,.branch-card,.workflow,.api-card{padding:20px;border:1px solid var(--line);border-radius:16px;background:var(--surface);box-shadow:var(--shadow)}.feature-icon{font-size:2rem;color:var(--accent)}.status{display:inline-block;padding:3px 8px;border-radius:999px;text-transform:uppercase;font-size:.65rem;font-weight:800}.status.active{background:rgba(132,243,161,.13);color:var(--good)}.status.planned{background:rgba(128,171,255,.13);color:var(--accent2)}.notice{padding:20px;border:1px solid var(--line);border-left:4px solid var(--warning);border-radius:12px;background:var(--surface)}pre{overflow-x:auto;padding:18px;border:1px solid var(--line);border-radius:13px;background:var(--code)}code{font-family:"Cascadia Code",Consolas,monospace}.api-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:13px}.module-section{margin:42px 0}.api-card h3{overflow-wrap:anywhere;margin:8px 0}.kind{padding:3px 7px;border-radius:999px;background:rgba(99,226,208,.12);color:var(--accent);font-size:.65rem;font-weight:800;text-transform:uppercase}footer{max-width:1080px;margin:auto;padding:0 48px 40px;color:var(--muted);font-size:.82rem}@media(max-width:950px){.shell{grid-template-columns:1fr}.sidebar{position:fixed;z-index:20;width:min(330px,88vw);transform:translateX(-105%);transition:transform .2s;box-shadow:var(--shadow)}.nav-open .sidebar{transform:translateX(0)}#menu-button{display:block}.content{padding:38px 24px 70px}.branch-grid,.three-column{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.two-column,.three-column,.branch-grid,.workflow-grid{grid-template-columns:1fr}}
'''

_SCRIPT = r'''(function(){const root=document.documentElement;const saved=localStorage.getItem("iq4-doc-theme");if(saved)root.dataset.theme=saved;const theme=document.getElementById("theme-button");if(theme)theme.addEventListener("click",()=>{const next=root.dataset.theme==="light"?"dark":"light";root.dataset.theme=next;localStorage.setItem("iq4-doc-theme",next)});const menu=document.getElementById("menu-button");if(menu)menu.addEventListener("click",()=>document.body.classList.toggle("nav-open"));const input=document.getElementById("search-input");const results=document.getElementById("search-results");const index=window.IQ4_DOCUMENTATION_SEARCH||[];if(!input||!results)return;input.addEventListener("input",()=>{const q=input.value.trim().toLowerCase();if(q.length<2){results.hidden=true;results.innerHTML="";return}const matches=index.filter(item=>(item.title+" "+item.text).toLowerCase().includes(q)).slice(0,12);results.innerHTML=matches.length?matches.map(item=>'<a href="'+item.url+'"><strong>'+item.title+'</strong><small>'+item.url+'</small></a>').join(""):'<div>No matching page or symbol.</div>';results.hidden=false})})();
'''


__all__ = [
    "DocumentationPortalResult",
    "build_documentation_portal",
    "documentation_payload",
    "open_documentation_portal",
]
