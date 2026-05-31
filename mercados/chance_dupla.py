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
        # 🔒 NOVA TRAVA: Só valida se o visitante venceu e o mandante perdeu no último jogo individual
        ultimo_res_mandante = s.get("t1_resultado_1", "").strip().upper()
        ultimo_res_visitante = s.get("t2_resultado_1", "").strip().upper()
        
        if ultimo_res_mandante == "D" and ultimo_res_visitante == "V":
            if vitorias_fora == 3:
                mercados.append("2X (70%)")
            elif vitorias_fora == 4:
                mercados.append("2X (85%)")
            elif vitorias_fora == 5:
                mercados.append("2X (100%)")
        else:
            # Log opcional para você acompanhar o motivo do descarte no GitHub Actions
            if vitorias_fora >= 3:
                print(f"   ⚠️ 2X descartado por forma recente: Mandante={ultimo_res_mandante} (esperado 'D'), Visitante={ultimo_res_visitante} (esperado 'V')", flush=True)
                
        return mercados
    except:
        return []
        
