"""Generate a quick sign-free Fock-state tomography artifact set."""

from pathlib import Path

from iq4comm.showcase import run_sign_free_tomography_showcase


if __name__ == "__main__":
    result = run_sign_free_tomography_showcase(
        Path("showcase_output"),
        require_cvxpy=True,
    )
    print(result.json_path)
    print(result.figure_path)
