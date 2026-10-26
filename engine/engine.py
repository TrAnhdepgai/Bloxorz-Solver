from .state import State, SplitState
from .level import load_level

# (orient, action) -> (new_orient, dr, dc)
TRANSITIONS = {
    ('S','U'): ('V',-2, 0), ('S','D'): ('V', 1, 0),
    ('S','L'): ('H', 0,-2), ('S','R'): ('H', 0, 1),
    ('H','U'): ('H',-1, 0), ('H','D'): ('H', 1, 0),
    ('H','L'): ('S', 0,-1), ('H','R'): ('S', 0, 2),
    ('V','U'): ('S',-1, 0), ('V','D'): ('S', 2, 0),
    ('V','L'): ('V', 0,-1), ('V','R'): ('V', 0, 1),
}
ACTIONS = ('U', 'D', 'L', 'R')          # thứ tự cố định
COST = {'U': 1.0, 'D': 1.0, 'L': 1.0, 'R': 1.0, 'SWAP': 1.0}  # chỗ cấu hình duy nhất


def default_cost(state, action, next_state):
    """Hook mặc định: cost chỉ phụ thuộc hành động."""
    return COST[action]

# Khi split: khối lập phương nhỏ di chuyển 1 ô theo hướng
CUBE_DELTA = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


def cells(orient, r, c):
    if orient == 'S': return [(r, c)]
    if orient == 'H': return [(r, c), (r, c + 1)]
    return [(r, c), (r + 1, c)]          # 'V'


class Engine:
    def __init__(self, level_path: str, cost_fn=default_cost):
        self.step_cost = cost_fn
        lv = load_level(level_path)
        self.grid = lv.grid
        self.rows = len(lv.grid)
        self.cols = len(lv.grid[0])
        self.start = lv.start
        self.goal = lv.goal
        self.fragile = set(lv.fragile)
        self.bridges = {k: list(v) for k, v in lv.bridges.items()}
        self.bridge_at = {p: k for k, ps in self.bridges.items() for p in ps}
        self.bridges_initial_open = lv.bridges_initial_open
        self.switches = list(lv.switches)
        # vị trí -> danh sách switch tại ô đó (giữ thứ tự khai báo trong file)
        self.switches_at = {}
        for sw in self.switches:
            self.switches_at.setdefault(sw['pos'], []).append(sw)

    # ---------- kiểm tra ô / hợp lệ ----------
    def _is_floor(self, r, c):
        return 0 <= r < self.rows and 0 <= c < len(self.grid[r]) and self.grid[r][c] == '#'

    def _cell_ok(self, r, c, bridges):
        """Ô có đỡ được khối không (sàn, hoặc cầu đang mở)."""
        bid = self.bridge_at.get((r, c))
        if bid is not None:
            return bid in bridges
        return self._is_floor(r, c)

    def _is_valid(self, orient, r, c, state):
        for (cr, cc) in cells(orient, r, c):
            if not self._cell_ok(cr, cc, state.bridges):
                return False
            if orient == 'S' and (cr, cc) in self.fragile:
                return False
        return True

    # ---------- công tắc ----------
    @staticmethod
    def _fire(bridges, sw):
        """Áp tác dụng của một công tắc lên tập cầu đang mở. Trả về frozenset mới."""
        targets = frozenset(sw['targets'])
        if not targets:
            return bridges
        if sw['mode'] == 'toggle':
            return bridges ^ targets
        if sw['set'] == 'open':
            return bridges | targets
        return bridges - targets

    def _apply_switches(self, state: State) -> State:
        """Áp công tắc sau khi khối (không split) vừa đi xong một nước hợp lệ."""
        bridges = state.bridges
        teleport = None
        for pos in cells(state.orient, state.row, state.col):
            for sw in self.switches_at.get(pos, ()):
                t = sw['type']
                if t == 'soft' or (state.orient == 'S' and t in ('heavy', 'split')):
                    bridges = self._fire(bridges, sw)
                    if t == 'split':
                        teleport = sw['teleport']
        if teleport is not None:
            return State('S', 0, 0, bridges, SplitState(teleport, 0))
        return State(state.orient, state.row, state.col, bridges)

    # ---------- split ----------
    @staticmethod
    def _merge_or_split(cubes, active, bridges) -> State:
        """Hai khối liền kề thì gộp lại thành H/V; ngược lại giữ split."""
        (r0, c0), (r1, c1) = cubes
        if r0 == r1 and abs(c0 - c1) == 1:
            return State('H', r0, min(c0, c1), bridges)
        if c0 == c1 and abs(r0 - r1) == 1:
            return State('V', min(r0, r1), c0, bridges)
        return State('S', 0, 0, bridges, SplitState(cubes, active))

    def _split_successors(self, state: State):
        sp = state.split
        result = []
        for a in ACTIONS:
            dr, dc = CUBE_DELTA[a]
            r, c = sp.cubes[sp.active]
            nr, nc = r + dr, c + dc
            if (nr, nc) == sp.cubes[1 - sp.active]:
                continue
            if not self._cell_ok(nr, nc, state.bridges):
                continue
            # khối nhỏ nhẹ: đứng trên fragile được; chỉ soft switch kích hoạt
            bridges = state.bridges
            for sw in self.switches_at.get((nr, nc), ()):
                if sw['type'] == 'soft':
                    bridges = self._fire(bridges, sw)
            cubes = list(sp.cubes)
            cubes[sp.active] = (nr, nc)
            # công tắc có thể đóng cầu dưới chân một trong hai khối -> rơi
            if not all(self._cell_ok(cr, cc, bridges) for cr, cc in cubes):
                continue
            nxt = self._merge_or_split(tuple(cubes), sp.active, bridges)
            result.append((a, nxt, self.step_cost(state, a, nxt)))
        swapped = State('S', 0, 0, state.bridges, SplitState(sp.cubes, 1 - sp.active))
        result.append(('SWAP', swapped, self.step_cost(state, 'SWAP', swapped)))
        return result

    # ---------- interface chính (xem ENGINE_CONTRACT.md) ----------
    def initial_state(self) -> State:
        return State('S', self.start[0], self.start[1], self.bridges_initial_open)

    def is_goal(self, state: State) -> bool:
        return (state.split is None and state.orient == 'S'
                and (state.row, state.col) == self.goal)

    def get_successors(self, state: State):
        if state.split is not None:
            return self._split_successors(state)
        result = []
        for a in ACTIONS:
            o, dr, dc = TRANSITIONS[(state.orient, a)]
            r, c = state.row + dr, state.col + dc
            if not self._is_valid(o, r, c, state):
                continue
            nxt = self._apply_switches(State(o, r, c, state.bridges))
            # công tắc có thể đóng cầu ngay dưới khối (hoặc teleport xuống cầu đóng) -> rơi
            if nxt.split is None:
                if not self._is_valid(nxt.orient, nxt.row, nxt.col, nxt):
                    continue
            elif not all(self._cell_ok(cr, cc, nxt.bridges) for cr, cc in nxt.split.cubes):
                continue
            result.append((a, nxt, self.step_cost(state, a, nxt)))
        return result