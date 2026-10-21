import pytest
from engine.engine import TRANSITIONS, cells

EXPECTED = {
    ('S','U'): ('V',-2,0), ('S','D'): ('V',1,0), ('S','L'): ('H',0,-2), ('S','R'): ('H',0,1),
    ('H','U'): ('H',-1,0), ('H','D'): ('H',1,0), ('H','L'): ('S',0,-1), ('H','R'): ('S',0,2),
    ('V','U'): ('S',-1,0), ('V','D'): ('S',2,0), ('V','L'): ('V',0,-1), ('V','R'): ('V',0,1),
}

@pytest.mark.parametrize("key", list(EXPECTED))
def test_table_entry(key):
    assert TRANSITIONS[key] == EXPECTED[key]

# Kiểm tra vật lý: khối lăn quanh một cạnh thì ô mới phải liền kề ô cũ
def test_cells_geometry():
    assert cells('H', 2, 3) == [(2, 3), (2, 4)]
    assert cells('V', 2, 3) == [(2, 3), (3, 3)]
    # S(5,5) lăn R -> H(5,6): chiếm (5,6),(5,7)
    o, dr, dc = TRANSITIONS[('S', 'R')]
    assert cells(o, 5 + dr, 5 + dc) == [(5, 6), (5, 7)]