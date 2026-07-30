"""Generate the three flagship iQuant4 developer-alpha artifacts."""

from pathlib import Path

from iq4comm.showcase import run_alpha_showcase


if __name__ == "__main__":
    manifest = run_alpha_showcase(
        Path("showcase_output"),
        include_tomography=True,
    )
    print("iQuant4 showcase completed.")
    print(manifest["manifest_path"])
