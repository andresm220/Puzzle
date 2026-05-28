import pytest
from seed import generate_puzzle_data

def test_corner_piece_tipo():
    data = generate_puzzle_data("PZL", "Test", 3, 3)
    corners = {p["id"] for p in data["pieces"] if p["tipo"] == "esquina"}
    assert corners == {"PZL_P0101", "PZL_P0103", "PZL_P0301", "PZL_P0303"}

def test_edge_piece_tipo():
    data = generate_puzzle_data("PZL", "Test", 3, 3)
    edges = {p["id"] for p in data["pieces"] if p["tipo"] == "borde"}
    assert edges == {"PZL_P0102", "PZL_P0201", "PZL_P0203", "PZL_P0302"}

def test_interior_piece_tipo():
    data = generate_puzzle_data("PZL", "Test", 3, 3)
    interior = [p for p in data["pieces"] if p["tipo"] == "interior"]
    assert len(interior) == 1
    assert interior[0]["id"] == "PZL_P0202"

def test_total_pieces():
    data = generate_puzzle_data("PZL", "Test", 4, 5)
    assert len(data["pieces"]) == 20

def test_fits_into_count_for_3x3():
    # horizontal: 2 per row * 3 rows = 6; vertical: 2 per col * 3 cols = 6 → 12 total
    data = generate_puzzle_data("PZL", "Test", 3, 3)
    assert len(data["fits"]) == 12

def test_corner_has_two_plano_sides():
    data = generate_puzzle_data("PZL", "Test", 3, 3)
    sides = {s["id"]: s for s in data["sides"]}
    assert sides["PZL_P0101_N"]["forma"] == "plano"
    assert sides["PZL_P0101_W"]["forma"] == "plano"
    assert sides["PZL_P0101_S"]["forma"] in ("macho", "hembra")
    assert sides["PZL_P0101_E"]["forma"] in ("macho", "hembra")

def test_fits_into_macho_hembra_pairing():
    data = generate_puzzle_data("PZL", "Test", 3, 3)
    sides = {s["id"]: s for s in data["sides"]}
    for fit in data["fits"]:
        a = sides[fit["from"]]
        b = sides[fit["to"]]
        assert a["perfil"] == b["perfil"]
        assert {a["forma"], b["forma"]} == {"macho", "hembra"}

def test_all_pieces_available_by_default():
    data = generate_puzzle_data("PZL", "Test", 3, 3)
    missing = [p for p in data["pieces"] if not p["available"]]
    assert len(missing) == 0

from seed import to_cypher_string

def test_cypher_string_contains_puzzle_merge():
    data = generate_puzzle_data("PZL", "Test", 2, 2)
    cypher = to_cypher_string(data)
    assert "MERGE (pz:Puzzle {id: 'PZL'})" in cypher

def test_cypher_string_contains_piece_merge():
    data = generate_puzzle_data("PZL", "Test", 2, 2)
    cypher = to_cypher_string(data)
    assert "MERGE (pc:Piece {id: 'PZL_P0101'})" in cypher

def test_cypher_string_contains_fits_into():
    data = generate_puzzle_data("PZL", "Test", 2, 2)
    cypher = to_cypher_string(data)
    assert "FITS_INTO" in cypher
