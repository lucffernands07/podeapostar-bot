def verificar_chance_dupla(s):
    try:
        mercados = []
        
        # --- REGRA 1X ---
        # Passo 1: Casa (t1) venceu a última e Fora (t2) empatou ou perdeu
        # O main extrai exatamente 't1_resultado_1' e 't2_resultado_1'
        cond_ind_1x = (s.get("t1_resultado_1") == "V" and s.get("t2_resultado_1") in ["E", "D"])
        
        # Passo 2: Mandante não perdeu os últimos 2 H2H (V ou E)
        cond_h2h_1x = (s.get("h2h_res_1") in ["V", "E"] and s.get("h2h_res_2") in ["V", "E"])

        if cond_ind_1x and cond_h2h_1x:
            pct = "100%" if s.get("casa_vitorias_recente", 0) >= 4 else "85%"
            mercados.append(f"1X ({pct})")
        
        # --- REGRA 2X ---
        cond_ind_2x = (s.get("t2_resultado_1") == "V" and s.get("t1_resultado_1") in ["E", "D"])
        cond_h2h_2x = (s.get("h2h_res_1") in ["D", "E"] and s.get("h2h_res_2") in ["D", "E"])

        if cond_ind_2x and cond_h2h_2x:
            pct = "100%" if s.get("fora_vitorias", 0) >= 4 else "90%"
            mercados.append(f"2X ({pct})")
                
        return mercados
    except:
        return []
        
