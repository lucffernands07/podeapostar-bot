import os
import json

PATH_USERS_DIR = "users"
PATH_USUARIOS_DB = os.path.join(PATH_USERS_DIR, "usuarios_db.json")

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

def adicionar_ou_atualizar_usuario(user_id, nome, banca_inicial=10.00):
    """ Adiciona um novo cliente monitorado ao sistema """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    db[str_id] = {
        "nome": nome,
        "banca_atual": banca_inicial,
        "base_segura": 10.00,
        "trava_manual": "AUTOMATICA", # AUTOMATICA, FORCAR_BASE_SEGURA, FORCAR_LIVRE
        "modo_atual": "LIVRE" if banca_inicial >= 10.00 else "MAIS_ACERTOS"
    }
    salvar_usuarios(db)
    print(f"✅ Usuário {nome} ({user_id}) registrado com R$ {banca_inicial:.2f}")

def atualizar_saldo_pos_jogo(user_id, ganhou, valor_apostado, status_regras, odd=0.0):
    """
    Atualiza a banca do usuário e redefine o modo_atual baseado na trava
    e no saldo resultante do jogo.
    """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    if str_id not in db:
        print(f"❌ Usuário {user_id} não encontrado para atualização de saldo.")
        return

    user = db[str_id]
    
    # 1. Calcula o Green ou Red do bilhete
    if ganhou:
        lucro_limpo = (valor_apostado * odd) - valor_apostado
        user["banca_atual"] += lucro_limpo
    else:
        user["banca_atual"] -= valor_apostado

    # 2. Reavalia as regras de trava para definir o modo_atual do próximo jogo
    banca = user["banca_atual"]
    bs = user["base_segura"]
    trava = user["trava_manual"]
    
    if trava == "FORCAR_BASE_SEGURA":
        user["modo_atual"] = "MAIS_ACERTOS"
    elif trava == "FORCAR_LIVRE":
        user["modo_atual"] = "LIVRE"
    else: # AUTOMATICA
        if banca < bs:
            user["modo_atual"] = "MAIS_ACERTOS"
        else:
            user["modo_atual"] = "LIVRE"

    salvar_usuarios(db)
    print(f"💰 Saldo de {user['nome']} atualizado: R$ {user['banca_atual']:.2f} | Próximo Modo: {user['modo_atual']}")

def alterar_trava_manual(user_id, novo_status):
    """ Altera o comportamento da trava: AUTOMATICA, FORCAR_BASE_SEGURA, FORCAR_LIVRE """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    if str_id in db:
        db[str_id]["trava_manual"] = novo_status
        # Força o modo de forma imediata no clique/comando
        if novo_status == "FORCAR_BASE_SEGURA":
            db[str_id]["modo_atual"] = "MAIS_ACERTOS"
        elif novo_status == "FORCAR_LIVRE":
            db[str_id]["modo_atual"] = "LIVRE"
            
        salvar_usuarios(db)
        print(f"⚙️ Configuração manual de {db[str_id]['nome']} alterada para: {novo_status}")
    else:
        print("❌ Usuário não encontrado.")

# ---ÁREA DE TESTE LOCAL ---
if __name__ == "__main__":
    # Exemplo de fluxo ocorrendo em segundo plano:
    # 1. Cadastra o Carlos que entrou na sua lista VIP
    adicionar_ou_atualizar_usuario(987654321, "Carlos VIP", banca_inicial=10.00)
    
    # 2. Digamos que o Carlos teve um Red de R$ 1,50 em um bilhete
    # O sistema debita e já muda ele para o modo "MAIS_ACERTOS" automaticamente porque caiu para R$ 8,50
    atualizar_saldo_pos_jogo(987654321, ganhou=False, valor_apostado=1.50, status_regras="AUTOMATICA")
    
    # 3. Se você quiser que o Carlos teste os filtros novos mesmo com banca baixa, você força o Livre:
    alterar_trava_manual(987654321, "FORCAR_LIVRE")
  
