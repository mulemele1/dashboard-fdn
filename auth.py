"""
auth.py
Sistema de autenticação compatível com
Python 3.6 + Streamlit antigo
"""

import os
import sqlite3
import hashlib
from datetime import datetime

import streamlit as st

# =====================================================
# BASE DE DADOS
# =====================================================

DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "users.db"
)

# =====================================================
# SAFE RERUN
# =====================================================

def safe_rerun():

    if hasattr(st, "rerun"):
        st.rerun()

    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

    else:

        st.markdown(
            """
            <meta http-equiv="refresh" content="0">
            """,
            unsafe_allow_html=True
        )

# =====================================================
# HASH PASSWORD
# =====================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()

# =====================================================
# DB CONNECTION
# =====================================================

def get_db():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn

# =====================================================
# INIT DB
# =====================================================

def init_db():

    conn = get_db()

    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
    """)

    conn.commit()

    c.execute("""
        SELECT id
        FROM users
        WHERE username = 'admin'
    """)

    admin_exists = c.fetchone()

    if not admin_exists:

        c.execute("""
            INSERT INTO users (
                username,
                password_hash,
                name,
                role,
                active,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            hash_password("admin123"),
            "Administrador",
            "admin",
            1,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()

    conn.close()

# =====================================================
# AUTHENTICATE
# =====================================================

def authenticate(username, password):

    conn = get_db()

    c = conn.cursor()

    c.execute("""
        SELECT *
        FROM users
        WHERE username = ?
        AND password_hash = ?
        AND active = 1
    """, (
        username.strip(),
        hash_password(password)
    ))

    user = c.fetchone()

    if user:

        c.execute("""
            UPDATE users
            SET last_login = ?
            WHERE id = ?
        """, (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            user["id"]
        ))

        conn.commit()

    conn.close()

    return user

# =====================================================
# LOGOUT
# =====================================================

def logout():

    keys = [
        "authenticated",
        "user_id",
        "user_name",
        "user_role",
        "username"
    ]

    for key in keys:

        if key in st.session_state:
            del st.session_state[key]

    safe_rerun()

# =====================================================
# LOGIN FORM
# =====================================================

def login_form():

    init_db()

    st.markdown("""
    <style>

    [data-testid="collapsedControl"] {
        display: none !important;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    .login-box {
        background: white;
        padding: 2rem;
        border-radius: 14px;
        box-shadow: 0 2px 20px rgba(0,0,0,0.1);
    }

    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        st.markdown("""
        # 📊 FDN Dashboard

        Dashboard de Progresso dos Levantamentos
        """)

        username = st.text_input(
            "👤 Utilizador"
        )

        password = st.text_input(
            "🔒 Password",
            type="password"
        )

        if st.button("Entrar"):

            if not username or not password:

                st.error(
                    "Preencha todos os campos."
                )

            else:

                user = authenticate(
                    username,
                    password
                )

                if user:

                    st.session_state.authenticated = True
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["name"]
                    st.session_state.user_role = user["role"]
                    st.session_state.username = user["username"]

                    safe_rerun()

                else:

                    st.error(
                        "Credenciais inválidas."
                    )

# =====================================================
# ADMIN PANEL
# =====================================================

def admin_panel():

    if st.session_state.get("user_role") != "admin":

        st.error("Acesso negado.")

        return

    init_db()

    st.title("⚙️ Gestão de Utilizadores")

    menu = st.selectbox(
        "Escolha uma opção",
        [
            "👥 Utilizadores",
            "➕ Novo Utilizador",
            "🔑 Alterar Password"
        ]
    )

    # =================================================
    # UTILIZADORES
    # =================================================

    if menu == "👥 Utilizadores":

        conn = get_db()

        users = conn.execute("""
            SELECT *
            FROM users
            ORDER BY created_at DESC
        """).fetchall()

        conn.close()

        for u in users:

            status = "🟢" if u["active"] else "🔴"

            with st.expander(
                "{} {} ({}) — {}".format(
                    status,
                    u["name"],
                    u["username"],
                    u["role"]
                )
            ):

                st.write(
                    "Criado:",
                    u["created_at"]
                )

                st.write(
                    "Último login:",
                    u["last_login"] or "Nunca"
                )

                is_self_admin = (
                    u["username"] == "admin"
                    and
                    u["id"] == st.session_state.user_id
                )

                if is_self_admin:

                    st.info(
                        "Não pode remover o próprio admin."
                    )

                else:

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        if u["active"]:

                            if st.button(
                                "🔴 Desactivar",
                                key="deact_{}".format(u["id"])
                            ):

                                conn = get_db()

                                conn.execute("""
                                    UPDATE users
                                    SET active = 0
                                    WHERE id = ?
                                """, (u["id"],))

                                conn.commit()
                                conn.close()

                                safe_rerun()

                        else:

                            if st.button(
                                "🟢 Activar",
                                key="act_{}".format(u["id"])
                            ):

                                conn = get_db()

                                conn.execute("""
                                    UPDATE users
                                    SET active = 1
                                    WHERE id = ?
                                """, (u["id"],))

                                conn.commit()
                                conn.close()

                                safe_rerun()

                    with col2:

                        if st.button(
                            "🗑️ Eliminar",
                            key="del_{}".format(u["id"])
                        ):

                            conn = get_db()

                            conn.execute("""
                                DELETE FROM users
                                WHERE id = ?
                            """, (u["id"],))

                            conn.commit()
                            conn.close()

                            safe_rerun()

    # =================================================
    # NOVO UTILIZADOR
    # =================================================

    elif menu == "➕ Novo Utilizador":

        st.subheader("Novo Utilizador")

        name = st.text_input("Nome")

        username = st.text_input("Username")

        password = st.text_input(
            "Password",
            type="password"
        )

        role = st.selectbox(
            "Perfil",
            [
                "viewer",
                "tecnico",
                "admin"
            ]
        )

        if st.button("Criar Utilizador"):

            if (
                not name or
                not username or
                not password
            ):

                st.error(
                    "Preencha todos os campos."
                )

            else:

                try:

                    conn = get_db()

                    conn.execute("""
                        INSERT INTO users (
                            username,
                            password_hash,
                            name,
                            role,
                            active,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, 1, ?)
                    """, (
                        username.strip(),
                        hash_password(password),
                        name.strip(),
                        role,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    ))

                    conn.commit()
                    conn.close()

                    st.success(
                        "Utilizador criado."
                    )

                    safe_rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Username já existe."
                    )

    # =================================================
    # ALTERAR PASSWORD
    # =================================================

    elif menu == "🔑 Alterar Password":

        conn = get_db()

        usernames = [
            u["username"]
            for u in conn.execute("""
                SELECT username
                FROM users
            """).fetchall()
        ]

        conn.close()

        target = st.selectbox(
            "Utilizador",
            usernames
        )

        new_pass = st.text_input(
            "Nova password",
            type="password"
        )

        confirm = st.text_input(
            "Confirmar password",
            type="password"
        )

        if st.button("Alterar Password"):

            if new_pass != confirm:

                st.error(
                    "Passwords diferentes."
                )

            elif len(new_pass) < 6:

                st.error(
                    "Mínimo 6 caracteres."
                )

            else:

                conn = get_db()

                conn.execute("""
                    UPDATE users
                    SET password_hash = ?
                    WHERE username = ?
                """, (
                    hash_password(new_pass),
                    target
                ))

                conn.commit()
                conn.close()

                st.success(
                    "Password alterada."
                )

                safe_rerun()