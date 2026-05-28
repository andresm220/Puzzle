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
        add_btn = st.form_submit_button("Agregar pieza")

    if add_btn:
        if any(p["id"] == piece_id for p in st.session_state.irr_pieces):
            st.warning(f"Ya existe una pieza con ID {piece_id}.")
        else:
            st.session_state.irr_pieces.append({
                "id": piece_id,
                "tipo": "normal",
                "available": True,
                "descripcion_visual": nombre_pieza.strip() or piece_id,
            })
            st.rerun()

    if st.session_state.irr_pieces:
        total = len(st.session_state.irr_pieces)
        sides_by_piece = {}
        fits_all = st.session_state.irr_fits
        for s in st.session_state.irr_sides:
            sides_by_piece.setdefault(s["piece_id"], []).append(s)

        st.markdown(f"**Piezas agregadas — {total} en total:**")
        for p in st.session_state.irr_pieces:
            pid = p["id"]
            nombre = p.get("descripcion_visual", pid)
            lados = sides_by_piece.get(pid, [])
            n_lados = len(lados)
            side_ids = {s["id"] for s in lados}
            n_conexiones = sum(
                1 for f in fits_all
                if f["from"] in side_ids or f["to"] in side_ids
            )

            # Build connection detail lines for this piece
            conn_lines = []
            piece_name_map = {p2["id"]: p2.get("descripcion_visual", p2["id"]) for p2 in st.session_state.irr_pieces}
            side_info_map = {s["id"]: s for s in st.session_state.irr_sides}
            for f in fits_all:
                sa = side_info_map.get(f["from"], {})
                sb = side_info_map.get(f["to"], {})
                if sa.get("piece_id") == pid:
                    otro_nombre = piece_name_map.get(sb.get("piece_id", ""), sb.get("piece_id", f["to"]))
                    conn_lines.append(f"↔ {sa.get('orientacion','?')} → <strong>{otro_nombre}</strong> ({sb.get('orientacion','?')})")
                elif sb.get("piece_id") == pid:
                    otro_nombre = piece_name_map.get(sa.get("piece_id", ""), sa.get("piece_id", f["from"]))
                    conn_lines.append(f"↔ {sb.get('orientacion','?')} → <strong>{otro_nombre}</strong> ({sa.get('orientacion','?')})")

            if n_lados == 0:
                estado = "⚠️ Sin lados configurados"
                color = "#92400E"
                bg = "#FEF3C7"
            elif n_conexiones == 0:
                estado = f"✓ {n_lados} lado{'s' if n_lados != 1 else ''} — sin conexiones aún"
                color = "#1E40AF"
                bg = "#EFF6FF"
            else:
                estado = f"✓ {n_lados} lado{'s' if n_lados != 1 else ''} · {n_conexiones} conexión{'es' if n_conexiones != 1 else ''}"
                color = "#14532D"
                bg = "#F0FDF4"

            # Sides with perfil
            sides_html = ""
            for s in lados:
                perfil = s.get("perfil", "")
                perfil_str = f' · <em>{perfil}</em>' if perfil not in ("", "plano", "sin_perfil") else ""
                sides_html += (
                    f'<div style="color:#475569;font-size:0.82em;margin-top:2px;padding-left:8px">'
                    f'{s["orientacion"]} — {s["forma"]}{perfil_str}</div>'
                )

            conns_html = "".join(
                f'<div style="color:#475569;font-size:0.82em;margin-top:2px;padding-left:8px">{line}</div>'
                for line in conn_lines
            )

            col1, col2 = st.columns([5, 1])
            col1.markdown(
                f'<div style="background:{bg};border-radius:6px;padding:8px 12px;margin-bottom:4px">'
                f'<strong style="color:#1E293B">{nombre}</strong> '
                f'<span style="color:#64748B;font-size:0.85em">{pid}</span><br>'
                f'<span style="color:{color};font-size:0.85em">{estado}</span>'
                f'{sides_html}'
                f'{conns_html}'
                f'</div>',
                unsafe_allow_html=True
            )
            if col2.button("Lados →", key=f"sides_{pid}"):
                st.session_state.irr_active_piece = pid
                st.session_state.irr_step = 3
                st.rerun()

    if st.button("✓ Finalizar y cargar", disabled=len(st.session_state.irr_pieces) == 0):
        _irr_load_to_neo4j()


def _irr_step3():
    active = st.session_state.irr_active_piece
    piece_info = next((p for p in st.session_state.irr_pieces if p["id"] == active), {})
    piece_label = piece_info.get("descripcion_visual") or active
    st.markdown(f"**Paso 3: Lados y conexiones — {active} — {piece_label}**")

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
            st.write(f"{s['id']} — {s['orientacion']} | {s['forma']} | {s['perfil']}")

    all_sides = st.session_state.irr_sides
    if len(all_sides) >= 2:
        st.divider()
        st.markdown("**Conectar lados (FITS_INTO)**")
        piece_map = {p["id"]: p.get("descripcion_visual") or p["id"]
                     for p in st.session_state.irr_pieces}
        def _side_label(s):
            perfil = s.get("perfil", "")
            perfil_str = f' · {perfil}' if perfil not in ("", "plano", "sin_perfil") else ""
            pieza_nombre = piece_map.get(s['piece_id'], s['piece_id'])
            return f"{pieza_nombre} — {s['orientacion']} ({s['forma']}{perfil_str})"

        side_labels = {s["id"]: _side_label(s) for s in all_sides}
        label_to_id = {v: k for k, v in side_labels.items()}
        side_options = list(side_labels.values())
        with st.form("irr_connect", clear_on_submit=True):
            col1, col2 = st.columns(2)
            side_a_label = col1.selectbox("Lado A", side_options, key="connect_a")
            side_b_label = col2.selectbox("Lado B", side_options, key="connect_b")
            side_a = label_to_id[side_a_label]
            side_b = label_to_id[side_b_label]
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
            st.markdown(f"**Conexiones registradas — {len(st.session_state.irr_fits)} en total:**")
            side_info = {s["id"]: s for s in all_sides}
            for f in st.session_state.irr_fits:
                sa = side_info.get(f["from"], {})
                sb = side_info.get(f["to"], {})
                nombre_a = piece_map.get(sa.get("piece_id", ""), sa.get("piece_id", f["from"]))
                nombre_b = piece_map.get(sb.get("piece_id", ""), sb.get("piece_id", f["to"]))
                ori_a = sa.get("orientacion", "?")
                ori_b = sb.get("orientacion", "?")
                forma_a = sa.get("forma", "?")
                forma_b = sb.get("forma", "?")
                st.markdown(
                    f'<div style="background:#F8FAFC;border-left:3px solid #D97706;'
                    f'padding:8px 12px;border-radius:0 6px 6px 0;margin-bottom:4px;font-size:0.9em">'
                    f'<strong style="color:#1E293B">{nombre_a}</strong> '
                    f'<span style="color:#64748B">({ori_a} · {forma_a})</span> '
                    f'<span style="color:#D97706">↔</span> '
                    f'<strong style="color:#1E293B">{nombre_b}</strong> '
                    f'<span style="color:#64748B">({ori_b} · {forma_b})</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

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
