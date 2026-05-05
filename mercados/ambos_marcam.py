def verificar_ambos_marcam(s):
    try:
        mercados = []
        
        # --- REGRA AMBOS MARCAM ---
        
        # Passo 1: Condição Individual - Ambos marcaram e sofreram no seu último jogo
        # Casa (t1) BTTS no último jogo
        casa_btts_1 = (s.get("t1_gols_m_1", 0) > 0 and s.get("t1_gols_s_1", 0) > 0)
        # Fora (t2) BTTS no último jogo
        fora_btts_1 = (s.get("t2_gols_m_1", 0) > 0 and s.get("t2_gols_s_1", 0) > 0)
        
        cond_individual = casa_btts_1 and fora_btts_1

        # Passo 2: Condição H2H - Pelo menos um BTTS nos últimos 2 confrontos diretos
        h2h_1_btts = False
        placar_1 = s.get("h2h_placar_1", "0:0")
        if ":" in placar_1:
            g1 = placar_1.split(":")
            if int(g1[0]) > 0 and int(g1[1]) > 0:
                h2h_1_btts = True
        
        h2h_2_btts = False
        placar_2 = s.get("h2h_placar_2", "0:0")
        if ":" in placar_2:
            g2 = placar_2.split(":")
            if int(g2[0]) > 0 and int(g2[1]) > 0:
                h2h_2_btts = True

        cond_h2h = h2h_1_btts or h2h_2_btts

        # --- VALIDAÇÃO FINAL ---
        # Só entra se passar nos 3 critérios (Individual Casa + Individual Fora + H2H)
        if cond_individual and cond_h2h:
            # Seguindo a lógica de porcentagem baseada em frequência (ex: 4 de 5 jogos com BTTS)
            # t1_btts_5 e t2_btts_5 devem ser extraídos pelo seu scraper
            if s.get("t1_btts_5", 0) >= 4 and s.get("t2_btts_5", 0) >= 4:
                pct = "100%"
            else:
                pct = "85%"
                
            mercados.append(f"AMBAS MARCAM ({pct})")
                
        return mercados
    except:
        return []
        
