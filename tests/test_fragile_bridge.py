from engine import State

B = frozenset()


def actions(e, s):
    return [a for a, _, _ in e.get_successors(s)]


def test_standing_on_fragile_is_removed(make_engine):
    e = make_engine(["####"] * 3, (1, 0), (1, 3), fragile=[[1, 2]])
    # H(1,0) chiếm (1,0),(1,1); R -> S(1,2) đứng trên fragile => bỏ
    assert "R" not in actions(e, State("H", 1, 0, B))


def test_lying_across_fragile_is_valid(make_engine):
    e = make_engine(["####"] * 3, (1, 0), (1, 3), fragile=[[1, 2]])
    # S(1,0) R -> H(1,1) chiếm (1,1),(1,2): nằm vắt qua fragile => hợp lệ
    assert "R" in actions(e, State("S", 1, 0, B))


def test_closed_bridge_is_void(make_engine):
    e = make_engine(["####"] * 3, (1, 0), (1, 3), bridges={"B1": [[1, 2], [1, 3]]})
    assert "R" not in actions(e, State("S", 1, 0, B))      # H(1,1) chiếm (1,2) cầu đóng


def test_open_bridge_is_walkable(make_engine):
    e = make_engine(["####"] * 3, (1, 0), (1, 3), bridges={"B1": [[1, 2], [1, 3]]})
    assert "R" in actions(e, State("S", 1, 0, frozenset({"B1"})))


def test_initial_open_bridges(make_engine):
    e = make_engine(["####"] * 3, (1, 0), (1, 3),
                    bridges={"B1": [[1, 2]]}, bridges_initial_open=["B1"])
    assert e.initial_state().bridges == frozenset({"B1"})