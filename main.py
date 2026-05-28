import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8')
from collections import deque
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase


def validate_inputs(session, puzzle_id: str, piece_id: str) -> None:
    result = list(session.run(
        "MATCH (pz:Puzzle {id: $id}) RETURN count(pz) AS count",
        id=puzzle_id
    ))
    if not result or result[0]["count"] == 0:
        print(f"ERROR: Puzzle '{puzzle_id}' not found in database.")
        sys.exit(1)

    result = list(session.run(
        "MATCH (pc:Piece {id: $id, puzzle_id: $puzzle_id}) RETURN pc.available AS available",
        id=piece_id, puzzle_id=puzzle_id
    ))
    if not result:
        print(f"ERROR: Piece '{piece_id}' not found in puzzle '{puzzle_id}'.")
        sys.exit(1)
    if not result[0]["available"]:
        print(f"WARNING: Piece '{piece_id}' is marked as missing. Please choose an available piece.")
        sys.exit(1)


def get_available_neighbors(session, piece_id: str, visited: set, extra_missing: set = None) -> list:
    extra_missing = extra_missing or set()
    records = session.run(
        """
        MATCH (p:Piece {id: $pieceId})-[:HAS_SIDE]->(mySide:Side)
              -[:FITS_INTO {correct: true}]-(theirSide:Side)
              <-[:HAS_SIDE]-(neighbor:Piece {available: true})
        WHERE NOT neighbor.id IN $visited
          AND NOT neighbor.id IN $extraMissing
        RETURN neighbor.id                    AS pieza,
               neighbor.tipo                 AS tipo,
               neighbor.descripcion_visual   AS nombre,
               theirSide.orientacion         AS orientacion_requerida,
               theirSide.forma               AS forma,
               theirSide.perfil              AS perfil,
               mySide.orientacion            AS conecta_con_lado,
               p.id                          AS mi_pieza,
               p.descripcion_visual          AS mi_nombre
        """,
        pieceId=piece_id,
        visited=list(visited),
        extraMissing=list(extra_missing)
    )
    return [dict(r) for r in records]


def get_missing_neighbors(session, piece_id: str) -> list:
    records = session.run(
        """
        MATCH (p:Piece {id: $pieceId})-[:HAS_SIDE]->(mySide:Side)
              -[:FITS_INTO {correct: true}]-(theirSide:Side)
              <-[:HAS_SIDE]-(missing:Piece {available: false})
        RETURN missing.id AS pieza_faltante
        """,
        pieceId=piece_id
    )
    return [r["pieza_faltante"] for r in records]


_DIRS = {
    "norte": "SUPERIOR ↑",
    "sur":   "INFERIOR ↓",
    "este":  "DERECHO →",
    "oeste": "IZQUIERDO ←",
}


def format_step(step_num: int, data: dict, is_first: bool = False) -> str:
    nombre = data.get("nombre", "") or ""
    pieza_label = f'"{nombre}"' if nombre else f'"{data["pieza"]}"'

    if is_first:
        return (
            f"Paso {step_num} — PIEZA INICIAL\n"
            f"  ① Busca la pieza {pieza_label} y tómala.\n"
            f"  ② Colócala en la mesa con la imagen mirando hacia adelante (como en la caja).\n"
            f"  ③ Este es tu punto de partida. Las demás piezas se conectarán a esta."
        )

    su_lado = _DIRS.get(data["orientacion_requerida"], data["orientacion_requerida"].upper())
    lado_ya_puesta = _DIRS.get(data["conecta_con_lado"], data["conecta_con_lado"].upper())
    mi_nombre = data.get("mi_nombre") or data["mi_pieza"]

    return (
        f"Paso {step_num}\n"
        f'  ① Busca la pieza {pieza_label} y tómala.\n'
        f"  ② Oriéntala con la imagen correcta (borde superior apuntando hacia adelante).\n"
        f'  ③ Encájala por su borde {su_lado} con el borde {lado_ya_puesta} de '
        f'la pieza "{mi_nombre}" que ya está en su lugar.'
    )


def list_puzzles(session) -> None:
    records = list(session.run(
        """
        MATCH (pz:Puzzle)-[:HAS_PIECE]->(pc:Piece)
        RETURN pz.id AS id, pz.nombre AS nombre, pz.total_piezas AS total,
               count(CASE WHEN pc.available = true THEN 1 END) AS disponibles
        ORDER BY pz.id
        """
    ))
    print(f"{'ID':<12} {'Nombre':<20} {'Total':<8} {'Disponibles'}")
    print(f"{'-'*11} {'-'*19} {'-'*7} {'-'*11}")
    for r in records:
        print(f"{r['id']:<12} {r['nombre']:<20} {r['total']:<8} {r['disponibles']}")


def list_pieces(session, puzzle_id: str) -> None:
    records = list(session.run(
        """
        MATCH (pz:Puzzle {id: $puzzle_id})-[:HAS_PIECE]->(pc:Piece)
        RETURN pz.nombre AS nombre, pc.id AS id, pc.tipo AS tipo, pc.available AS available
        ORDER BY pc.id
        """,
        puzzle_id=puzzle_id
    ))
    if not records:
        print(f"ERROR: Puzzle '{puzzle_id}' not found.")
        sys.exit(1)
    nombre = records[0]["nombre"]
    print(f"\nPuzzle: {puzzle_id} — {nombre}\n")
    print(f"{'ID':<16} {'Tipo':<12} {'Disponible'}")
    print(f"{'-'*15} {'-'*11} {'-'*10}")
    for r in records:
        mark = "✓" if r["available"] else "✗  (missing)"
        print(f"{r['id']:<16} {r['tipo']:<12} {mark}")


def bfs_assemble(session, puzzle_id: str, start_piece_id: str, extra_missing: set = None) -> dict:
    extra_missing = extra_missing or set()

    all_pieces = list(session.run(
        "MATCH (pc:Piece {puzzle_id: $puzzle_id}) RETURN pc.id AS id, pc.available AS available",
        puzzle_id=puzzle_id
    ))
    total = len(all_pieces)
    available_ids = {r["id"] for r in all_pieces if r["available"]} - extra_missing

    visited = set()
    missing_found = set(extra_missing)
    islands = []

    candidates = [start_piece_id] + sorted(available_ids - {start_piece_id})

    for start in candidates:
        if start in visited or start not in available_ids:
            continue

        steps = []
        queue = deque([start])
        tipo_result = list(session.run(
            "MATCH (pc:Piece {id: $id}) RETURN pc.tipo AS tipo, pc.descripcion_visual AS nombre",
            id=start
        ))
        if not tipo_result:
            continue

        visited.add(start)
        steps.append(format_step(1, {
            "pieza": start, "tipo": tipo_result[0]["tipo"],
            "nombre": tipo_result[0].get("nombre") or "",
            "orientacion_requerida": None, "forma": None,
            "perfil": None, "conecta_con_lado": None, "mi_pieza": None,
        }, is_first=True))

        while queue:
            current = queue.popleft()
            for missing_id in get_missing_neighbors(session, current):
                if missing_id not in missing_found:
                    missing_found.add(missing_id)
            for neighbor in get_available_neighbors(session, current, visited, extra_missing):
                pid = neighbor["pieza"]
                if pid not in visited:
                    visited.add(pid)
                    steps.append(format_step(len(steps) + 1, neighbor))
                    queue.append(pid)

        islands.append({"label": f"Isla {len(islands) + 1}", "steps": steps})

    unreachable = sorted(available_ids - visited)

    return {
        "islands": islands,
        "missing": sorted(missing_found),
        "unreachable": unreachable,
        "placed": len(visited),
        "total": total,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BFS puzzle assembly guide")
    parser.add_argument(
        "--list",
        nargs="?",
        const=True,
        default=None,
        metavar="PUZZLE_ID",
        help="List all puzzles (no value) or pieces for a specific puzzle (with PUZZLE_ID)",
    )
    parser.add_argument("puzzle_id", nargs="?", help="Puzzle ID, e.g. PZL_001")
    parser.add_argument("start_piece", nargs="?", help="Starting piece ID, e.g. PZL_001_P0101")
    args = parser.parse_args()

    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, password]):
        sys.exit("ERROR: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must all be set in .env")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            if args.list is True:
                list_puzzles(session)
            elif args.list is not None:
                list_pieces(session, args.list)
            else:
                if not args.puzzle_id or not args.start_piece:
                    parser.error("puzzle_id and start_piece are required when --list is not used")
                validate_inputs(session, args.puzzle_id, args.start_piece)
                result = bfs_assemble(session, args.puzzle_id, args.start_piece)
                for i, island in enumerate(result["islands"]):
                    if len(result["islands"]) > 1:
                        print(f"\n=== Isla {i + 1} ===\n")
                    for step in island["steps"]:
                        print(step)
                        print()
                if result["missing"]:
                    print(f"⚠  Piezas faltantes: {result['missing']}")
                    print()
                print("---")
                print(f"Resumen: {result['placed']}/{result['total']} piezas colocadas.")
                if result["unreachable"]:
                    print(f"Piezas no alcanzadas: {result['unreachable']}")
    finally:
        driver.close()
