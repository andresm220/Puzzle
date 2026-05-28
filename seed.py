import argparse
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase


def generate_puzzle_data(puzzle_id: str, nombre: str, rows: int, cols: int) -> dict:
    pieces = []
    sides = []
    fits = []

    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            pid = f"{puzzle_id}_P{r:02d}{c:02d}"
            is_top = r == 1
            is_bottom = r == rows
            is_left = c == 1
            is_right = c == cols

            if (is_top or is_bottom) and (is_left or is_right):
                tipo = "esquina"
            elif is_top or is_bottom or is_left or is_right:
                tipo = "borde"
            else:
                tipo = "interior"

            pieces.append({
                "id": pid,
                "puzzle_id": puzzle_id,
                "tipo": tipo,
                "descripcion_visual": f"Pieza {(r - 1) * cols + c}",
                "available": True,
            })

            for direction, is_exterior in [
                ("N", is_top),
                ("S", is_bottom),
                ("E", is_right),
                ("W", is_left),
            ]:
                sides.append({
                    "id": f"{pid}_{direction}",
                    "piece_id": pid,
                    "orientacion": {"N": "norte", "S": "sur", "E": "este", "W": "oeste"}[direction],
                    "forma": "plano" if is_exterior else None,
                    "perfil": "plano" if is_exterior else None,
                })

    sides_map = {s["id"]: s for s in sides}

    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            pid = f"{puzzle_id}_P{r:02d}{c:02d}"
            if c < cols:
                rpid = f"{puzzle_id}_P{r:02d}{c+1:02d}"
                profile = f"H_{r:02d}{c:02d}"
                a = sides_map[f"{pid}_E"]
                b = sides_map[f"{rpid}_W"]
                a["forma"], a["perfil"] = "macho", profile
                b["forma"], b["perfil"] = "hembra", profile
                fits.append({"from": a["id"], "to": b["id"]})
            if r < rows:
                bpid = f"{puzzle_id}_P{r+1:02d}{c:02d}"
                profile = f"V_{r:02d}{c:02d}"
                a = sides_map[f"{pid}_S"]
                b = sides_map[f"{bpid}_N"]
                a["forma"], a["perfil"] = "macho", profile
                b["forma"], b["perfil"] = "hembra", profile
                fits.append({"from": a["id"], "to": b["id"]})

    return {
        "puzzle": {"id": puzzle_id, "nombre": nombre, "total_piezas": rows * cols, "rows": rows, "cols": cols},
        "pieces": pieces,
        "sides": sides,
        "fits": fits,
    }


def to_cypher_string(data: dict) -> str:
    def _esc(value: str) -> str:
        return str(value).replace("'", "\\'")

    lines = []
    pz = data["puzzle"]
    lines.append(
        f"MERGE (pz:Puzzle {{id: '{_esc(pz['id'])}'}}) "
        f"SET pz.nombre = '{_esc(pz['nombre'])}', pz.total_piezas = {pz['total_piezas']};"
    )
    for pc in data["pieces"]:
        avail = "true" if pc["available"] else "false"
        lines.append(
            f"MERGE (pc:Piece {{id: '{_esc(pc['id'])}'}}) "
            f"SET pc.puzzle_id = '{_esc(pc['puzzle_id'])}', pc.tipo = '{_esc(pc['tipo'])}', "
            f"pc.descripcion_visual = '{_esc(pc['descripcion_visual'])}', pc.available = {avail};"
        )
        lines.append(
            f"MATCH (pz:Puzzle {{id: '{_esc(pc['puzzle_id'])}'}}), (pc:Piece {{id: '{_esc(pc['id'])}'}}) "
            f"MERGE (pz)-[:HAS_PIECE]->(pc);"
        )
    for s in data["sides"]:
        forma = s["forma"] or "plano"
        perfil = s["perfil"] or "plano"
        lines.append(
            f"MERGE (s:Side {{id: '{_esc(s['id'])}'}}) "
            f"SET s.piece_id = '{_esc(s['piece_id'])}', s.orientacion = '{_esc(s['orientacion'])}', "
            f"s.forma = '{_esc(forma)}', s.perfil = '{_esc(perfil)}';"
        )
        lines.append(
            f"MATCH (pc:Piece {{id: '{_esc(s['piece_id'])}'}}), (s:Side {{id: '{_esc(s['id'])}'}}) "
            f"MERGE (pc)-[:HAS_SIDE]->(s);"
        )
    for fit in data["fits"]:
        lines.append(
            f"MATCH (a:Side {{id: '{_esc(fit['from'])}'}}) , (b:Side {{id: '{_esc(fit['to'])}'}}) "
            f"MERGE (a)-[:FITS_INTO {{correct: true}}]->(b);"
        )
    return "\n".join(lines)


def load_to_neo4j(driver, data: dict) -> None:
    pz = data["puzzle"]
    with driver.session() as session:
        session.run(
            "MERGE (pz:Puzzle {id: $id}) SET pz.nombre = $nombre, pz.total_piezas = $total",
            id=pz["id"], nombre=pz["nombre"], total=pz["total_piezas"]
        )
        for pc in data["pieces"]:
            session.run(
                "MERGE (pc:Piece {id: $id}) "
                "SET pc.puzzle_id = $puzzle_id, pc.tipo = $tipo, "
                "pc.descripcion_visual = $desc, pc.available = $available",
                id=pc["id"], puzzle_id=pc["puzzle_id"], tipo=pc["tipo"],
                desc=pc["descripcion_visual"], available=pc["available"]
            )
            session.run(
                "MATCH (pz:Puzzle {id: $pzid}), (pc:Piece {id: $pcid}) "
                "MERGE (pz)-[:HAS_PIECE]->(pc)",
                pzid=pc["puzzle_id"], pcid=pc["id"]
            )
        for s in data["sides"]:
            forma = s["forma"] or "plano"
            perfil = s["perfil"] or "plano"
            session.run(
                "MERGE (s:Side {id: $id}) "
                "SET s.piece_id = $piece_id, s.orientacion = $orientacion, "
                "s.forma = $forma, s.perfil = $perfil",
                id=s["id"], piece_id=s["piece_id"], orientacion=s["orientacion"],
                forma=forma, perfil=perfil
            )
            session.run(
                "MATCH (pc:Piece {id: $pcid}), (s:Side {id: $sid}) "
                "MERGE (pc)-[:HAS_SIDE]->(s)",
                pcid=s["piece_id"], sid=s["id"]
            )
        for fit in data["fits"]:
            session.run(
                "MATCH (a:Side {id: $a}), (b:Side {id: $b}) "
                "MERGE (a)-[:FITS_INTO {correct: true}]->(b)",
                a=fit["from"], b=fit["to"]
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and load a puzzle into Neo4j")
    parser.add_argument("puzzle_id", help="Puzzle ID, e.g. PZL_001")
    parser.add_argument("nombre", help="Puzzle name")
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--output", help="Save generated Cypher to this file")
    parser.add_argument("--no-load", action="store_true", help="Skip loading into Neo4j")
    args = parser.parse_args()

    data = generate_puzzle_data(args.puzzle_id, args.nombre, args.rows, args.cols)

    if args.output:
        cypher = to_cypher_string(data)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(cypher)
        print(f"Cypher saved to {args.output}")

    if not args.no_load:
        load_dotenv()
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        if not all([uri, user, password]):
            import sys
            sys.exit("ERROR: NEO4J_URI, NEO4J_USER (or NEO4J_USERNAME), and NEO4J_PASSWORD must all be set in .env")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        try:
            load_to_neo4j(driver, data)
        finally:
            driver.close()
        print(f"Puzzle {args.puzzle_id} ({args.rows}x{args.cols}) loaded into Neo4j.")
