"""
auth.py - Sistema de Autenticação FDN Dashboard
Compatível com Streamlit antigo (Python 3.6)
"""
import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# ============================================
# FUNÇÃO COMPATÍVEL DE RERUN
# ============================================
def safe_rerun():
    """Compatível com versões antigas e novas do Streamlit"""
    if hasattr(st, 'rerun'):
        st.rerun()
    elif hasattr(st, 'experimental_rerun'):
        st.experimental_rerun()
    else:
        # Se nenhum existir, recarregar a página via JavaScript
        st.markdown(
            '<meta http-equiv="refresh" content="0">',
            unsafe_allow_html=True
        )

# ============================================
# BASE DE DADOS
# ============================================

def get_db():
    """Retorna conexão à base de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Cria tabelas se não existirem e adiciona admin por defeito"""
    conn = get_db()
    c = conn.cursor()
    
    # Criar tabela
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
    
    # Verificar se admin existe ANTES de tentar inserir
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    admin_exists = c.fetchone()
    
    # Criar admin por defeito se não existir
    if not admin_exists:
        try:
            c.execute("""
                INSERT INTO users (username, password_hash, name, role, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "admin",
                hash_password("admin123"),
                "Administrador",
                "admin",
                1,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            # Já existe, ignorar
            pass
    
    conn.close()

def hash_password(password):
    """Hash SHA-256 da password"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================
# AUTENTICAÇÃO
# ============================================

def authenticate(username, password):
    """Verifica credenciais. Retorna utilizador ou None."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM users
        WHERE username = ? AND password_hash = ? AND active = 1
    """, (username.strip(), hash_password(password)))
    user = c.fetchone()
    
    if user:
        # Actualizar último login
        c.execute("UPDATE users SET last_login = ? WHERE id = ?",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user["id"]))
        conn.commit()
    
    conn.close()
    return user

def logout():
    """Limpa sessão"""
    for key in ["authenticated", "user_id", "user_name", "user_role", "username"]:
        if key in st.session_state:
            del st.session_state[key]
    safe_rerun()

# ============================================
# FORMULÁRIO DE LOGIN
# ============================================

def login_form():
    """Mostra formulário de login"""
    init_db()
    
    # CSS do login
    st.markdown("""
    <style>
    body { background-color: #f0f4f8; }
    .login-container {
        max-width: 400px;
        margin: 4rem auto;
        padding: 2.5rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(26,95,122,0.15);
    }
    .login-logo {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .login-logo h1 {
        color: #1a5f7a;
        font-size: 2rem;
        margin: 0;
    }
    .login-logo p {
        color: #666;
        font-size: 0.9rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1a5f7a, #0d3b4a);
        color: white;
        border: none;
        padding: 0.6rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: bold;
        margin-top: 0.5rem;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0d3b4a, #1a5f7a);
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-logo">
            <h1>📊 FDN</h1>
            <p>Dashboard de Progresso dos Levantamentos</p>
            <hr style="border-color:#1a5f7a33; margin: 1rem 0;">
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("👤 Utilizador", placeholder="username", key="login_user")
        password = st.text_input("🔒 Password", type="password", placeholder="••••••••", key="login_pass")
        
        if st.button("Entrar", key="login_btn"):
            if not username or not password:
                st.error("Preencha o utilizador e a password.")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user["id"]
                    st.session_state.user_name = user["name"]
                    st.session_state.user_role = user["role"]
                    st.session_state.username = user["username"]
                    st.rerun()
                else:
                    st.error("❌ Utilizador ou password incorrectos.")
        
        st.markdown("""
        <p style="text-align:center; font-size:0.75rem; color:#999; margin-top:1.5rem;">
            FDN © 2026 | Acesso Restrito
        </p>
        """, unsafe_allow_html=True)

    """Mostra formulário de login"""
    init_db()
    
    # CSS do login - sem sidebar
    st.markdown("""
    <style>
        /* Esconder completamente a sidebar */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* Esconder o header padrão do Streamlit */
        header {
            display: none !important;
        }
        
        /* Remover padding para usar espaço total */
        .main > div {
            padding: 0rem !important;
        }
        
        /* Centralizar o conteúdo */
        .stApp {
            background: linear-gradient(135deg, #f0f4f8 0%, #e0e8f0 100%);
        }
        
        /* Container do login */
        .login-container {
            max-width: 420px;
            margin: 0 auto;
            padding: 2.5rem;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(26,95,122,0.2);
        }
        
        .login-logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .login-logo h1 {
            color: #1a5f7a;
            font-size: 2.2rem;
            margin: 0;
        }
        
        .login-logo p {
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #1a5f7a, #0d3b4a);
            color: white;
            border: none;
            padding: 0.7rem;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: bold;
            margin-top: 1rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background: linear-gradient(135deg, #0d3b4a, #1a5f7a);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(26,95,122,0.3);
        }
        
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 1px solid #ddd;
            padding: 0.7rem;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #1a5f7a;
            box-shadow: 0 0 0 2px rgba(26,95,122,0.2);
        }
        
        hr {
            margin: 1rem 0;
        }
        
        /* Footer */
        .login-footer {
            text-align: center;
            font-size: 0.75rem;
            color: #999;
            margin-top: 1.5rem;
        }
    </style>
    
    <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh;">
        <div class="login-container">
            <div class="login-logo">
                <h1>📊 FDN</h1>
                <p>Dashboard de Progresso dos Levantamentos</p>
                <hr>
            </div>
    """, unsafe_allow_html=True)
    
    username = st.text_input("👤 Utilizador", placeholder="username", key="login_user")
    password = st.text_input("🔒 Password", type="password", placeholder="••••••••", key="login_pass")
    
    if st.button("Entrar", key="login_btn"):
        if not username or not password:
            st.error("Preencha o utilizador e a password.")
        else:
            user = authenticate(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user_id = user["id"]
                st.session_state.user_name = user["name"]
                st.session_state.user_role = user["role"]
                st.session_state.username = user["username"]
                safe_rerun()
            else:
                st.error("❌ Utilizador ou password incorrectos.")
    
    st.markdown("""
            <div class="login-footer">
                FDN © 2026 | Acesso Restrito
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# PAINEL DE ADMIN
# ============================================

def admin_panel():
    """Painel de gestão de utilizadores — só para admins"""
    if st.session_state.get("user_role") != "admin":
        st.error("Acesso negado.")
        return
    
    init_db()
    st.markdown("## ⚙️ Gestão de Utilizadores")
    
    tabs = st.tabs(["👥 Utilizadores", "➕ Novo Utilizador", "🔑 Alterar Password"])
    
    # ── Tab 1: Lista de utilizadores ──────────────────────
    with tabs[0]:
        conn = get_db()
        users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        conn.close()
        
        if not users:
            st.info("Sem utilizadores registados.")
        else:
            for u in users:
                with st.expander(f"{'🟢' if u['active'] else '🔴'} {u['name']} ({u['username']}) — {u['role']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Criado:** {u['created_at']}")
                        st.write(f"**Último login:** {u['last_login'] or 'Nunca'}")
                    with col2:
                        # Não permitir desactivar/eliminar o próprio admin
                        if u["username"] != "admin" or u["id"] != st.session_state.user_id:
                            if u["active"]:
                                if st.button(f"🔴 Desactivar", key=f"deact_{u['id']}"):
                                    conn = get_db()
                                    conn.execute("UPDATE users SET active = 0 WHERE id = ?", (u["id"],))
                                    conn.commit()
                                    conn.close()
                                    st.success("Utilizador desactivado.")
                                    safe_rerun()
                            else:
                                if st.button(f"🟢 Activar", key=f"act_{u['id']}"):
                                    conn = get_db()
                                    conn.execute("UPDATE users SET active = 1 WHERE id = ?", (u["id"],))
                                    conn.commit()
                                    conn.close()
                                    st.success("Utilizador activado.")
                                    safe_rerun()
                            
                            if st.button(f"🗑️ Eliminar", key=f"del_{u['id']}"):
                                conn = get_db()
                                conn.execute("DELETE FROM users WHERE id = ?", (u["id"],))
                                conn.commit()
                                conn.close()
                                st.success("Utilizador eliminado.")
                                safe_rerun()
                        else:
                            st.info("ℹ️ Não pode desactivar ou eliminar o próprio admin.")
    
    # ── Tab 2: Novo utilizador ─────────────────────────────
    with tabs[1]:
        st.markdown("### Criar novo utilizador")
        new_name = st.text_input("Nome completo", key="new_name")
        new_username = st.text_input("Username", key="new_username")
        new_password = st.text_input("Password", type="password", key="new_password")
        new_role = st.selectbox("Perfil", ["viewer", "tecnico", "admin"], key="new_role")
        
        role_info = {
            "viewer": "Pode ver todos os dados mas não pode gerir utilizadores.",
            "tecnico": "Acesso à dashboard completa.",
            "admin": "Acesso total incluindo gestão de utilizadores."
        }
        st.info(role_info[new_role])
        
        if st.button("✅ Criar Utilizador", key="create_user_btn"):
            if not new_name or not new_username or not new_password:
                st.error("Preencha todos os campos.")
            elif len(new_password) < 6:
                st.error("A password deve ter pelo menos 6 caracteres.")
            else:
                try:
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO users (username, password_hash, name, role, active, created_at)
                        VALUES (?, ?, ?, ?, 1, ?)
                    """, (
                        new_username.strip(),
                        hash_password(new_password),
                        new_name.strip(),
                        new_role,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Utilizador '{new_username}' criado com sucesso!")
                    safe_rerun()
                except sqlite3.IntegrityError:
                    st.error(f"❌ O username '{new_username}' já existe.")
    
    # ── Tab 3: Alterar password ────────────────────────────
    with tabs[2]:
        st.markdown("### Alterar password de um utilizador")
        conn = get_db()
        usernames = [u["username"] for u in conn.execute("SELECT username FROM users").fetchall()]
        conn.close()
        
        target_user = st.selectbox("Utilizador", usernames, key="change_user")
        new_pass = st.text_input("Nova password", type="password", key="change_pass")
        confirm_pass = st.text_input("Confirmar password", type="password", key="confirm_pass")
        
        if st.button("🔑 Alterar Password", key="change_pass_btn"):
            if not new_pass or not confirm_pass:
                st.error("Preencha os campos de password.")
            elif new_pass != confirm_pass:
                st.error("As passwords não coincidem.")
            elif len(new_pass) < 6:
                st.error("A password deve ter pelo menos 6 caracteres.")
            else:
                conn = get_db()
                conn.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                             (hash_password(new_pass), target_user))
                conn.commit()
                conn.close()
                st.success(f"✅ Password de '{target_user}' alterada com sucesso!")