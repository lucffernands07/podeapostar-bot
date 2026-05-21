def verificar_chance_dupla(s):
    try:
        mercados = []
        
        # Pega exatamente as variáveis que vêm das tabelas posicionais
        ucc = s.get("t1_resultado_1", "")  # Tabela 1: Último do Casa
        uff = s.get("t2_resultado_1", "")  # Tabela 2: Último do Fora
        uh2h = s.get("h2h_res_1", "")      # Tabela 3: Último H2H do Mando
        
        dados_ok = (ucc != "" and uff != "" and uh2h != "")
        if not dados_ok:
            return []

        # --- REGRA 1X (Idêntica ao seu texto e teste) ---
        # Tabela 1: V ou E | Tabela 2: D ou E | Tabela 3: V ou E
        cond_1x = (ucc in ["V", "E"] and uff in ["D", "E"] and uh2h in ["V", "E"])
        
        if cond_1x:
            pct = s.get("chance_dupla_pct", "85%")
            mercados.append(f"1X ({pct})")
        
        # --- REGRA 2X (Idêntica ao seu texto atual) ---
        # Tabela 1: D | Tabela 2: V | Tabela 3: D
        cond_2x = (ucc == "D" and uff == "V" and uh2h == "D")
        
        if cond_2x:
            pct = s.get("chance_dupla_pct", "90%")
            mercados.append(f"2X ({pct})")
                
        return mercados
    except:
        return []
        
