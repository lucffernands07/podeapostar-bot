def verificar_chance_dupla(s):
    try:
        mercados = []
        
        # Pega exatamente as variáveis que vêm das tabelas posicionais
        ucc = s.get("t1_resultado_1", "")  # Tabela 1: Último do Casa
        uff = s.get("t2_resultado_1", "")  # Tabela 2: Último do Fora
        uh2h = s.get("h2h_res_1", "")      # Tabela 3: Último H2H do Mando
        
        # --- AJUSTE NA TRAVA ---
        # O uh2h OBRIGATORIAMENTE precisa ser uma dessas três letras.
        # Se for "" (vazio por causa do continue), o jogo é barrado aqui.
        dados_ok = (ucc != "" and uff != "" and uh2h in ["V", "E", "D"])
        if not dados_ok:
            return []

        # --- REGRA 1X ---
        # Incluído o 'and dados_ok' para garantir a trava de ferro
        cond_1x = (ucc in ["V", "E"] and uff in ["D", "E"] and uh2h in ["V", "E"] and dados_ok)
        
        if cond_1x:
            pct = s.get("chance_dupla_pct", "85%")
            mercados.append(f"1X ({pct})")
        
        # --- REGRA 2X ---
        # Incluído o 'and dados_ok' para garantir a trava de ferro
        cond_2x = (ucc == "D" and uff == "V" and uh2h == "D" and dados_ok)
        
        if cond_2x:
            pct = s.get("chance_dupla_pct", "90%")
            mercados.append(f"2X ({pct})")
                
        return mercados
    except:
        return []
        
