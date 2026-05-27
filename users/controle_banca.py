import os
import json

PATH_USERS_DIR = "users"
PATH_USUARIOS_DB = os.path.join(PATH_USERS_DIR, "usuarios_db.json")

# Seu ID único do Telegram para garantir que só você acessa o painel de controle
SEU_TELEGRAM_ID = 123456789  # ⚠️ Substitua pelo seu ID real do Telegram

def garantir_banco_existe():
    os.makedirs(PATH_USERS_DIR, exist_ok=True)
    if not os.path.exists(PATH_USUARIOS_DB):
        with open(PATH_USUARIOS_DB, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)

def carregar_usuarios():
    garantir_banco_existe()
    with open(PATH_USUARIOS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_usuarios(dados):
    with open(PATH_USUARIOS_DB, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def garantir_usuario(user_id, nome_usuario):
    """ Registra o usuário com R$ 10 caso ele não exista no sistema """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    if str_id not in db:
        db[str_id] = {
            "nome": nome_usuario,
            "banca_atual": 10.00,
            "base_segura": 10.00,
            "trava_manual": "AUTOMATICA",  # Pode ser: AUTOMATICA, FORCAR_BASE_SEGURA, FORCAR_LIVRE
            "modo_atual": "LIVRE"
        }
        salvar_usuarios(db)
    return db[str_id]

def processar_regras_usuario(user_id):
    """
    Retorna qual o modo de bilhete e stake que o usuário deve receber,
    respeitando a trava automática por saldo ou a sua configuração manual.
    """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    if str_id not in db:
        return {"modo": "MAIS_ACERTOS", "stake": 1.50, "status": "TRAVADO"}
        
    user = db[str_id]
    banca = user["banca_atual"]
    bs = user["base_segura"]
    trava = user["trava_manual"]
    lucro = max(0.0, banca - bs)
    
    # 1. Verifica se você forçou manualmente alguma regra para ele
    if trava == "FORCAR_BASE_SEGURA":
        user["modo_atual"] = "MAIS_ACERTOS"
        salvar_usuarios(db)
        return {"modo": "MAIS_ACERTOS", "stake": 1.50, "status": "FORCADO_BASE_SEGURA"}
        
    elif trava == "FORCAR_LIVRE":
        user["modo_atual"] = "LIVRE"
        salvar_usuarios(db)
        return {"modo": "LIVRE", "stake": lucro if lucro > 0 else 1.50, "status": "FORCADO_LIVRE"}
        
    # 2. Se estiver em modo AUTOMÁTICA, decide puramente pelo saldo
    else:
        if banca < bs:
            user["modo_atual"] = "MAIS_ACERTOS"
            salvar_usuarios(db)
            return {"modo": "MAIS_ACERTOS", "stake": 1.50, "status": "AUTOMATICO_TRAVADO"}
        else:
            user["modo_atual"] = "LIVRE"
            salvar_usuarios(db)
            return {"modo": "LIVRE", "stake": lucro if lucro > 0 else 1.50, "status": "AUTOMATICO_LIVRE"}

# =========================================================================
# FUNÇÕES DO PAINEL ADMINISTRATIVO (SÓ VOCÊ CONTROLA)
# =========================================================================

def alterar_trava_usuario(admin_id, target_user_id, novo_status):
    """ Altera a trava de um usuário. Apenas se o admin_id for o seu """
    if admin_id != SEU_TELEGRAM_ID:
        return "❌ Acesso Negado."
        
    db = carregar_usuarios()
    str_target = str(target_user_id)
    
    if str_target in db:
        # novo_status deve ser: "AUTOMATICA", "FORCAR_BASE_SEGURA" ou "FORCAR_LIVRE"
        db[str_target]["trava_manual"] = novo_status
        salvar_usuarios(db)
        return f"✅ Usuário {db[str_target]['nome']} atualizado para: {novo_status}"
    return "❌ Usuário não encontrado."
  
