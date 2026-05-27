import os
import json

PATH_USERS_DIR = "users"
PATH_USUARIOS_DB = os.path.join(PATH_USERS_DIR, "usuarios_db.json")

def carregar_usuarios():
    if not os.path.exists(PATH_USUARIOS_DB):
        return {}
    with open(PATH_USUARIOS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_usuarios(dados):
    with open(PATH_USUARIOS_DB, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def registrar_clique_apostado(user_id):
    """
    Gatilho acionado quando o usuário clica em 'Apostado'.
    Deduz o valor da stake atual do saldo dele.
    """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    if str_id not in db:
        return {"sucesso": False, "erro": "Usuário não registrado"}
        
    user = db[str_id]
    banca_anterior = user["banca_atual"]
    bs = user["base_segura"]
    lucro = max(0.0, banca_anterior - bs)
    
    # Define o valor que ele está apostando baseado no cenário atual dele
    # Se está no modo restrito ou se a banca zerou o lucro, aposta R$ 1,50.
    if user["modo_atual"] == "MAIS_ACERTOS" or lucro == 0:
        stake_apostada = 1.50
    else:
        # Se ele está no modo livre, assume o lucro disponível (ou uma stake padrão)
        stake_apostada = lucro  

    # Deduz o valor da banca do usuário (o jogo foi para o 'Green ou Red pendente')
    user["banca_atual"] -= stake_apostada
    
    # Salva as alterações no banco privado
    salvar_usuarios(db)
    
    return {
        "sucesso": True,
        "nome": user["nome"],
        "stake": stake_apostada,
        "banca_atualizada": user["banca_atual"],
        "modo": user["modo_atual"]
    }

def processar_resultado_final_jogo(user_id, ganhou, stake_usada, odd=2.0):
    """
    Esta função roda na Fase 2 da madrugada (conclusão dos placares).
    Se deu Green, ela devolve o dinheiro da stake + o lucro limpo.
    Se deu Red, o dinheiro já foi deduzido no clique, então só consolida.
    """
    db = carregar_usuarios()
    str_id = str(user_id)
    
    if str_id not in db:
        return
        
    user = db[str_id]
    
    if ganhou:
        # Devolve o valor apostado e soma o lucro da Odd
        retorno_total = stake_usada * odd
        user["banca_atual"] += retorno_total
    
    # Recalcula o modo para o próximo dia após a validação do placar real
    if user["trava_manual"] == "AUTOMATICA":
        if user["banca_atual"] < user["base_segura"]:
            user["modo_atual"] = "MAIS_ACERTOS"
        else:
            user["modo_atual"] = "LIVRE"
            
    salvar_usuarios(db)
    
