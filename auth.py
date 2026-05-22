"""
Gestão de utilizadores do Dashboard FdN
Níveis de acesso:
  - superadmin : Vê tudo, gere utilizadores
  - admin      : Vê todos os inquéritos, estatísticas completas
  - viewer     : Vê apenas resumo geral (sem dados pessoais)
"""

import bcrypt
import json
import os
import re
import logging
from datetime import datetime

USERS_FILE = "users_db.json"

# Configurar logging
logging.basicConfig(
    filename='dashboard_audit.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# Utilizadores de demonstração
DEFAULT_USERS = {
    "admin_fdn": {
        "password_hash": bcrypt.hashpw(b"Admin@FdN2026", bcrypt.gensalt()).decode(),
        "full_name": "Administrador FdN",
        "role": "superadmin",
        "email": "admin@fdn.escaleno.co.mz",
        "active": True,
        "created_at": datetime.now().isoformat()
    },
    "gestor": {
        "password_hash": bcrypt.hashpw(b"Gestor@2026", bcrypt.gensalt()).decode(),
        "full_name": "Gestor de Projecto",
        "role": "admin",
        "email": "gestor@fdn.escaleno.co.mz",
        "active": True,
        "created_at": datetime.now().isoformat()
    },
    "visualizador": {
        "password_hash": bcrypt.hashpw(b"Viewer@2026", bcrypt.gensalt()).decode(),
        "full_name": "Visualizador",
        "role": "viewer",
        "email": "viewer@fdn.escaleno.co.mz",
        "active": True,
        "created_at": datetime.now().isoformat()
    }
}

ROLE_LABELS = {
    "superadmin": "Super Admin",
    "admin": "Administrador",
    "viewer": "Visualizador"
}

ROLE_PERMISSIONS = {
    "superadmin": ["view_summary", "view_details", "view_map", "view_responses", "manage_users", "export_data"],
    "admin":      ["view_summary", "view_details", "view_map", "view_responses", "export_data"],
    "viewer":     ["view_summary", "view_map"]
}


def _load_users():
    """Carrega utilizadores do ficheiro JSON"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    # Primeira execução: criar ficheiro com users padrão
    _save_users(DEFAULT_USERS)
    return DEFAULT_USERS


def _save_users(users: dict):
    """Guarda utilizadores no ficheiro JSON"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def log_action(username: str, action: str, details: str = ""):
    """Regista acções para auditoria"""
    logging.info(f"{username} | {action} | {details}")


def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """Valida formato do username (3-20 caracteres, letras/números/underscore)"""
    return re.match(r'^[a-zA-Z0-9_]{3,20}$', username) is not None


def authenticate(username: str, password: str):
    """
    Verifica credenciais. Devolve o dict do utilizador ou None.
    """
    users = _load_users()
    user = users.get(username)
    if not user or not user.get("active", True):
        return None
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        log_action(username, "LOGIN_SUCESSO", "Login realizado com sucesso")
        return {**user, "username": username}
    log_action(username, "LOGIN_FALHOU", "Tentativa de login falhou")
    return None


def has_permission(user: dict, permission: str) -> bool:
    """Verifica se o utilizador tem determinada permissão"""
    if not user:
        return False
    role = user.get("role", "viewer")
    return permission in ROLE_PERMISSIONS.get(role, [])


def get_all_users():
    """Retorna lista de todos os utilizadores"""
    users = _load_users()
    return [{"username": k, **v} for k, v in users.items()]


def add_user(username: str, password: str, full_name: str, role: str, email: str, current_user=None) -> bool:
    """Adiciona novo utilizador (apenas superadmin)"""
    if current_user and current_user.get("role") != "superadmin":
        log_action(current_user.get("username", "unknown"), "ADD_USER_FALHOU", "Permissão negada")
        return False
    
    if not validate_username(username):
        log_action(current_user.get("username", "unknown"), "ADD_USER_FALHOU", f"Username inválido: {username}")
        return False
    
    if not validate_email(email):
        log_action(current_user.get("username", "unknown"), "ADD_USER_FALHOU", f"Email inválido: {email}")
        return False
    
    users = _load_users()
    if username in users:
        return False
    
    users[username] = {
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "full_name": full_name,
        "role": role,
        "email": email,
        "active": True,
        "created_at": datetime.now().isoformat()
    }
    _save_users(users)
    log_action(current_user.get("username", "system"), "ADD_USER_SUCESSO", f"Utilizador {username} criado")
    return True


def update_user(username: str, **kwargs) -> bool:
    """Actualiza dados de um utilizador"""
    users = _load_users()
    if username not in users:
        return False
    
    allowed_fields = ["full_name", "email", "role"]
    for field, value in kwargs.items():
        if field in allowed_fields:
            users[username][field] = value
    
    _save_users(users)
    return True


def update_user_password(username: str, new_password: str, current_user=None) -> bool:
    """Actualiza password de um utilizador"""
    if current_user and current_user.get("role") != "superadmin" and current_user.get("username") != username:
        log_action(current_user.get("username", "unknown"), "UPDATE_PASS_FALHOU", f"Permissão negada para {username}")
        return False
    
    users = _load_users()
    if username not in users:
        return False
    
    users[username]["password_hash"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    _save_users(users)
    log_action(current_user.get("username", "system"), "UPDATE_PASS_SUCESSO", f"Password actualizada para {username}")
    return True


def toggle_user_active(username: str, current_user=None) -> bool:
    """Activa/desactiva um utilizador"""
    if current_user and current_user.get("role") != "superadmin":
        log_action(current_user.get("username", "unknown"), "TOGGLE_USER_FALHOU", f"Permissão negada para {username}")
        return False
    
    users = _load_users()
    if username not in users or username == current_user.get("username"):
        return False
    
    users[username]["active"] = not users[username].get("active", True)
    _save_users(users)
    status = "ativado" if users[username]["active"] else "desativado"
    log_action(current_user.get("username", "system"), "TOGGLE_USER_SUCESSO", f"Utilizador {username} {status}")
    return True


def delete_user(username: str, current_user=None) -> bool:
    """Remove um utilizador (apenas superadmin, não pode remover a si próprio)"""
    if current_user and current_user.get("role") != "superadmin":
        return False
    
    users = _load_users()
    if username not in users or username == current_user.get("username"):
        return False
    
    del users[username]
    _save_users(users)
    log_action(current_user.get("username", "system"), "DELETE_USER_SUCESSO", f"Utilizador {username} removido")
    return True