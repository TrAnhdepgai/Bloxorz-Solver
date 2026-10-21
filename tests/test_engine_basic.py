import json
import pytest
from engine import Engine, State, SplitState


def make_engine(tmp_path, grid, start, goal, **extra):
    data = {"grid": grid, "start": list(start), "goal": list(goal), **extra}
    p = tmp_path / "level.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return Engine(str(p))


@pytest.fixture
def open_engine(tmp_path):
    # sàn 3x6 không có void, start (1,1), goal (1,4)
    return make_engine(tmp_path, ["######"] * 3, (1, 1), (1, 4))


def actions_of(engine, state):
    return [a for a, _, _ in engine.get_successors(state)]


# ---------- initial state ----------
def test_initial_state(open_engine):
    s = open_engine.initial_state()
    assert (s.orient, s.row, s.col) == ("S", 1, 1)
    assert s.bridges == frozenset()
    assert s.split is None


# ---------- nước đi bất hợp lệ ----------
def test_out_of_board_is_removed(open_engine):
    corner = State("S", 0, 0, frozenset())
    # U -> V(-2,0) ra ngoài, L -> H(0,-2) ra ngoài
    assert actions_of(open_engine, corner) == ["D", "R"]


def test_void_is_removed(tmp_path):
    e = make_engine(tmp_path, ["####", "#.##", "####"], (1, 0), (2, 3))
    s = State("S", 1, 0, frozenset())
    # R -> H(1,1) chiếm (1,1) là void
    assert "R" not in actions_of(e, s)


# ---------- thắng ----------
def test_goal_only_when_standing_on_goal(open_engine):
    b = frozenset()
    assert open_engine.is_goal(State("S", 1, 4, b)) is True
    assert open_engine.is_goal(State("S", 1, 3, b)) is False
    # nằm vắt qua goal (1,4) thì không thắng
    assert open_engine.is_goal(State("H", 1, 3, b)) is False
    assert open_engine.is_goal(State("H", 1, 4, b)) is False
    assert open_engine.is_goal(State("V", 0, 4, b)) is False
    assert open_engine.is_goal(State("V", 1, 4, b)) is False


def test_split_cube_cannot_win(open_engine):
    sp = SplitState(((1, 4), (0, 0)), 0)
    s = State("S", 0, 0, frozenset(), sp)
    assert open_engine.is_goal(s) is False


# ---------- tính thuần và xác định ----------
def test_successors_pure_and_deterministic(open_engine):
    s = State("S", 1, 1, frozenset())
    before = State("S", 1, 1, frozenset())
    first = open_engine.get_successors(s)
    second = open_engine.get_successors(s)
    assert s == before          # state đầu vào không đổi
    assert first == second      # cùng kết quả, cùng thứ tự


def test_successor_order_is_UDLR(open_engine):
    s = State("S", 1, 1, frozenset())
    order = "UDLR"
    acts = actions_of(open_engine, s)
    assert acts == sorted(acts, key=order.index)


def test_successor_cost_default(open_engine):
    for _, _, cost in open_engine.get_successors(open_engine.initial_state()):
        assert cost == 1.0


def test_round_trip_R_then_L(open_engine):
    s0 = open_engine.initial_state()
    nxt = {a: s for a, s, _ in open_engine.get_successors(s0)}
    back = {a: s for a, s, _ in open_engine.get_successors(nxt["R"])}
    assert back["L"] == s0


# ---------- hash / so sánh State ----------
def test_states_differ_by_bridges():
    a = State("S", 1, 1, frozenset())
    b = State("S", 1, 1, frozenset({"B1"}))
    assert a != b
    assert len({a, b}) == 2


def test_equal_states_hash_equal():
    a = State("S", 1, 1, frozenset({"B1"}))
    b = State("S", 1, 1, frozenset({"B1"}))
    assert a == b and hash(a) == hash(b)
    assert len({a, b}) == 1