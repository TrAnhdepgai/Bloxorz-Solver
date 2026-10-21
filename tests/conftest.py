import json
import pytest
from engine import Engine


@pytest.fixture
def make_engine(tmp_path):
    """Tạo Engine từ dict level. Dùng: make_engine(grid=[...], start=(r,c), goal=(r,c), **extra)"""
    def _make(grid, start, goal, **extra):
        data = {"grid": grid, "start": list(start), "goal": list(goal), **extra}
        p = tmp_path / "level.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return Engine(str(p))
    return _make