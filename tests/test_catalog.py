"""Kiểm tra bộ màn chơi hợp nhất: định dạng, bộ benchmark cố định, optimal_moves khớp BFS, cầu nối GUI."""
import json

import pytest

import engine.engine as engine_module
from engine import Engine
from engine.catalog import GROUPS, LEVEL_DIR, describe, dump_level, load_catalog, to_gui_level, validate
from engine.level import LevelError
from solvers import bfs, ucs
from solvers.base import replay_path

ALL = load_catalog()
BENCH = load_catalog(benchmark_only=True)


def test_catalog_not_empty_and_ids_unique():
    assert ALL and len({e["id"] for e in ALL}) == len(ALL)


@pytest.mark.parametrize("entry", ALL, ids=lambda e: e["id"])
def test_file_name_matches_group(entry):
    assert entry["id"].startswith(entry["data"]["group"] + "_")


def test_benchmark_has_four_groups_of_three():
    for group in GROUPS:
        in_group = [e for e in BENCH if e["data"]["group"] == group]
        assert len(in_group) == 3, f"nhóm {group} có {len(in_group)} màn benchmark (cần 3)"


def test_each_group_has_a_large_level():
    """Mỗi nhóm có ít nhất một màn 'đủ lớn' để thấy khác biệt giữa các thuật toán."""
    for group in GROUPS:
        largest = max(describe(e["data"])["floor"] for e in BENCH if e["data"]["group"] == group)
        assert largest >= 75, f"nhóm {group}: màn lớn nhất chỉ có {largest} ô sàn"


def test_benchmark_covers_every_mechanic():
    data = [e["data"] for e in BENCH]
    kinds = {sw["type"] for d in data for sw in d.get("switches", [])}
    modes = {(sw["mode"], sw.get("set")) for d in data for sw in d.get("switches", []) if sw.get("targets")}
    assert kinds == {"soft", "heavy", "split"}
    assert {"toggle", "permanent"} <= {m for m, _ in modes}
    assert any(d.get("fragile") for d in data if d["group"] == "fragile")
    assert any(d.get("fragile") and d.get("switches") for d in data if d["group"] == "combined")


@pytest.mark.parametrize("entry", BENCH, ids=lambda e: e["id"])
def test_benchmark_level_solvable_and_optimal_moves_correct(entry):
    problem = Engine(entry["data"])
    outcome = bfs(problem)
    assert outcome.path is not None, "màn benchmark phải giải được"
    assert replay_path(problem, outcome.path)
    assert entry["data"]["optimal_moves"] == len(outcome.path), \
        "optimal_moves lệch BFS -> chạy: python compute_optimal.py"
    # UCS tối ưu theo chi phí: không đắt hơn đường đi BFS (bằng nhau khi mọi nước cost 1)
    assert ucs(problem).cost <= sum(engine_module.COST[a] for a in outcome.path) + 1e-9


@pytest.mark.parametrize("entry", [e for e in ALL if not e["data"].get("benchmark")], ids=lambda e: e["id"])
def test_campaign_levels_optimal_moves_correct(entry):
    out = bfs(Engine(entry["data"]))
    assert out.path is not None and entry["data"]["optimal_moves"] == len(out.path)


@pytest.mark.parametrize("entry", ALL, ids=lambda e: e["id"])
def test_dump_roundtrip_is_stable(entry):
    """File trên đĩa đúng bằng định dạng chuẩn -> compute_optimal.py ghi lại không tạo diff thừa."""
    assert entry["path"].read_text(encoding="utf-8") == dump_level(entry["data"])
    assert json.loads(dump_level(entry["data"])) == entry["data"]


@pytest.mark.parametrize("entry", ALL, ids=lambda e: e["id"])
def test_gui_conversion_keeps_geometry(entry):
    d, gui = entry["data"], to_gui_level(entry)
    rows = gui["grid"]
    assert rows[d["start"][0]][d["start"][1]] == "S" and rows[d["goal"][0]][d["goal"][1]] == "G"
    assert sum(r.count("S") for r in rows) == 1 and sum(r.count("G") for r in rows) == 1
    assert [r.replace("S", "O").replace("G", "O").replace("O", "#") for r in rows] == d["grid"]
    assert gui["optimal_moves"] == d["optimal_moves"] and gui["name"] == d["name"]


@pytest.mark.parametrize("patch", [
    {"group": "nope"}, {"name": ""}, {"difficulty": "1"}, {"optimal_moves": -3}, {"optimal_moves": "7"},
])
def test_validate_rejects_bad_metadata(patch):
    good = dict(ALL[0]["data"])
    validate(good)
    with pytest.raises(LevelError):
        validate({**good, **patch})
