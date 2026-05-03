def verificar_chance_dupla(s):
    """
    Nova lógica de Dupla Chance baseada em:
    Passo 1: Momento Individual (Último jogo)
    Passo 2: Histórico Recente de Confronto Direto (Últimos 2 jogos H2H)
    """
    mercados = []
    
    # --- REGRA 1X (MANDANTE) ---
    # Passo 1: Casa venceu a última e Fora empatou ou perdeu
    condicao_individual_1x = (s["t1_resultado_1"] == "V" and s["t2_resultado_1"] in ["E", "D"])
    
    # Passo 2: Casa não perdeu nos últimos 2 jogos contra este adversário (H2H)
    # h2h_res_1 é o mais recente, h2h_res_2 é o anterior.
    # O resultado no H2H é sempre do ponto de vista do Time 1 (Mandante).
    # Portanto, "V" ou "E" no H2H significa que o mandante não perdeu.
    condicao_h2h_1x = (s["h2h_res_1"] in ["V", "E"] and s["h2h_res_2"] in ["V", "E"])

    if condicao_individual_1x and condicao_h2h_1x:
        # Define a porcentagem baseada no aproveitamento total recente
        pct = "100%" if s["casa_vitorias_recente"] >= 4 else "85%"
        mercados.append(f"1X ({pct})")
    

    # --- REGRA 2X (VISITANTE) ---
    # Passo 1: Fora venceu a última e Casa empatou ou perdeu
    condicao_individual_2x = (s["t2_resultado_1"] == "V" and s["t1_resultado_1"] in ["E", "D"])
    
    # Passo 2: Fora não perdeu nos últimos 2 jogos contra este adversário (H2H)
    # Como os resultados H2H no seu main são do ponto de vista do Time 1,
    # para o Time 2 não ter derrota, o H2H deve ser "D" (vitória do T2) ou "E" (empate).
    condicao_h2h_2x = (s["h2h_res_1"] in ["D", "E"] and s["h2h_res_2"] in ["D", "E"])

    if condicao_individual_2x and condicao_h2h_2x:
        pct = "100%" if s["fora_vitorias"] >= 4 else "90%"
        mercados.append(f"2X ({pct})")
            
    return mercados
