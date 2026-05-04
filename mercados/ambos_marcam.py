def verificar_ambos_marcam(s):
    passos_concluidos = 0

    # PASSO 1: Ambas marcam recente da Casa (Usa a contagem que o main já faz)
    if s.get("casa_btts", 0) >= 1:
        passos_concluidos += 1

    # PASSO 2: Ambas marcam recente de Fora
    if s.get("fora_btts", 0) >= 1:
        passos_concluidos += 1

    # PASSO 3: Média de gols no H2H (No seu main, se a média for alta, indica BTTS)
    # Se houveram muitos empates no H2H, a chance de BTTS é maior
    if s.get("h2h_empates", 0) >= 1:
        passos_concluidos += 1

    # VALIDAÇÃO DO MÍNIMO DE 2 PASSOS
    if passos_concluidos == 3:
        return [f"Ambas Marcam (100%)"]
    elif passos_concluidos == 2:
        return [f"Ambas Marcam (80%)"]
    
    return []
    
