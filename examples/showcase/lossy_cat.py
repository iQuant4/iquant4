"""Generate loss-degraded even-cat Wigner functions and metrics."""

from pathlib import Path

from iq4comm.showcase import run_lossy_cat_showcase


if __name__ == "__main__":
    result = run_lossy_cat_showcase(Path("showcase_output"))
    print(result.json_path)
    print(result.figure_path)
