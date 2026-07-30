"""Generate optimized receiver-family tables, data, and a BER figure."""

from pathlib import Path

from iq4comm.showcase import run_receiver_family_showcase


if __name__ == "__main__":
    result = run_receiver_family_showcase(Path("showcase_output"))
    print(result.report_path.read_text(encoding="utf-8"))
    print(result.figure_path)
