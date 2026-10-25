import glob
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import Engine, State  # noqa: E402
from solvers import bfs, dfs, ids, ucs  # noqa: E402
from solvers.base import replay_path  # noqa: E402
import engine.engine as engine_module  # noqa: E402

LEVEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")   # màn nhỏ dành cho unit test
ALL_LEVELS = sorted(glob.glob(os.path.join(LEVEL_DIR, "*.json")))
SOLVABLE = [p for p in ALL_LEVELS if "unsolvable" not in p]
UNSOLVABLE = [p for p in ALL_LEVELS if "unsolvable" in p]
SOLVERS = [bfs, dfs, ids, ucs]


def path_cost(path):
    """Tổng chi phí của một đường đi theo bảng COST hiện hành (đúng cả khi hàm cost không đều)."""
    return sum(engine_module.COST[a] for a in path)


@pytest.mark.parametrize("path", SOLVABLE)
@pytest.mark.parametrize("solver", SOLVERS, ids=lambda s: s.__name__)
def test_solver_finds_valid_path(solver, path):
    problem = Engine(path)
    outcome = solver(problem)
    assert outcome.path is not None
    assert replay_path(problem, outcome.path)           # đi theo path trên engine thì thắng
    assert outcome.cost == pytest.approx(path_cost(outcome.path))


@pytest.mark.parametrize("path", SOLVABLE)
def test_bfs_and_ids_same_length(path):
    problem = Engine(path)
    assert len(bfs(problem).path) == len(ids(problem).path)   # cùng tối ưu theo SỐ NƯỚC; lệch nhau = có bug


@pytest.mark.parametrize("path", SOLVABLE)
def test_ucs_cost_not_worse_than_bfs_path(path):
    """UCS tối ưu theo CHI PHÍ: không bao giờ đắt hơn đường đi của BFS. Chi phí đều thì hai bên bằng nhau."""
    problem = Engine(path)
    assert ucs(problem).cost <= path_cost(bfs(problem).path) + 1e-9


@pytest.mark.parametrize("path", SOLVABLE)
def test_dfs_not_shorter_than_bfs(path):
    problem = Engine(path)
    assert len(dfs(problem).path) >= len(bfs(problem).path)


@pytest.mark.parametrize("path", UNSOLVABLE)
@pytest.mark.parametrize("solver", SOLVERS, ids=lambda s: s.__name__)
def test_unsolvable_returns_none(solver, path):
    outcome = solver(Engine(path))
    assert outcome.path is None and outcome.cost is None


def test_ucs_prefers_cheaper_path():
    """UCS phải theo cost, không theo số bước: giả lập chi phí 'L' đắt thì tránh đi trái."""
    old = dict(engine_module.COST)
    try:
        engine_module.COST.update({"L": 10.0})
        problem = Engine(SOLVABLE[0])
        out = ucs(problem)
        assert out.cost == pytest.approx(sum(engine_module.COST[a] for a in out.path))
    finally:
        engine_module.COST.update(old)


def test_state_hashable_and_bridges_matter():
    a = State("S", 1, 1, frozenset())
    b = State("S", 1, 1, frozenset({"B1"}))
    assert a != b
    assert len({a, b, State("S", 1, 1, frozenset())}) == 2
