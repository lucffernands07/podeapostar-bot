def verificar_chance_dupla(s):
    try:
        mercados = []
        
        # Dados do novo modelo de raspagem (Casa em Casa / Visitante Fora)
        vitorias_casa = s.get("casa_vitorias_recente", 0)
        vitorias_fora_rec = s.get("fora_vitorias_recente", 0)

        # -----------------------------------------------------------------
        # 🟩 REGRA 1X: Mandante forte em casa vs Visitante fraco fora
        # -----------------------------------------------------------------
        # Derrotas/tropeços no contexto (considerando 5 jogos)
        tropecos_casa = 5 - vitorias_casa
        vitorias_visitante_fora = vitorias_fora_rec
        
        # 1X: Mandante invicto/máx 1 tropeço em casa AND Visitante venceu no máximo 3 jogos fora (pelo menos 2 tropeços)
        if tropecos_casa <= 1 and (5 - vitorias_visitante_fora) >= 2:
            if vitorias_casa == 5 and vitorias_visitante_fora <= 1:
                mercados.append("1X (100%)")
            elif vitorias_casa >= 4 or vitorias_visitante_fora <= 2:
                mercados.append("1X (85%)")
            else:
                mercados.append("1X (70%)")
                
        # -----------------------------------------------------------------
        # 🟦 REGRA 2X: Visitante forte fora vs Mandante fraco em casa + H2H
        # -----------------------------------------------------------------
        
        # Caminho A: Baseado na nova raspagem Casa/Fora (Visitante min 4/5 fora, Casa max 1/5 em casa)
        if vitorias_fora_rec >= 4 and vitorias_casa <= 1:
            if vitorias_fora_rec == 5 and vitorias_casa == 0:
                mercados.append("2X (100%)")
            else:
                mercados.append("2X (85%)")

        # Caminho B: Baseado em H2H Geral + Trava de Forma Recente
        else:
            vitorias_fora_h2h = 0
            for i in range(1, 6):
                if s.get(f"h2h_geral_res_{i}", "").strip().upper() == "FORA":
                    vitorias_fora_h2h += 1
                    
            ultimo_res_mandante = s.get("t1_resultado_1", "").strip().upper()
            ultimo_res_visitante = s.get("t2_resultado_1", "").strip().upper()
            
            if ultimo_res_mandante == "D" and ultimo_res_visitante == "V":
                if vitorias_fora_h2h == 3:
                    mercados.append("2X (70%)")
                elif vitorias_fora_h2h == 4:
                    mercados.append("2X (85%)")
                elif vitorias_fora_h2h == 5:
                    mercados.append("2X (100%)")
            else:
                if vitorias_fora_h2h >= 3:
                    print(f"   ⚠️ 2X descartado por forma recente: Mandante={ultimo_res_mandante} (esperado 'D'), Visitante={ultimo_res_visitante} (esperado 'V')", flush=True)
                
        return mercados
        
    except Exception as e:
        print(f"   ❌ Erro ao processar mercado de Dupla Chance: {e}", flush=True)
        return []
        
