from engine import State, SplitState

B = frozenset()
GRID = ["########"] * 3
SPLIT_SW = {"pos": [1, 3], "type": "split", "teleport": [[0, 1], [2, 6]]}


def succ(e, s):
    return {a: n for a, n, _ in e.get_successors(s)}


def split_state(c0, c1, active=0, bridges=B):
    return State("S", 0, 0, bridges, SplitState((c0, c1), active))


def test_standing_on_split_switch_splits(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    assert succ(e, State("H", 1, 1, B))["R"] == split_state((0, 1), (2, 6))


def test_lying_on_split_switch_does_not_split(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    n = succ(e, State("S", 1, 2, B))["R"]          # H(1,3)
    assert n.split is None and n.orient == "H"


def test_split_actions_and_order(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    acts = [a for a, _, _ in e.get_successors(split_state((0, 1), (2, 6)))]
    assert acts == ["D", "L", "R", "SWAP"]          # U ra ngoài bảng; SWAP luôn có cuối


def test_swap_toggles_active_only(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    s = split_state((0, 1), (2, 6), active=0)
    sw = succ(e, s)["SWAP"]
    assert sw == split_state((0, 1), (2, 6), active=1)
    assert succ(e, sw)["SWAP"] == s


def test_swap_cost_configurable_default(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    costs = {a: c for a, _, c in e.get_successors(split_state((0, 1), (2, 6)))}
    assert costs["SWAP"] == 1.0


def test_move_only_active_cube(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    s = split_state((0, 1), (2, 6), active=1)
    assert succ(e, s)["L"] == split_state((0, 1), (2, 5), active=1)


def test_merge_horizontal(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    assert succ(e, split_state((1, 1), (1, 3)))["R"] == State("H", 1, 2, B)


def test_merge_vertical(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    s = split_state((0, 2), (2, 2))
    assert succ(e, s)["D"] == State("V", 1, 2, B)


def test_cube_can_stand_on_fragile(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), fragile=[[1, 2]], switches=[SPLIT_SW])
    assert "R" in succ(e, split_state((1, 1), (2, 6)))


def test_cube_cannot_enter_void(make_engine):
    sw = {"pos": [1, 3], "type": "split", "teleport": [[2, 1], [2, 6]]}
    e = make_engine(["#.######", "########", "########"], (1, 1), (1, 7), switches=[sw])
    assert "L" not in succ(e, split_state((0, 2), (2, 6)))   # (0,1) là void


def test_soft_fires_for_cube_but_heavy_does_not(make_engine):
    sws = [{"pos": [1, 2], "type": "soft", "targets": ["B1"], "mode": "toggle"},
           {"pos": [1, 3], "type": "heavy", "targets": ["B1"], "mode": "permanent", "set": "open"}]
    e = make_engine(["########", "########", "########"], (1, 1), (1, 7),
                    bridges={"B1": [[2, 5]]}, switches=sws)
    on_soft = succ(e, split_state((1, 1), (2, 7)))["R"]
    assert on_soft.bridges == frozenset({"B1"})
    on_heavy = succ(e, split_state((1, 2), (2, 7)))["R"]
    assert on_heavy.bridges == B


def test_split_cube_is_not_goal(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    assert e.is_goal(split_state((1, 7), (0, 0))) is False


def test_split_states_hashable_and_pure(make_engine):
    e = make_engine(GRID, (1, 1), (1, 7), switches=[SPLIT_SW])
    s = split_state((0, 1), (2, 6))
    assert e.get_successors(s) == e.get_successors(s)
    assert s == split_state((0, 1), (2, 6))
    assert len({s, split_state((0, 1), (2, 6)), split_state((0, 1), (2, 6), 1)}) == 2