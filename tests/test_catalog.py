"""Kiểm tra bộ màn chơi hợp nhất: định dạng, bộ benchmark cố định, optimal_moves khớp BFS, cầu nối GUI."""
import json

import pytest

import engine.engine as engine_module
from engine import Engine
from engine.catalog import GROUPS, describe, dump_level, load_catalog, to_gui_level, validate
from engine.level import LevelError
from solvers import bfs, ucs
from solvers.base import replay_path

ALL = load_catalog()
BENCH = load_catalog(benchmark_only=True)

# Màn 01–05 là tutorial basic (không đưa vào báo cáo). Từ difficulty 6 trở đi đều là benchmark.
# Không còn đúng 3 màn/nhóm: basic chỉ lấy 3 màn khó, ba nhóm kia lấy cả chiến dịch.
BENCHMARK_COUNTS = {"basic": 3, "fragile": 5, "switch": 8, "combined": 6}
# Ô sàn của màn benchmark lớn nhất mỗi nhóm (catalog hiện tại, không phải ngưỡng 75 cũ).
MIN_LARGEST_FLOOR = {"basic": 50, "fragile": 75, "switch": 50, "combined": 75}


def test_catalog_not_empty_and_ids_unique():
    assert ALL and len({e["id"] for e in ALL}) == len(ALL)
    assert [e["data"]["difficulty"] for e in ALL] == list(range(1, len(ALL) + 1))


@pytest.mark.parametrize("entry", ALL, ids=lambda e: e["id"])
def test_file_name_matches_group(entry):
    """Tên file: NN_<chủ đề>_<slug>, NN trùng difficulty.
    Chủ đề là group, trừ màn tách khối (19–21) ghi `split` nhưng vẫn thuộc group `switch`."""
    group = entry["data"]["group"]
    diff = entry["data"]["difficulty"]
    prefix = f"{diff:02d}_"
    assert entry["id"].startswith(prefix), entry["id"]
    topic = entry["id"][len(prefix):].split("_", 1)[0]
    allowed = {group, "split"} if group == "switch" else {group}
    assert topic in allowed, entry["id"]


def test_benchmark_counts_match_catalog():
    got = {group: sum(e["data"]["group"] == group for e in BENCH) for group in GROUPS}
    assert got == BENCHMARK_COUNTS, got
    for entry in ALL:
        ranked = entry["data"]["difficulty"] >= 6
        assert bool(entry["data"].get("benchmark")) is ranked, entry["id"]


def test_each_group_has_a_large_level():
    """Mỗi nhóm có một màn đủ rộng để các thuật toán không cùng một lời giải tầm thường.
    basic/switch khoảng 50 ô; fragile và combined vẫn có màn >= 75 ô."""
    for group, minimum in MIN_LARGEST_FLOOR.items():
        largest = max(describe(e["data"])["floor"] for e in BENCH if e["data"]["group"] == group)
        assert largest >= minimum, f"nhóm {group}: màn lớn nhất chỉ có {largest} ô sàn (cần >= {minimum})"


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
    """File trên đĩa là JSON pretty-print, không byte-khớp dump_level (writer gọn của compute_optimal.py).
    So nội dung đã parse. dump_level phải không mất trường và ghi hai lần ra cùng một chuỗi."""
    raw = entry["path"].read_text(encoding="utf-8")
    assert json.loads(raw) == entry["data"]
    dumped = dump_level(entry["data"])
    assert json.loads(dumped) == entry["data"]
    assert dump_level(json.loads(dumped)) == dumped


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
