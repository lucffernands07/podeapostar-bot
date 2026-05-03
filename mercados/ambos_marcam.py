def verificar_ambos_marcam(s):
    """
    Nova lógica Ambos Marcam (BTTS) - Sistema de Pontuação:
    Mínimo 2 passos para validar.
    """
    passos_concluidos = 0

    # PASSO 1: Último jogo individual da CASA teve Ambas Marcam?
    # t1_gols_m_1 (marcou) e t1_gols_s_1 (sofreu)
    if s.get("t1_gols_m_1", 0) > 0 and s.get("t1_gols_s_1", 0) > 0:
        passos_concluidos += 1

    # PASSO 2: Último jogo individual de FORA teve Ambas Marcam?
    # t2_gols_m_1 (marcou) e t2_gols_s_1 (sofreu)
    if s.get("t2_gols_m_1", 0) > 0 and s.get("t2_gols_s_1", 0) > 0:
        passos_concluidos += 1

    # PASSO 3: Pelo menos um Ambas Marcam nos últimos 2 jogos de Confronto Direto (H2H)
    btts_h2h = False
    for i in ["1", "2"]:
        placar = s.get(f"h2h_placar_{i}", "0:0")
        if ":" in placar:
            try:
                gols = placar.split(":")
                # Se os dois times marcaram no confronto histórico i
                if int(gols[0]) > 0 and int(gols[1]) > 0:
                    btts_h2h = True
                    break
            except:
                continue
    
    if btts_h2h:
        passos_concluidos += 1

    # --- VALIDAÇÃO DO MÍNIMO DE 2 PASSOS ---
    if passos_concluidos == 3:
        return [f"Ambas Marcam (100%)"]
    
    elif passos_concluidos == 2:
        # Aqui ele aceita QUALQUER combinação de 2 passos (1+2, 1+3 ou 2+3)
        return [f"Ambas Marcam (80%)"]
    
    else:
        # Se só bateu 1 passo ou nenhum, descarta (retorna lista vazia)
        return []
        
