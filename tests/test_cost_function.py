from engine import State
from engine.costs import ROLL_COST, SPLIT_STEP_COST, SWAP_COST, TIP_COST, weighted_cost
from engine.state import SplitState

NONE = frozenset()


def test_tip_costs_more_than_roll():
    standing = State("S", 3, 3, NONE)
    lying = State("H", 3, 3, NONE)
    assert weighted_cost(standing, "R", lying) == TIP_COST
    assert weighted_cost(lying, "U", State("H", 2, 3, NONE)) == ROLL_COST
    assert weighted_cost(lying, "R", State("S", 3, 5, NONE)) == TIP_COST


def test_split_state_ignores_placeholder_orient():
    split = State("S", 0, 0, NONE, SplitState(((0, 0), (0, 2)), 0))
    merged = State("H", 0, 0, NONE)
    assert weighted_cost(split, "R", merged) == SPLIT_STEP_COST
    swapped = State("S", 0, 0, NONE, SplitState(((0, 0), (0, 2)), 1))
    assert weighted_cost(split, "SWAP", swapped) == SWAP_COST


def test_all_costs_positive():
    assert min(ROLL_COST, TIP_COST, SPLIT_STEP_COST, SWAP_COST) > 0