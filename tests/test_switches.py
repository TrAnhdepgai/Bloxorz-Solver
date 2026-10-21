import pytest
from engine import State

B = frozenset()
OPEN = frozenset({"B1"})
GRID = ["########", "#####..#", "########"]
BR = {"B1": [[1, 5], [1, 6]]}


def level(make_engine, sw):
    return make_engine(GRID, (1, 1), (1, 7), bridges=BR, switches=[sw])


def succ(e, s):
    return {a: n for a, n, _ in e.get_successors(s)}


SOFT = {"pos": [1, 3], "type": "soft", "targets": ["B1"], "mode": "toggle"}
HEAVY_OPEN = {"pos": [1, 3], "type": "heavy", "targets": ["B1"], "mode": "permanent", "set": "open"}
HEAVY_CLOSE = {"pos": [1, 3], "type": "heavy", "targets": ["B1"], "mode": "permanent", "set": "close"}


def test_soft_triggers_when_standing(make_engine):
    e = level(make_engine, SOFT)
    assert succ(e, State("H", 1, 1, B))["R"] == State("S", 1, 3, OPEN)


def test_soft_triggers_when_lying(make_engine):
    e = level(make_engine, SOFT)
    # S(1,2) R -> H(1,3) chiếm (1,3),(1,4): vẫn kích hoạt
    assert succ(e, State("S", 1, 2, B))["R"] == State("H", 1, 3, OPEN)


def test_toggle_flips_back_and_forth(make_engine):
    e = level(make_engine, SOFT)
    assert succ(e, State("H", 1, 1, B))["R"].bridges == OPEN
    assert succ(e, State("H", 1, 1, OPEN))["R"].bridges == B


def test_move_not_touching_switch_keeps_bridges(make_engine):
    e = level(make_engine, SOFT)
    assert succ(e, State("S", 1, 0, B))["R"].bridges == B   # H(1,1) chiếm (1,1),(1,2): không có công tắc


def test_heavy_ignores_lying_block(make_engine):
    e = level(make_engine, HEAVY_OPEN)
    assert succ(e, State("S", 1, 2, B))["R"] == State("H", 1, 3, B)


def test_heavy_permanent_open(make_engine):
    e = level(make_engine, HEAVY_OPEN)
    assert succ(e, State("H", 1, 1, B))["R"].bridges == OPEN
    assert succ(e, State("H", 1, 1, OPEN))["R"].bridges == OPEN   # giữ nguyên, không đảo


def test_heavy_permanent_close(make_engine):
    e = level(make_engine, HEAVY_CLOSE)
    assert succ(e, State("H", 1, 1, OPEN))["R"].bridges == B
    assert succ(e, State("H", 1, 1, B))["R"].bridges == B


def test_switch_closing_bridge_under_block_removes_move(make_engine):
    # công tắc (1,3) toggle cầu B1 nằm ở (1,4); S(1,2) R -> H(1,3) chiếm (1,3),(1,4)
    # cầu đang mở, nhưng công tắc đóng nó lại => khối rơi => bỏ nước đi
    e = make_engine(GRID, (1, 1), (1, 7), bridges={"B1": [[1, 4]]}, switches=[SOFT])
    assert "R" not in succ(e, State("S", 1, 2, OPEN))


def test_new_states_are_frozensets(make_engine):
    e = level(make_engine, SOFT)
    assert isinstance(succ(e, State("H", 1, 1, B))["R"].bridges, frozenset)


def test_successors_do_not_mutate_state(make_engine):
    e = level(make_engine, SOFT)
    s = State("H", 1, 1, B)
    e.get_successors(s)
    assert s == State("H", 1, 1, B)