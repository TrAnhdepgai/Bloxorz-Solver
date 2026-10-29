import csv

import pytest

pytest.importorskip("matplotlib")
import plot_results  # noqa: E402

FIELDS = ["solver", "level", "found", "valid", "length", "cost", "expanded", "time_s", "peak_mem_kb", "path",
          "group", "optimal_moves", "name", "rows", "cols", "bridge_cells", "fragile_cells", "switch_types"]


def write_csv(path, with_memory=True):
    rows = []
    for level, group, rows_n, cols, bridges, fragile in (
        ("basic_01_a_b", "basic", 4, 7, 0, 0),
        ("fragile_01_c_d", "fragile", 5, 9, 0, 3),
    ):
        for solver, length in (("bfs", 5), ("dfs", 20)):
            rows.append(dict(
                solver=solver, level=level, found=True, valid=True, length=length, cost=float(length),
                expanded=10, time_s=0.001, peak_mem_kb=12.5 if with_memory else "nan",
                path="RR", group=group, optimal_moves=5, name=level, rows=rows_n, cols=cols,
                bridge_cells=bridges, fragile_cells=fragile, switch_types="",
            ))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


@pytest.mark.parametrize("with_memory", [True, False])
def test_plot_script_writes_report_artifacts(tmp_path, monkeypatch, with_memory):
    write_csv(tmp_path / "r.csv", with_memory)
    fig = tmp_path / "fig"
    tables = tmp_path / "tab"
    monkeypatch.setattr("sys.argv", [
        "plot_results.py", "--csv", str(tmp_path / "r.csv"), "--out", str(fig), "--tables", str(tables),
    ])
    plot_results.main()
    names = {p.name for p in fig.glob("*.pdf")}
    expect = {"fig_expanded.pdf", "fig_time.pdf", "fig_length.pdf", "fig_scaling.pdf"}
    if with_memory:
        expect.add("fig_memory.pdf")
    assert names == expect
    assert not list(fig.glob("*.png"))
    tier = (tables / "results_by_tier.tex").read_text(encoding="utf-8")
    assert "Giải" in tier and "BFS" in tier and "1/1" in tier and "10.0" in tier and "1.00" in tier
    testset = (tables / "testset.tex").read_text(encoding="utf-8")
    assert "$4 \\times 7$" in testset
    assert "Bridge" in testset and "Tối ưu" in testset
    detail = (tables / "results_detail.tex").read_text(encoding="utf-8")
    assert "basic\\_01\\_a\\_b" in detail
    if with_memory:
        assert "12.5" in tier
    else:
        assert "fig_memory.pdf" not in names


def test_tier_mean_skips_invalid_replay():
    rows = plot_results.read_results  # placemarker to keep import used if rewritten
    assert rows
    parsed = [{
        "solver": "bfs", "level": "a", "group": "basic", "found": True, "valid": True,
        "expanded": 10.0, "time_s": 1.0, "peak_mem_kb": 1.0, "length": 4.0, "cost": 4.0,
        "optimal_moves": 4.0, "rows": 1, "cols": 1, "bridge_cells": 0, "fragile_cells": 0,
        "switch_types": "", "name": "",
    }, {
        "solver": "bfs", "level": "b", "group": "basic", "found": True, "valid": False,
        "expanded": 1000.0, "time_s": 9.0, "peak_mem_kb": 9.0, "length": 99.0, "cost": 99.0,
        "optimal_moves": 4.0, "rows": 1, "cols": 1, "bridge_cells": 0, "fragile_cells": 0,
        "switch_types": "", "name": "",
    }]
    mean, solved, total = plot_results.mean_on_solved(parsed, "basic", "bfs", "expanded")
    assert (mean, solved, total) == (10.0, 1, 2)
