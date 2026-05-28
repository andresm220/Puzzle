import uuid
import streamlit as st
from seed import generate_puzzle_data, load_to_neo4j
from db import get_driver


def _new_puzzle_id():
    return f"PZL_{uuid.uuid4().hex[:6].upper()}"


def render_create():
    st.header("Crear rompecabezas")
    mode = st.radio("Tipo", ["Regular (cuadrícula)", "Irregular (pieza por pieza)"],
                    horizontal=True)
    st.divider()
    if mode == "Regular (cuadrícula)":
        _render_regular()
    else:
        _render_irregular()


def _render_regular():
    if "reg_puzzle_id" not in st.session_state:
        st.session_state.reg_puzzle_id = _new_puzzle_id()
    st.subheader("Rompecabezas de cuadrícula")
    with st.form("regular_form"):
        col1, col2 = st.columns(2)
        with col1:
            puzzle_id = st.text_input("ID", value=st.session_state.reg_puzzle_id, help="Auto-generado, puedes cambiarlo")
            nombre = st.text_input("Nombre", placeholder="Mi rompecabezas")
        with col2:
            rows = st.number_input("Filas", min_value=2, max_value=50, value=3)
            cols = st.number_input("Columnas", min_value=2, max_value=50, value=4)
        submitted = st.form_submit_button("Crear y cargar en Neo4j")

    if submitted:
        if not puzzle_id or not nombre:
            st.error("ID y nombre son requeridos.")
            return
        try:
            data = generate_puzzle_data(puzzle_id.strip(), nombre.strip(), int(rows), int(cols))
            driver = get_driver()
            load_to_neo4j(driver, data)
            st.session_state.reg_puzzle_id = _new_puzzle_id()
            st.markdown(
                f'<div class="success-card">✓ Rompecabezas <strong>{puzzle_id}</strong> cargado — '
                f'{int(rows)}×{int(cols)} = {int(rows)*int(cols)} piezas</div>',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Error: {e}")


def _render_irregular():
    st.subheader("Rompecabezas irregular")

    defaults = {
        "irr_step": 1,
        "irr_puzzle_id": _new_puzzle_id(),
        "irr_nombre": "",
        "irr_pieces": [],
        "irr_sides": [],
        "irr_fits": [],
        "irr_active_piece": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    step = st.session_state.irr_step
    st.caption(f"Paso {step} de 3")
    st.progress(step / 3)

    if step == 1:
        _irr_step1()
    elif step == 2:
        _irr_step2()
    elif step == 3:
        _irr_step3()


def _irr_step1():
    st.markdown("**Paso 1: Información del rompecabezas**")
    with st.form("irr_step1"):
        puzzle_id = st.text_input("ID del rompecabezas",
                                  value=st.session_state.irr_puzzle_id,
                                  help="Auto-generado, puedes cambiarlo")
        nombre = st.text_input("Nombre",
                               value=st.session_state.irr_nombre,
                               placeholder="Mi rompecabezas irregular")
        next_btn = st.form_submit_button("Siguiente →")
    if next_btn:
        if not puzzle_id or not nombre:
            st.error("Completa ID y nombre.")
            return
        st.session_state.irr_puzzle_id = puzzle_id.strip()
        st.session_state.irr_nombre = nombre.strip()
        st.session_state.irr_step = 2
        st.rerun()


def _irr_step2():
    st.markdown("**Paso 2: Agregar piezas**")
    pid = st.session_state.irr_puzzle_id

    with st.form("irr_add_piece", clear_on_submit=True):
        n = len(st.session_state.irr_pieces) + 1
        piece_id = st.text_input("ID de pieza", value=f"{pid}_P{n:03d}")
        nombre_pieza = st.text_input("Nombre / descripción", placeholder="Ej: Cielo azul, Montaña derecha")
        tipo = st.selectbox("Tipo", ["normal", "esquina", "borde", "interior"])
        available = st.checkbox("Disponible", value=True)
        add_btn = st.form_submit_button("Agregar pieza")

    if add_btn:
        if any(p["id"] == piece_id for p in st.session_state.irr_pieces):
            st.warning(f"Ya existe una pieza con ID {piece_id}.")
        else:
            st.session_state.irr_pieces.append({
                "id": piece_id,
                "tipo": tipo,
                "available": available,
                "descripcion_visual": nombre_pieza.strip() or piece_id,
            })
            st.rerun()

    if st.session_state.irr_pieces:
        st.markdown("**Piezas agregadas:**")
        for p in st.session_state.irr_pieces:
            col1, col2 = st.columns([4, 1])
            col1.write(f"`{p['id']}` — {p.get('descripcion_visual', p['id'])} | {p['tipo']} {'✓' if p['available'] else '✗'}")
            if col2.button("Lados →", key=f"sides_{p['id']}"):
                st.session_state.irr_active_piece = p["id"]
                st.session_state.irr_step = 3
                st.rerun()

    if st.button("✓ Finalizar y cargar", disabled=len(st.session_state.irr_pieces) == 0):
        _irr_load_to_neo4j()


def _irr_step3():
    active = st.session_state.irr_active_piece
    st.markdown(f"**Paso 3: Lados y conexiones — Pieza `{active}`**")

    with st.form("irr_add_side", clear_on_submit=True):
        orientacion = st.selectbox("Orientación", ["norte", "sur", "este", "oeste"])
        forma = st.selectbox("Forma", ["plano", "macho", "hembra"])
        perfil = st.text_input("Perfil", placeholder="curva_A")
        add_side_btn = st.form_submit_button("Agregar lado")

    if add_side_btn:
        side_id = f"{active}_{orientacion[0].upper()}"
        if any(s["id"] == side_id for s in st.session_state.irr_sides):
            st.warning(f"Ya existe el lado {orientacion} para esta pieza.")
        else:
            st.session_state.irr_sides.append({
                "id": side_id,
                "piece_id": active,
                "orientacion": orientacion,
                "forma": forma,
                "perfil": perfil.strip() or "sin_perfil",
            })
            st.rerun()

    sides_for_piece = [s for s in st.session_state.irr_sides if s["piece_id"] == active]
    if sides_for_piece:
        st.markdown("**Lados de esta pieza:**")
        for s in sides_for_piece:
            st.write(f"`{s['id']}` — {s['orientacion']} | {s['forma']} | {s['perfil']}")

    all_sides = st.session_state.irr_sides
    if len(all_sides) >= 2:
        st.divider()
        st.markdown("**Conectar lados (FITS_INTO)**")
        side_ids = [s["id"] for s in all_sides]
        with st.form("irr_connect", clear_on_submit=True):
            col1, col2 = st.columns(2)
            side_a = col1.selectbox("Lado A", side_ids, key="connect_a")
            side_b = col2.selectbox("Lado B", side_ids, key="connect_b")
            connect_btn = st.form_submit_button("Conectar →")
        if connect_btn:
            if side_a == side_b:
                st.error("Selecciona dos lados distintos.")
            elif any(f["from"] == side_a and f["to"] == side_b for f in st.session_state.irr_fits):
                st.warning("Esa conexión ya existe.")
            else:
                st.session_state.irr_fits.append({"from": side_a, "to": side_b})
                st.rerun()

        if st.session_state.irr_fits:
            st.markdown("**Conexiones:**")
            for f in st.session_state.irr_fits:
                st.write(f"`{f['from']}` ↔ `{f['to']}`")

    if st.button("← Volver a piezas"):
        st.session_state.irr_step = 2
        st.rerun()


def _irr_load_to_neo4j():
    pid = st.session_state.irr_puzzle_id
    nombre = st.session_state.irr_nombre
    pieces = st.session_state.irr_pieces
    sides = st.session_state.irr_sides
    fits = st.session_state.irr_fits

    data = {
        "puzzle": {"id": pid, "nombre": nombre, "total_piezas": len(pieces)},
        "pieces": [
            {**p, "puzzle_id": pid}
            for p in pieces
        ],
        "sides": sides,
        "fits": fits,
    }
    try:
        driver = get_driver()
        load_to_neo4j(driver, data)
        st.success(f"✓ Rompecabezas '{pid}' cargado con {len(pieces)} piezas y {len(fits)} conexiones.")
        for k in ["irr_step", "irr_puzzle_id", "irr_nombre", "irr_pieces",
                  "irr_sides", "irr_fits", "irr_active_piece"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
    except Exception as e:
        st.error(f"Error al cargar: {e}")
