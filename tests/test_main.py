import pytest
from unittest.mock import MagicMock
from main import validate_inputs, get_available_neighbors, get_missing_neighbors, list_puzzles, list_pieces


def make_session(records):
    session = MagicMock()
    result = MagicMock()
    result.__iter__ = MagicMock(return_value=iter(records))
    session.run.return_value = result
    return session


def test_validate_inputs_raises_if_puzzle_not_found():
    session = make_session([])
    with pytest.raises(SystemExit):
        validate_inputs(session, "BAD_ID", "P001")


def test_validate_inputs_raises_if_piece_not_found():
    session = MagicMock()
    puzzle_result = MagicMock()
    puzzle_result.__iter__ = MagicMock(return_value=iter([{"count": 1}]))
    piece_result = MagicMock()
    piece_result.__iter__ = MagicMock(return_value=iter([]))
    session.run.side_effect = [puzzle_result, piece_result]
    with pytest.raises(SystemExit):
        validate_inputs(session, "PZL", "BAD_PIECE")


def test_validate_inputs_raises_if_piece_unavailable():
    session = MagicMock()
    puzzle_result = MagicMock()
    puzzle_result.__iter__ = MagicMock(return_value=iter([{"count": 1}]))
    piece_result = MagicMock()
    piece_result.__iter__ = MagicMock(return_value=iter([{"available": False}]))
    session.run.side_effect = [puzzle_result, piece_result]
    with pytest.raises(SystemExit):
        validate_inputs(session, "PZL", "PZL_P0202")


def test_get_available_neighbors_returns_list():
    record = {
        "pieza": "PZL_P0102", "tipo": "borde",
        "orientacion_requerida": "norte", "forma": "hembra",
        "perfil": "H_0101", "conecta_con_lado": "este", "mi_pieza": "PZL_P0101",
    }
    session = make_session([record])
    result = get_available_neighbors(session, "PZL_P0101", set())
    assert len(result) == 1
    assert result[0]["pieza"] == "PZL_P0102"


def test_get_missing_neighbors_returns_ids():
    record = {"pieza_faltante": "PZL_P0202"}
    session = make_session([record])
    result = get_missing_neighbors(session, "PZL_P0101")
    assert "PZL_P0202" in result


from main import format_step


def test_list_puzzles_prints_header(capsys):
    record = {"id": "PZL_001", "nombre": "Volcán", "total": 12, "disponibles": 11}
    session = make_session([record])
    list_puzzles(session)
    out = capsys.readouterr().out
    assert "PZL_001" in out
    assert "Volcán" in out
    assert "11" in out


def test_list_pieces_prints_pieces(capsys):
    record = {"nombre": "Volcán", "id": "PZL_001_P0101", "tipo": "esquina", "available": True}
    session = make_session([record])
    list_pieces(session, "PZL_001")
    out = capsys.readouterr().out
    assert "PZL_001_P0101" in out
    assert "esquina" in out


def test_list_pieces_exits_if_puzzle_not_found():
    session = make_session([])
    with pytest.raises(SystemExit):
        list_pieces(session, "BAD")


def test_format_step_first_piece():
    output = format_step(1, {
        "pieza": "PZL_P0101", "tipo": "esquina", "nombre": "Cielo azul",
        "orientacion_requerida": None, "forma": None,
        "perfil": None, "conecta_con_lado": None, "mi_pieza": None,
    }, is_first=True)
    assert "Paso 1" in output
    assert "Cielo azul" in output
    assert "punto de partida" in output.lower()

def test_format_step_regular_piece():
    output = format_step(2, {
        "pieza": "PZL_P0102", "tipo": "borde", "nombre": "Montaña",
        "orientacion_requerida": "norte", "forma": "hembra",
        "perfil": "H_0101", "conecta_con_lado": "este",
        "mi_pieza": "PZL_P0101", "mi_nombre": "Cielo azul",
    }, is_first=False)
    assert "Paso 2" in output
    assert "Montaña" in output
    assert "SUPERIOR" in output
    assert "DERECHO" in output
    assert "Cielo azul" in output


from main import bfs_assemble


def test_bfs_assemble_returns_dict():
    session = MagicMock()
    all_pieces_result = MagicMock()
    all_pieces_result.__iter__ = MagicMock(return_value=iter([
        {"id": "PZL_P0101", "available": True}
    ]))
    tipo_result = MagicMock()
    tipo_result.__iter__ = MagicMock(return_value=iter([{"tipo": "esquina"}]))
    missing_result = MagicMock()
    missing_result.__iter__ = MagicMock(return_value=iter([]))
    available_result = MagicMock()
    available_result.__iter__ = MagicMock(return_value=iter([]))
    session.run.side_effect = [
        all_pieces_result, tipo_result, missing_result, available_result
    ]
    result = bfs_assemble(session, "PZL", "PZL_P0101")
    assert isinstance(result, dict)
    assert "islands" in result
    assert "missing" in result
    assert "unreachable" in result
    assert "placed" in result
    assert "total" in result
    assert len(result["islands"]) == 1
    assert len(result["islands"][0]["steps"]) == 1


def test_bfs_assemble_extra_missing_excluded():
    session = MagicMock()
    all_pieces_result = MagicMock()
    all_pieces_result.__iter__ = MagicMock(return_value=iter([
        {"id": "PZL_P0101", "available": True},
        {"id": "PZL_P0102", "available": True},
    ]))
    tipo_result = MagicMock()
    tipo_result.__iter__ = MagicMock(return_value=iter([{"tipo": "esquina"}]))
    missing_result = MagicMock()
    missing_result.__iter__ = MagicMock(return_value=iter([]))
    available_result = MagicMock()
    available_result.__iter__ = MagicMock(return_value=iter([]))
    session.run.side_effect = [
        all_pieces_result, tipo_result, missing_result, available_result
    ]
    result = bfs_assemble(session, "PZL", "PZL_P0101", extra_missing={"PZL_P0102"})
    assert "PZL_P0102" in result["missing"]
