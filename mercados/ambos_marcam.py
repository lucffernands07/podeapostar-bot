def verificar_btts(s):
    """
    Regra: Mínimo 4 de 5 sucessos para ambos os times.
    1° VALIDAÇÃO: Trava rígida (Clean Sheet) - O jogo mais recente (H2H 0)
    DEVE ter sido 'Ambas Marcam' para os dois (casa_ult_btts e fora_ult_btts).
    """
    
    # 1. Verifica a trava do jogo mais recente (Obrigatório para 85% ou 100%)
    # Se o robô não confirmou que ambos marcaram e sofreram no último, cancela.
    casa_ok = s.get("casa_ult_btts")
    fora_ok = s.get("fora_ult_btts")
    
    if not (casa_ok and fora_ok):
        return None

    # 2. Verifica a frequência (mínimo 4/5)
    frequencia_ok = (s.get("casa_btts", 0) >= 4 and s.get("fora_btts", 0) >= 4)
    
    if frequencia_ok:
        # 3. Retorna a porcentagem baseada na frequência
        if s["casa_btts"] == 5 and s["fora_btts"] == 5:
            return "100%"
        else:
            return "85%" # Caso um ou ambos sejam 4/5
            
    return None
