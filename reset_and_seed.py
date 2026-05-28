"""Limpia la DB y carga puzzles de ejemplo."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from db import get_driver
from seed import generate_puzzle_data, load_to_neo4j

driver = get_driver()


# ── 1. Limpiar todo ──────────────────────────────────────────────────────────
print("Limpiando base de datos...")
with driver.session() as s:
    s.run("MATCH (n) DETACH DELETE n")
print("✓ DB limpia\n")


# ── 2. Puzzles regulares (cuadrícula) ────────────────────────────────────────

regular_puzzles = [
    ("PZL_MINI",   "Mini 2×3",         2, 3),
    ("PZL_SMALL",  "Pequeño 3×4",      3, 4),
    ("PZL_MED",    "Mediano 4×5",      4, 5),
    ("PZL_LARGE",  "Grande 5×6",       5, 6),
]

for pid, nombre, rows, cols in regular_puzzles:
    data = generate_puzzle_data(pid, nombre, rows, cols)
    load_to_neo4j(driver, data)
    print(f"✓ {nombre} ({rows}×{cols} = {rows*cols} piezas)")


# ── 3. Puzzle irregular — Paisaje montañoso (6 piezas) ───────────────────────
print()

def make_side(side_id, piece_id, orientacion, forma, perfil):
    return {"id": side_id, "piece_id": piece_id,
            "orientacion": orientacion, "forma": forma, "perfil": perfil}

# Piezas
IRR1 = "PZL_PAISAJE"
pieces_irr1 = [
    {"id": f"{IRR1}_P001", "puzzle_id": IRR1, "tipo": "esquina",  "descripcion_visual": "Cielo izquierdo",    "available": True},
    {"id": f"{IRR1}_P002", "puzzle_id": IRR1, "tipo": "borde",    "descripcion_visual": "Cielo centro",       "available": True},
    {"id": f"{IRR1}_P003", "puzzle_id": IRR1, "tipo": "esquina",  "descripcion_visual": "Cielo derecho",      "available": True},
    {"id": f"{IRR1}_P004", "puzzle_id": IRR1, "tipo": "borde",    "descripcion_visual": "Montaña izquierda",  "available": True},
    {"id": f"{IRR1}_P005", "puzzle_id": IRR1, "tipo": "interior", "descripcion_visual": "Pico nevado",        "available": True},
    {"id": f"{IRR1}_P006", "puzzle_id": IRR1, "tipo": "borde",    "descripcion_visual": "Montaña derecha",    "available": True},
]

sides_irr1 = [
    # P001 (esquina sup-izq): bordes N y W planos, E y S encajan
    make_side(f"{IRR1}_P001_N", f"{IRR1}_P001", "norte",  "plano",  "plano"),
    make_side(f"{IRR1}_P001_W", f"{IRR1}_P001", "oeste",  "plano",  "plano"),
    make_side(f"{IRR1}_P001_E", f"{IRR1}_P001", "este",   "macho",  "H_R1C1"),
    make_side(f"{IRR1}_P001_S", f"{IRR1}_P001", "sur",    "macho",  "V_R1C1"),

    # P002 (borde sup-centro): borde N plano, E y W encajan, S encaja
    make_side(f"{IRR1}_P002_N", f"{IRR1}_P002", "norte",  "plano",  "plano"),
    make_side(f"{IRR1}_P002_W", f"{IRR1}_P002", "oeste",  "hembra", "H_R1C1"),
    make_side(f"{IRR1}_P002_E", f"{IRR1}_P002", "este",   "macho",  "H_R1C2"),
    make_side(f"{IRR1}_P002_S", f"{IRR1}_P002", "sur",    "macho",  "V_R1C2"),

    # P003 (esquina sup-der): bordes N y E planos
    make_side(f"{IRR1}_P003_N", f"{IRR1}_P003", "norte",  "plano",  "plano"),
    make_side(f"{IRR1}_P003_E", f"{IRR1}_P003", "este",   "plano",  "plano"),
    make_side(f"{IRR1}_P003_W", f"{IRR1}_P003", "oeste",  "hembra", "H_R1C2"),
    make_side(f"{IRR1}_P003_S", f"{IRR1}_P003", "sur",    "macho",  "V_R1C3"),

    # P004 (borde izq-abajo): borde W plano
    make_side(f"{IRR1}_P004_W", f"{IRR1}_P004", "oeste",  "plano",  "plano"),
    make_side(f"{IRR1}_P004_S", f"{IRR1}_P004", "sur",    "plano",  "plano"),
    make_side(f"{IRR1}_P004_N", f"{IRR1}_P004", "norte",  "hembra", "V_R1C1"),
    make_side(f"{IRR1}_P004_E", f"{IRR1}_P004", "este",   "macho",  "H_R2C1"),

    # P005 (interior — pico nevado)
    make_side(f"{IRR1}_P005_N", f"{IRR1}_P005", "norte",  "hembra", "V_R1C2"),
    make_side(f"{IRR1}_P005_W", f"{IRR1}_P005", "oeste",  "hembra", "H_R2C1"),
    make_side(f"{IRR1}_P005_E", f"{IRR1}_P005", "este",   "macho",  "H_R2C2"),
    make_side(f"{IRR1}_P005_S", f"{IRR1}_P005", "sur",    "plano",  "plano"),

    # P006 (borde der-abajo): borde E plano
    make_side(f"{IRR1}_P006_E", f"{IRR1}_P006", "este",   "plano",  "plano"),
    make_side(f"{IRR1}_P006_S", f"{IRR1}_P006", "sur",    "plano",  "plano"),
    make_side(f"{IRR1}_P006_N", f"{IRR1}_P006", "norte",  "hembra", "V_R1C3"),
    make_side(f"{IRR1}_P006_W", f"{IRR1}_P006", "oeste",  "hembra", "H_R2C2"),
]

fits_irr1 = [
    {"from": f"{IRR1}_P001_E", "to": f"{IRR1}_P002_W"},  # cielo izq → cielo centro
    {"from": f"{IRR1}_P002_E", "to": f"{IRR1}_P003_W"},  # cielo centro → cielo der
    {"from": f"{IRR1}_P001_S", "to": f"{IRR1}_P004_N"},  # cielo izq ↓ montaña izq
    {"from": f"{IRR1}_P002_S", "to": f"{IRR1}_P005_N"},  # cielo centro ↓ pico
    {"from": f"{IRR1}_P003_S", "to": f"{IRR1}_P006_N"},  # cielo der ↓ montaña der
    {"from": f"{IRR1}_P004_E", "to": f"{IRR1}_P005_W"},  # montaña izq → pico
    {"from": f"{IRR1}_P005_E", "to": f"{IRR1}_P006_W"},  # pico → montaña der
]

data_irr1 = {
    "puzzle": {"id": IRR1, "nombre": "Paisaje Montañoso", "total_piezas": 6},
    "pieces": pieces_irr1,
    "sides": sides_irr1,
    "fits": fits_irr1,
}
load_to_neo4j(driver, data_irr1)
print(f"✓ Paisaje Montañoso — irregular 6 piezas")


# ── 4. Puzzle irregular — Ciudad nocturna (8 piezas) ─────────────────────────

IRR2 = "PZL_CIUDAD"
pieces_irr2 = [
    {"id": f"{IRR2}_P001", "puzzle_id": IRR2, "tipo": "esquina",  "descripcion_visual": "Luna llena",         "available": True},
    {"id": f"{IRR2}_P002", "puzzle_id": IRR2, "tipo": "borde",    "descripcion_visual": "Cielo estrellado",   "available": True},
    {"id": f"{IRR2}_P003", "puzzle_id": IRR2, "tipo": "esquina",  "descripcion_visual": "Nube oscura",        "available": True},
    {"id": f"{IRR2}_P004", "puzzle_id": IRR2, "tipo": "borde",    "descripcion_visual": "Edificio izquierdo", "available": True},
    {"id": f"{IRR2}_P005", "puzzle_id": IRR2, "tipo": "interior", "descripcion_visual": "Torre central",      "available": True},
    {"id": f"{IRR2}_P006", "puzzle_id": IRR2, "tipo": "interior", "descripcion_visual": "Ventanas iluminadas","available": True},
    {"id": f"{IRR2}_P007", "puzzle_id": IRR2, "tipo": "borde",    "descripcion_visual": "Calle y faroles",    "available": True},
    {"id": f"{IRR2}_P008", "puzzle_id": IRR2, "tipo": "esquina",  "descripcion_visual": "Edificio derecho",   "available": True},
]

def grid_sides(puzzle_id, pieces_grid, rows, cols):
    """Generate sides and fits for a logical grid layout of irregular pieces."""
    sides = []
    fits = []
    grid = {}
    for r in range(rows):
        for c in range(cols):
            if r * cols + c < len(pieces_grid):
                grid[(r, c)] = pieces_grid[r * cols + c]["id"]

    for (r, c), pid in grid.items():
        is_top    = r == 0
        is_bottom = r == rows - 1
        is_left   = c == 0
        is_right  = c == cols - 1

        sides.append(make_side(f"{pid}_N", pid, "norte", "plano" if is_top    else "hembra", "plano" if is_top    else f"V_{r}{c}"))
        sides.append(make_side(f"{pid}_S", pid, "sur",   "plano" if is_bottom else "macho",  "plano" if is_bottom else f"V_{r+1}{c}"))
        sides.append(make_side(f"{pid}_W", pid, "oeste", "plano" if is_left   else "hembra", "plano" if is_left   else f"H_{r}{c}"))
        sides.append(make_side(f"{pid}_E", pid, "este",  "plano" if is_right  else "macho",  "plano" if is_right  else f"H_{r}{c+1}"))

        if c + 1 < cols and (r, c + 1) in grid:
            fits.append({"from": f"{pid}_E", "to": f"{grid[(r,c+1)]}_W"})
        if r + 1 < rows and (r + 1, c) in grid:
            fits.append({"from": f"{pid}_S", "to": f"{grid[(r+1,c)]}_N"})

    return sides, fits

sides_irr2, fits_irr2 = grid_sides(IRR2, pieces_irr2, 3, 3)

data_irr2 = {
    "puzzle": {"id": IRR2, "nombre": "Ciudad Nocturna", "total_piezas": 8},
    "pieces": pieces_irr2,
    "sides": sides_irr2,
    "fits": fits_irr2,
}
load_to_neo4j(driver, data_irr2)
print(f"✓ Ciudad Nocturna — irregular 8 piezas (1 faltante)")


# ── 5. Puzzle con piezas faltantes — Mapa del tesoro (9 piezas) ──────────────

data_mapa = generate_puzzle_data("PZL_MAPA", "Mapa del Tesoro", 3, 3)
descripciones = [
    "Mar abierto",      "Brújula norte",    "Isla lejana",
    "Barco pirata",     "Marca X del tesoro","Costa rocosa",
    "Cueva submarina",  "Arrecife de coral", "Puerto escondido",
]
for i, pc in enumerate(data_mapa["pieces"]):
    pc["descripcion_visual"] = descripciones[i]

load_to_neo4j(driver, data_mapa)
print(f"✓ Mapa del Tesoro — 3×3")


print("\n--- Resumen final ---")
with driver.session() as s:
    r = s.run("MATCH (pz:Puzzle) RETURN count(pz) AS puzzles").single()
    r2 = s.run("MATCH (pc:Piece) RETURN count(pc) AS pieces").single()
    r3 = s.run("MATCH ()-[f:FITS_INTO]->() RETURN count(f) AS fits").single()
    print(f"Puzzles: {r['puzzles']}  |  Piezas: {r2['pieces']}  |  Conexiones: {r3['fits']}")

driver.close()
print("\n¡Listo!")
