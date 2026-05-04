def verificar_btts(s):
    try:
        passos = 0
        # Passo 1: BTTS no último jogo da Casa
        if s.get("t1_gols_m_1", 0) > 0 and s.get("t1_gols_s_1", 0) > 0:
            passos += 1

        # Passo 2: BTTS no último jogo de Fora
        if s.get("t2_gols_m_1", 0) > 0 and s.get("t2_gols_s_1", 0) > 0:
            passos += 1

        # Passo 3: BTTS no H2H (Últimos 2 jogos)
        btts_h2h = False
        for i in ["1", "2"]:
            placar = s.get(f"h2h_placar_{i}", "0:0")
            if ":" in placar:
                g = placar.split(":")
                if int(g[0]) > 0 and int(g[1]) > 0:
                    btts_h2h = True
                    break
        if btts_h2h:
            passos += 1

        # O seu main espera que retorne apenas a string da porcentagem se bater 2 passos
        if passos == 3: return "100%"
        if passos == 2: return "80%"
        
        return None # Se não bater 2 passos, retorna None e o main ignora
    except:
        return None
        
