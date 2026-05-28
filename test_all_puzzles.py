"""Prueba el BFS en todos los puzzles cargados."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from db import get_driver
from main import bfs_assemble

driver = get_driver()

with driver.session() as session:
    puzzles = list(session.run(
        """
        MATCH (pz:Puzzle)-[:HAS_PIECE]->(pc:Piece)
        RETURN pz.id AS id, pz.nombre AS nombre, pz.total_piezas AS total,
               count(pc) AS cargadas
        ORDER BY pz.id
        """
    ))

print(f"{'='*60}")
print(f"  PRUEBA DE TODOS LOS PUZZLES ({len(puzzles)} encontrados)")
print(f"{'='*60}\n")

all_ok = True

for pz in puzzles:
    pid = pz["id"]
    nombre = pz["nombre"]
    total = pz["total"]
    cargadas = pz["cargadas"]

    # Obtener pieza inicial (la primera disponible)
    with driver.session() as session:
        first = session.run(
            "MATCH (pz:Puzzle {id:$id})-[:HAS_PIECE]->(pc:Piece {available:true}) "
            "RETURN pc.id AS id ORDER BY pc.id LIMIT 1",
            id=pid
        ).single()

    if not first:
        print(f"[FAIL] {nombre} ({pid}) — sin piezas disponibles")
        all_ok = False
        continue

    start = first["id"]

    try:
        with driver.session() as session:
            result = bfs_assemble(session, pid, start)

        placed = result["placed"]
        total_r = result["total"]
        missing = result["missing"]
        unreachable = result["unreachable"]
        islands = len(result["islands"])

        ok = placed == total_r and not missing and not unreachable
        status = "OK  " if ok else "WARN"

        print(f"[{status}] {nombre}")
        print(f"       Piezas en DB: {cargadas} | Esperadas: {total} | Colocadas BFS: {placed}/{total_r}")
        if islands > 1:
            print(f"       Islas: {islands}")
        if missing:
            print(f"       Faltantes: {missing}")
        if unreachable:
            print(f"       No alcanzadas: {unreachable}")
        print(f"       Pieza inicial: {start}")
        print(f"       Pasos generados: {sum(len(i['steps']) for i in result['islands'])}")
        print()

        if not ok:
            all_ok = False

    except Exception as e:
        print(f"[FAIL] {nombre} ({pid}) — ERROR: {e}")
        all_ok = False
        print()

print(f"{'='*60}")
print(f"  Resultado: {'TODOS OK' if all_ok else 'HAY PROBLEMAS'}")
print(f"{'='*60}")

driver.close()
