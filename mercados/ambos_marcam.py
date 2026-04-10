def verificar_btts(s):
    """
    Regra: Mínimo 4 de 5 sucessos para ambos os times.
    Trava de Segurança: O jogo mais recente (índice 0 no H2H) 
    deve ter sido 'Ambas Marcam' para os dois.
    """
    # 1. Verifica a frequência (mínimo 4/5)
    frequencia_ok = (s["casa_btts"] >= 4 and s["fora_btts"] >= 4)
    
    # 2. Verifica a trava do jogo mais recente
    ultimo_jogo_ok = (s["casa_ult_btts"] and s["fora_ult_btts"])
    
    if frequencia_ok and ultimo_jogo_ok:
        # Retorna a porcentagem baseada na frequência
        if s["casa_btts"] == 5 and s["fora_btts"] == 5:
            return "100%"
        else:
            return "85%" # Caso um ou ambos sejam 4/5
            
    return None
