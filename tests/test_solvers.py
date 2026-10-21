import glob
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fake_engine import TRANSITIONS, Engine, State  # noqa: E402
from solvers import bfs, dfs, ids, ucs  # noqa: E402
from solvers.base import replay_path  # noqa: E402

LEVEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "levels")
ALL_LEVELS = sorted(glob.glob(os.path.join(LEVEL_DIR, "*.json")))
SOLVABLE = [p for p in ALL_LEVELS if "unsolvable" not in p]
UNSOLVABLE = [p for p in ALL_LEVELS if "unsolvable" in p]
SOLVERS = [bfs, dfs, ids, ucs]


@pytest.mark.parametrize("path", SOLVABLE)
@pytest.mark.parametrize("solver", SOLVERS, ids=lambda s: s.__name__)
def test_solver_finds_valid_path(solver, path):
    problem = Engine(path)
    outcome = solver(problem)
    assert outcome.path is not None
    assert replay_path(problem, outcome.path)           # đi theo path trên engine thì thắng
    assert outcome.cost == pytest.approx(len(outcome.path))   # cost = số bước khi mỗi bước cost 1


@pytest.mark.parametrize("path", SOLVABLE)
def test_bfs_ids_ucs_same_length(path):
    problem = Engine(path)
    lengths = {s.__name__: len(s(problem).path) for s in (bfs, ids, ucs)}
    assert len(set(lengths.values())) == 1, lengths      # lệch nhau = có bug


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
    import fake_engine
    old = dict(fake_engine.COST)
    try:
        fake_engine.COST.update({"L": 10.0})
        problem = Engine(SOLVABLE[0])
        out = ucs(problem)
        assert out.cost == pytest.approx(sum(fake_engine.COST[a] for a in out.path))
    finally:
        fake_engine.COST.update(old)


def test_transition_table_matches_contract():
    expected = {
        ("S", "U"): ("V", -2, 0), ("S", "D"): ("V", 1, 0), ("S", "L"): ("H", 0, -2), ("S", "R"): ("H", 0, 1),
        ("H", "U"): ("H", -1, 0), ("H", "D"): ("H", 1, 0), ("H", "L"): ("S", 0, -1), ("H", "R"): ("S", 0, 2),
        ("V", "U"): ("S", -1, 0), ("V", "D"): ("S", 2, 0), ("V", "L"): ("V", 0, -1), ("V", "R"): ("V", 0, 1),
    }
    for (o, a), val in expected.items():
        assert TRANSITIONS[o][a] == val


def test_state_hashable_and_bridges_matter():
    a = State("S", 1, 1, frozenset())
    b = State("S", 1, 1, frozenset({"B1"}))
    assert a != b
    assert len({a, b, State("S", 1, 1, frozenset())}) == 2
