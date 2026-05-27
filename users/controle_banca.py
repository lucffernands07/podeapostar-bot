import os
import json

PATH_USERS_DIR = "users"
PATH_USUARIOS_DB = os.path.join(PATH_USERS_DIR, "usuarios_db.json")

def carregar_usuarios():
    os.makedirs(PATH_USERS_DIR, exist_ok=True)
    if not os.path.exists(PATH_USUARIOS_DB):
        with open(PATH_USUARIOS_DB, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
    with open(PATH_USUARIOS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_usuarios(dados):
    with open(PATH_USUARIOS_DB, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def verificar_cadastro_usuario(user_id):
    """
    Retorna True se o usuário já estiver registrado no banco,
    ou False se ele precisar ser barrado.
    """
    db = carregar_usuarios()
    return str(user_id) in db

def registrar_novo_usuario(user_id, nome):
    """
    Cadastra o usuário do zero com a Base Segura de R$ 10.
    Retorna True se for um cadastro novo, False se já existia.
    """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    if str_id not in db:
        db[str_id] = {
            "nome": nome,
            "banca_atual": 10.00,
            "base_segura": 10.00,
            "trava_manual": "AUTOMATICA",
            "modo_atual": "LIVRE"
        }
        salvar_usuarios(db)
        return True
    return False
    
