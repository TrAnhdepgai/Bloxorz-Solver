"""Hàm cost đề xuất cho UCS / A*.

Chữ ký đúng hook của Engine: cost_fn(state, action, next_state) -> float (luôn > 0).

Quy ước:
    - Khối đang tách đôi (state.split != None): mỗi nước (một khối nhỏ đi 1 ô, hoặc SWAP) = 1.0
    - Khối nguyên, ĐỔI tư thế (đứng <-> nằm): TIP_COST = 2.0
    - Khối nguyên, GIỮ tư thế (lăn khi đang nằm): ROLL_COST = 1.0

Bất biến mà heuristic của A* dựa vào (xem solvers/astar.py):
    mỗi bước tốn ít nhất `cost_per_cell` x (số ô Manhattan mà bước đó rút ngắn được).
    Nước đổi tư thế rút ngắn tối đa 2 ô, tốn 2.0; nước còn lại tối đa 1 ô, tốn 1.0
    => weighted_cost.cost_per_cell = 1.0. Với uniform_cost (mọi bước 1.0, rút ngắn tối đa 2 ô) là 0.5.
    Hàm cost không khai báo cost_per_cell thì A* dùng h = 0 (thành UCS, vẫn đúng).
    Đổi giá trị ở đây thì phải chạy lại tests/test_heuristic.py.
"""

ROLL_COST = 1.0
TIP_COST = 2.0
SPLIT_STEP_COST = 1.0
SWAP_COST = 1.0


def weighted_cost(state, action, next_state):
    """Phải kiểm tra split TRƯỚC: khi tách đôi, orient chỉ là giá trị giữ chỗ 'S'."""
    if state.split is not None:
        return SWAP_COST if action == "SWAP" else SPLIT_STEP_COST
    return TIP_COST if state.orient != next_state.orient else ROLL_COST


def uniform_cost(state, action, next_state):
    return 1.0


weighted_cost.cost_per_cell = 1.0
uniform_cost.cost_per_cell = 0.5

COST_FUNCTIONS = {"uniform": uniform_cost, "weighted": weighted_cost}