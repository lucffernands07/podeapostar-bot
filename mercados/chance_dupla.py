def verificar_chance_dupla(s):
    try:
        mercados = []
        
        vitorias_casa = 0
        vitorias_fora = 0
        
        # 📊 Lê o canal exclusivo mapeado pelo main.py (as 5 partidas gerais sem travas)
        for i in range(1, 6):
            res_h2h = s.get(f"h2h_geral_res_{i}", "").strip().upper()
            if res_h2h == "CASA":
                vitorias_casa += 1
            elif res_h2h == "FORA":
                vitorias_fora += 1

        # -----------------------------------------------------------------
        # 🟩 FILTRAGEM DO MERCADO BASEADA NA SUA TAXA DE SUCESSO (Últimos 5 jogos)
        # -----------------------------------------------------------------
        
        # --- REGRA 1X (MANDANTE DE HOJE) ---
        if vitorias_casa == 3:
            mercados.append("1X (70%)")
        elif vitorias_casa == 4:
            mercados.append("1X (85%)")
        elif vitorias_casa == 5:
            mercados.append("1X (100%)")
        
        # --- REGRA 2X (VISITANTE DE HOJE) ---
        if vitorias_fora == 3:
            mercados.append("2X (70%)")
        elif vitorias_fora == 4:
            mercados.append("2X (85%)")
        elif vitorias_fora == 5:
            mercados.append("2X (100%)")
                
        return mercados
    except:
        return []
        
