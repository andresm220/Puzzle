"""Limpia la DB y carga puzzles de ejemplo con perfiles reales."""
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


# ── Helper ───────────────────────────────────────────────────────────────────
def side(sid, piece_id, orientacion, forma, perfil):
    return {"id": sid, "piece_id": piece_id,
            "orientacion": orientacion, "forma": forma, "perfil": perfil}

def piece(pid, puzzle_id, nombre):
    return {"id": pid, "puzzle_id": puzzle_id, "tipo": "normal",
            "descripcion_visual": nombre, "available": True}

def connect(a_id, b_id, perfil):
    """Returns (side_a_patch, side_b_patch, fit). a=macho, b=hembra."""
    return (
        {"id": a_id, "forma": "macho",  "perfil": perfil},
        {"id": b_id, "forma": "hembra", "perfil": perfil},
        {"from": a_id, "to": b_id},
    )

def patch_sides(sides, patches):
    idx = {s["id"]: s for s in sides}
    for p in patches:
        idx[p["id"]].update(p)

def load(puzzle_id, nombre, pieces, sides, fits):
    data = {
        "puzzle": {"id": puzzle_id, "nombre": nombre, "total_piezas": len(pieces)},
        "pieces": pieces, "sides": sides, "fits": fits,
    }
    load_to_neo4j(driver, data)
    print(f"✓ {nombre} — {len(pieces)} piezas · {len(fits)} conexiones")


# ── 2. Puzzles regulares (cuadrícula) ────────────────────────────────────────
print("--- Puzzles regulares ---")

for pid, nombre, r, c in [
    ("PZL_MINI",  "Mini 2×3",    2, 3),
    ("PZL_MED",   "Mediano 4×5", 4, 5),
    ("PZL_LARGE", "Grande 6×7",  6, 7),
]:
    data = generate_puzzle_data(pid, nombre, r, c)
    load_to_neo4j(driver, data)
    print(f"✓ {nombre} ({r}×{c} = {r*c} piezas)")


# ── 3. Jardín de Mariposas — irregular 2×3, perfiles descriptivos ─────────────
print("\n--- Puzzles irregulares ---")

PID = "PZL_JARDIN"
pieces_j = [
    piece(f"{PID}_P001", PID, "Cielo azul"),
    piece(f"{PID}_P002", PID, "Nube viajera"),
    piece(f"{PID}_P003", PID, "Sol del mediodía"),
    piece(f"{PID}_P004", PID, "Jardín bajo"),
    piece(f"{PID}_P005", PID, "Mariposa monarca"),
    piece(f"{PID}_P006", PID, "Flores silvestres"),
]

# Todos los lados — exteriores plano, interiores se parchean después
sides_j = [
    # P001 — esquina sup-izq
    side(f"{PID}_P001_N", f"{PID}_P001", "norte", "plano", "plano"),
    side(f"{PID}_P001_W", f"{PID}_P001", "oeste", "plano", "plano"),
    side(f"{PID}_P001_E", f"{PID}_P001", "este",  "macho", "?"),
    side(f"{PID}_P001_S", f"{PID}_P001", "sur",   "macho", "?"),
    # P002 — borde sup-centro
    side(f"{PID}_P002_N", f"{PID}_P002", "norte", "plano", "plano"),
    side(f"{PID}_P002_W", f"{PID}_P002", "oeste", "hembra", "?"),
    side(f"{PID}_P002_E", f"{PID}_P002", "este",  "macho",  "?"),
    side(f"{PID}_P002_S", f"{PID}_P002", "sur",   "macho",  "?"),
    # P003 — esquina sup-der
    side(f"{PID}_P003_N", f"{PID}_P003", "norte", "plano", "plano"),
    side(f"{PID}_P003_E", f"{PID}_P003", "este",  "plano", "plano"),
    side(f"{PID}_P003_W", f"{PID}_P003", "oeste", "hembra", "?"),
    side(f"{PID}_P003_S", f"{PID}_P003", "sur",   "macho",  "?"),
    # P004 — borde inf-izq
    side(f"{PID}_P004_S", f"{PID}_P004", "sur",   "plano", "plano"),
    side(f"{PID}_P004_W", f"{PID}_P004", "oeste", "plano", "plano"),
    side(f"{PID}_P004_N", f"{PID}_P004", "norte", "hembra", "?"),
    side(f"{PID}_P004_E", f"{PID}_P004", "este",  "macho",  "?"),
    # P005 — interior centro
    side(f"{PID}_P005_N", f"{PID}_P005", "norte", "hembra", "?"),
    side(f"{PID}_P005_W", f"{PID}_P005", "oeste", "hembra", "?"),
    side(f"{PID}_P005_E", f"{PID}_P005", "este",  "macho",  "?"),
    side(f"{PID}_P005_S", f"{PID}_P005", "sur",   "plano",  "plano"),
    # P006 — esquina inf-der
    side(f"{PID}_P006_S", f"{PID}_P006", "sur",   "plano", "plano"),
    side(f"{PID}_P006_E", f"{PID}_P006", "este",  "plano", "plano"),
    side(f"{PID}_P006_N", f"{PID}_P006", "norte", "hembra", "?"),
    side(f"{PID}_P006_W", f"{PID}_P006", "oeste", "hembra", "?"),
]

fits_j = []
patches_j = []
for a_id, b_id, perfil in [
    (f"{PID}_P001_E", f"{PID}_P002_W", "tab_nube"),
    (f"{PID}_P002_E", f"{PID}_P003_W", "pico_sol"),
    (f"{PID}_P004_E", f"{PID}_P005_W", "petalo_izq"),
    (f"{PID}_P005_E", f"{PID}_P006_W", "petalo_der"),
    (f"{PID}_P001_S", f"{PID}_P004_N", "onda_lluvia"),
    (f"{PID}_P002_S", f"{PID}_P005_N", "vuelo_mariposa"),
    (f"{PID}_P003_S", f"{PID}_P006_N", "rayo_luz"),
]:
    pa, pb, fit = connect(a_id, b_id, perfil)
    patches_j += [pa, pb]
    fits_j.append(fit)

patch_sides(sides_j, patches_j)
load(PID, "Jardín de Mariposas", pieces_j, sides_j, fits_j)


# ── 4. Océano Profundo — irregular 2×4, perfiles marinos ─────────────────────

PID = "PZL_OCEANO"
pieces_o = [
    piece(f"{PID}_P001", PID, "Superficie brillante"),
    piece(f"{PID}_P002", PID, "Ola central"),
    piece(f"{PID}_P003", PID, "Horizonte marino"),
    piece(f"{PID}_P004", PID, "Cielo costero"),
    piece(f"{PID}_P005", PID, "Fondo arenoso"),
    piece(f"{PID}_P006", PID, "Cardumen de peces"),
    piece(f"{PID}_P007", PID, "Coral rojo"),
    piece(f"{PID}_P008", PID, "Cueva submarina"),
]

# Layout 2 filas x 4 cols
# Fila 1: P001 P002 P003 P004
# Fila 2: P005 P006 P007 P008

sides_o = []
fits_o = []
patches_o = []

grid = [
    [f"{PID}_P001", f"{PID}_P002", f"{PID}_P003", f"{PID}_P004"],
    [f"{PID}_P005", f"{PID}_P006", f"{PID}_P007", f"{PID}_P008"],
]
ROWS, COLS = 2, 4

h_profiles = [
    ["cresta_ola_AB", "cresta_ola_BC", "cresta_ola_CD"],
    ["arena_AB",      "arena_BC",      "arena_CD"],
]
v_profiles = [
    ["buceo_1", "corriente_2", "profundidad_3", "abismo_4"],
]

for r in range(ROWS):
    for c in range(COLS):
        pid = grid[r][c]
        is_top = r == 0; is_bot = r == ROWS-1
        is_left = c == 0; is_right = c == COLS-1

        sides_o.append(side(f"{pid}_N", pid, "norte", "plano" if is_top  else "hembra", "plano" if is_top  else "?"))
        sides_o.append(side(f"{pid}_S", pid, "sur",   "plano" if is_bot  else "macho",  "plano" if is_bot  else "?"))
        sides_o.append(side(f"{pid}_W", pid, "oeste", "plano" if is_left else "hembra", "plano" if is_left else "?"))
        sides_o.append(side(f"{pid}_E", pid, "este",  "plano" if is_right else "macho", "plano" if is_right else "?"))

        if not is_right:
            perfil = h_profiles[r][c]
            right_pid = grid[r][c+1]
            pa, pb, fit = connect(f"{pid}_E", f"{right_pid}_W", perfil)
            patches_o += [pa, pb]; fits_o.append(fit)
        if not is_bot:
            perfil = v_profiles[r][c]
            bot_pid = grid[r+1][c]
            pa, pb, fit = connect(f"{pid}_S", f"{bot_pid}_N", perfil)
            patches_o += [pa, pb]; fits_o.append(fit)

patch_sides(sides_o, patches_o)
load(PID, "Océano Profundo", pieces_o, sides_o, fits_o)


# ── 5. Ciudad Nocturna — 3×3 irregular con perfiles arquitectónicos ───────────

PID = "PZL_CIUDAD"
nombres_c = [
    "Luna llena",       "Cielo estrellado", "Nube oscura",
    "Edificio izquierdo","Torre central",   "Ventanas iluminadas",
    "Calle y faroles",  "Acera mojada",     "Reflejo en charco",
]
perfiles_h = [
    ["arco_A", "arco_B"],
    ["ventana_C", "ventana_D"],
    ["adoquin_E", "adoquin_F"],
]
perfiles_v = [
    ["fachada_1", "fachada_2", "fachada_3"],
    ["vitrina_4", "vitrina_5", "vitrina_6"],
]

grid_c = [[f"{PID}_P{r*3+c+1:03d}" for c in range(3)] for r in range(3)]
pieces_c = [piece(grid_c[r][c], PID, nombres_c[r*3+c]) for r in range(3) for c in range(3)]
sides_c = []; fits_c = []; patches_c = []

for r in range(3):
    for c in range(3):
        pid = grid_c[r][c]
        is_top = r == 0; is_bot = r == 2
        is_left = c == 0; is_right = c == 2

        sides_c.append(side(f"{pid}_N", pid, "norte", "plano" if is_top   else "hembra", "plano" if is_top   else "?"))
        sides_c.append(side(f"{pid}_S", pid, "sur",   "plano" if is_bot   else "macho",  "plano" if is_bot   else "?"))
        sides_c.append(side(f"{pid}_W", pid, "oeste", "plano" if is_left  else "hembra", "plano" if is_left  else "?"))
        sides_c.append(side(f"{pid}_E", pid, "este",  "plano" if is_right else "macho",  "plano" if is_right else "?"))

        if not is_right:
            perfil = perfiles_h[r][c]
            pa, pb, fit = connect(f"{pid}_E", f"{grid_c[r][c+1]}_W", perfil)
            patches_c += [pa, pb]; fits_c.append(fit)
        if not is_bot:
            perfil = perfiles_v[r][c]
            pa, pb, fit = connect(f"{pid}_S", f"{grid_c[r+1][c]}_N", perfil)
            patches_c += [pa, pb]; fits_c.append(fit)

patch_sides(sides_c, patches_c)
load(PID, "Ciudad Nocturna", pieces_c, sides_c, fits_c)


# ── 6. Mapa del Tesoro — 3×3 regular con nombres descriptivos ─────────────────

data_mapa = generate_puzzle_data("PZL_MAPA", "Mapa del Tesoro", 3, 3)
for pc, nombre in zip(data_mapa["pieces"], [
    "Mar abierto",       "Brújula norte",     "Isla lejana",
    "Barco pirata",      "Marca X del tesoro", "Costa rocosa",
    "Cueva submarina",   "Arrecife de coral",  "Puerto escondido",
]):
    pc["descripcion_visual"] = nombre
load_to_neo4j(driver, data_mapa)
print(f"✓ Mapa del Tesoro — 3×3 con nombres descriptivos")


# ── 7. Verificación final ──────────────────────────────────────────────────────
print("\n--- Verificación de propiedades en Neo4j ---")
with driver.session() as s:
    r = s.run("MATCH (pz:Puzzle) RETURN count(pz) AS puzzles").single()
    r2 = s.run("MATCH (pc:Piece) RETURN count(pc) AS pieces").single()
    r3 = s.run("MATCH ()-[f:FITS_INTO]->() RETURN count(f) AS fits").single()
    r4 = s.run("MATCH (pc:Piece) WHERE pc.puzzle_id IS NOT NULL RETURN count(pc) AS c").single()
    r5 = s.run("MATCH (s:Side)  WHERE s.piece_id IS NOT NULL  RETURN count(s) AS c").single()
    r6 = s.run("MATCH (s:Side) WHERE s.perfil <> 'plano' AND s.perfil <> 'sin_perfil' RETURN count(s) AS c").single()
    print(f"Puzzles: {r['puzzles']}  |  Piezas: {r2['pieces']}  |  Conexiones: {r3['fits']}")
    print(f"Piece.puzzle_id aún en DB: {r4['c']}  (debe ser 0)")
    print(f"Side.piece_id aún en DB:   {r5['c']}  (debe ser 0)")
    print(f"Lados con perfil real:      {r6['c']}")

    # Muestra 5 perfiles de ejemplo
    sample = list(s.run(
        "MATCH (s:Side) WHERE s.perfil <> 'plano' RETURN s.id AS id, s.forma AS forma, s.perfil AS perfil LIMIT 6"
    ))
    print("\nEjemplos de lados con perfil:")
    for row in sample:
        print(f"  {row['id']:<35} forma={row['forma']:<8} perfil={row['perfil']}")

driver.close()
print("\n¡Listo!")
