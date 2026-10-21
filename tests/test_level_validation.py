import pytest
from engine.level import LevelError

GRID = ["######"] * 3
BR = {"B1": [[1, 4]]}


def build(make_engine, **extra):
    extra.setdefault("grid", GRID)
    extra.setdefault("start", (1, 1))
    extra.setdefault("goal", (1, 4))
    return make_engine(**extra)


@pytest.mark.parametrize("extra", [
    dict(fragile=[[1, 1]]),                                                   # start fragile
    dict(fragile=[[1, 4]]),                                                   # goal fragile
    dict(switches=[{"type": "soft", "targets": []}]),                         # thiếu pos
    dict(switches=[{"pos": [1, 2]}]),                                         # thiếu type
    dict(switches=[{"pos": [1, 2], "type": "weird"}]),                        # type sai
    dict(switches=[{"pos": [1, 2], "type": "soft", "targets": ["X"]}], bridges=BR),   # cầu không tồn tại
    dict(switches=[{"pos": [1, 2], "type": "soft", "targets": ["B1"], "mode": "x"}], bridges=BR),
    dict(switches=[{"pos": [1, 2], "type": "heavy", "targets": ["B1"], "mode": "permanent"}], bridges=BR),
    dict(switches=[{"pos": [1, 2], "type": "split"}]),                        # thiếu teleport
    dict(switches=[{"pos": [1, 2], "type": "split", "teleport": [[0, 0], [0, 1]]}]),  # liền kề
    dict(switches=[{"pos": [1, 2], "type": "split", "teleport": [[0, 0], [0, 0]]}]),  # trùng
    dict(switches=[{"pos": [9, 9], "type": "soft"}]),                         # ngoài bảng
    dict(switches=[{"pos": "abc", "type": "soft"}]),                          # toạ độ rác
])
def test_invalid_level_raises_levelerror(make_engine, extra):
    with pytest.raises(LevelError):
        build(make_engine, **extra)


def test_valid_full_level_loads(make_engine):
    e = build(make_engine, bridges=BR, fragile=[[0, 2]], switches=[
        {"pos": [1, 2], "type": "soft", "targets": ["B1"], "mode": "toggle"},
        {"pos": [2, 2], "type": "heavy", "targets": ["B1"], "mode": "permanent", "set": "open"},
        {"pos": [0, 0], "type": "split", "teleport": [[2, 1], [2, 5]]},
    ])
    assert len(e.switches) == 3