import streamlit as st
from db import get_driver
from main import bfs_assemble


def render_solve():
    st.header("Resolver rompecabezas")

    with st.expander("🧭 ¿Qué es norte, sur, este y oeste?", expanded=False):
        st.markdown("""
Cada pieza física tiene **una flecha marcada** que indica su norte. Antes de empezar:

> **Define tu norte:** elige una dirección en tu mesa (por ejemplo, hacia la pared del frente) y mantenla fija durante todo el armado.

Con eso definido, cada pieza siempre se coloca con su flecha apuntando a ese norte. Las instrucciones usan los 4 puntos cardinales así:

| Símbolo | Dirección | En la pieza |
|---|---|---|
| ↑ Norte | Hacia tu norte | Borde de arriba |
| ↓ Sur | Opuesto a tu norte | Borde de abajo |
| → Este | A tu derecha | Borde derecho |
| ← Oeste | A tu izquierda | Borde izquierdo |

**Ejemplo:** *"Conéctala por su lado este → al lado oeste ← de 'Cielo centro'"* significa: toma el borde derecho de la pieza nueva y encájalo con el borde izquierdo de la pieza que ya está colocada.
        """)
        st.divider()

    driver = get_driver()

    with driver.session() as session:
        puzzles = list(session.run(
            """
            MATCH (pz:Puzzle)-[:HAS_PIECE]->(pc:Piece)
            RETURN pz.id AS id, pz.nombre AS nombre, pz.total_piezas AS total,
                   count(CASE WHEN pc.available = true THEN 1 END) AS disponibles
            ORDER BY pz.id
            """
        ))

    if not puzzles:
        st.info("No hay rompecabezas en la base de datos. Crea uno primero en la pestaña Crear.")
        return

    puzzle_options = {
        f"{r['id']} — {r['nombre']} ({r['disponibles']}/{r['total']} piezas)": r['id']
        for r in puzzles
    }
    selected_label = st.selectbox("Seleccionar rompecabezas", list(puzzle_options.keys()))
    puzzle_id = puzzle_options[selected_label]

    with driver.session() as session:
        pieces = list(session.run(
            """
            MATCH (pz:Puzzle {id: $puzzle_id})-[:HAS_PIECE]->(pc:Piece)
            RETURN pc.id AS id, pc.tipo AS tipo, pc.available AS available,
                   pc.descripcion_visual AS nombre
            ORDER BY pc.id
            """,
            puzzle_id=puzzle_id
        ))

    available_pieces = [p for p in pieces if p["available"]]

    st.divider()
    st.subheader("Marcar piezas faltantes (solo esta sesión)")
    st.caption("Las piezas marcadas se excluyen del BFS sin modificar la base de datos.")

    extra_missing = set()
    cols = st.columns(3)
    for i, p in enumerate(available_pieces):
        with cols[i % 3]:
            nombre = p.get('nombre') or p['id']
            label = f"{p['id']} — {nombre}"
            if st.checkbox(label, key=f"miss_{puzzle_id}_{p['id']}"):
                extra_missing.add(p["id"])

    st.divider()
    start_map = {
        f"{p['id']} — {p.get('nombre') or p['id']}": p["id"]
        for p in available_pieces if p["id"] not in extra_missing
    }

    if not start_map:
        st.warning("No hay piezas disponibles para iniciar el BFS.")
        return

    start_label = st.selectbox("Pieza inicial", list(start_map.keys()))
    start_piece = start_map[start_label]

    if st.button("▶ Resolver", use_container_width=True):
        with driver.session() as session:
            result = bfs_assemble(session, puzzle_id, start_piece, extra_missing=extra_missing)

        st.divider()
        st.subheader(f"Pasos — {result['placed']}/{result['total']} piezas")

        for island in result["islands"]:
            if len(result["islands"]) > 1:
                st.markdown(f"#### 🧩 {island['label']}")
            for step in island["steps"]:
                st.markdown(f'<div class="step-card">{step}</div>', unsafe_allow_html=True)

        for missing_id in result["missing"]:
            st.markdown(
                f'<div class="missing-card">⚠ Pieza <strong>{missing_id}</strong> '
                f'no disponible — sección omitida.</div>',
                unsafe_allow_html=True
            )

        if result["unreachable"]:
            st.warning(f"Piezas no alcanzadas por desconexión: {result['unreachable']}")

        st.markdown(
            f'<div class="success-card">Resumen: {result["placed"]}/{result["total"]} '
            f'piezas colocadas.</div>',
            unsafe_allow_html=True
        )
