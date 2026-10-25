import csv

import pytest

pytest.importorskip("matplotlib")
import plot_results  # noqa: E402

FIELDS = ["solver", "level", "found", "valid", "length", "cost", "expanded", "time_s", "peak_mem_kb", "path",
          "group", "optimal_moves"]


def write_csv(path, with_memory=True):
    rows = []
    for level, group in (("basic_01_a_b", "basic"), ("fragile_01_c_d", "fragile")):
        for solver, length in (("bfs", 5), ("dfs", 20)):
            rows.append(dict(solver=solver, level=level, found=True, valid=True, length=length, cost=length,
                             expanded=10, time_s=0.001, peak_mem_kb=12.5 if with_memory else "nan",
                             path="RR", group=group, optimal_moves=5))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


@pytest.mark.parametrize("with_memory,count", [(True, 6), (False, 5)])
def test_plot_script_writes_figures_and_tables(tmp_path, monkeypatch, with_memory, count):
    write_csv(tmp_path / "r.csv", with_memory)
    monkeypatch.setattr("sys.argv", ["plot_results.py", "--csv", str(tmp_path / "r.csv"), "--out", str(tmp_path / "fig")])
    plot_results.main()
    assert len(list((tmp_path / "fig").glob("*.png"))) == count       # 5 hình riêng + overview (bỏ hình bộ nhớ nếu không đo)
    assert "| Màn |" in (tmp_path / "fig" / "results_tables.md").read_text(encoding="utf-8")
    assert "BFS" in (tmp_path / "fig" / "summary_vs_bfs.md").read_text(encoding="utf-8")
