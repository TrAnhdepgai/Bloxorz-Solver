"""A* phải cho CÙNG chi phí với UCS (heuristic admissible) trên toàn bộ bộ benchmark.

Tự bỏ qua cho tới khi A* được đăng ký trong solvers/__init__.py (SOLVERS["astar"]).
Chạy lại sau MỖI lần đổi hàm cost hoặc heuristic: heuristic phải còn admissible với hàm cost mới.
"""
import pytest

from engine import Engine
from engine.catalog import load_catalog
from solvers import SOLVERS, ucs
from solvers.base import replay_path

BENCH = load_catalog(benchmark_only=True)


@pytest.mark.skipif("astar" not in SOLVERS, reason="A* chưa được đăng ký")
@pytest.mark.parametrize("entry", BENCH, ids=lambda e: e["id"])
def test_astar_cost_equals_ucs_cost(entry):
    problem = Engine(entry["data"])
    reference = ucs(problem)
    out = SOLVERS["astar"](problem)
    assert out.path is not None and replay_path(problem, out.path)
    assert out.cost == pytest.approx(reference.cost), "A* đắt hơn UCS: heuristic có thể không admissible"
