import re

def verificar_vitoria_casa(stats):
    """
    Regra de Vitória Casa Baseada no Cruzamento de Mando:
    1. Mandante: Apenas VITÓRIA ('V') no seu último jogo geral.
    2. Visitante: Apenas DERROTA ('D') no seu último jogo geral.
    3. H2H: O último jogo com mando de campo correto (t1 em casa) precisa ser VITÓRIA ('V').
    
    Porcentagem fixa: 85%
    """
    retorno = []
    
    # Captura os dados do dicionário preenchido pelo main.py
    casa_ultimo = stats.get("t1_resultado_1", "")
    fora_ultimo = stats.get("t2_resultado_1", "")
    h2h_1 = stats.get("h2h_res_1", "")
    
    # 1. Validação do Momento Imediato (Passo 1 e 2 da sua regra)
    # Mandante precisa ter vencido o último jogo geral E Visitante precisa ter perdido o último jogo geral
    valida_momento = (casa_ultimo == "V") and (fora_ultimo == "D")
    
    # 2. Validação do H2H Histórico com Mando Correto (Passo 3 da sua regra)
    # Como o main.py já filtrou e descartou os mandos invertidos, o h2h_1 é o último jogo real em casa.
    valida_h2h = (h2h_1 == "V")
    
    # Executa o funil de segurança
    if valida_momento and valida_h2h:
        # Formata o texto exatamente como os seus outros módulos para o listão do Telegram
        mercado_texto = "Vitória Casa (85%)"
        retorno.append(mercado_texto)
        
    return retorno
    
