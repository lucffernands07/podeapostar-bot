# mercados/chance_dupla.py

def verificar_chance_dupla(s):
    try:
        mercados = []
        
        # -----------------------------------------------------------------
        # 🟩 REGRA 1X: Baseada no limite de derrotas (Mandante vs Visitante)
        # -----------------------------------------------------------------
        derrotas_casa = 0
        derrotas_fora = 0
        
        # Contar derrotas nos últimos 5 jogos individuais do Mandante (t1)
        for i in range(1, 6):
            if s.get(f"t1_resultado_{i}", "").strip().upper() == "D":
                derrotas_casa += 1
                
        # Contar derrotas nos últimos 5 jogos individuais do Visitante (t2)
        for i in range(1, 6):
            if s.get(f"t2_resultado_{i}", "").strip().upper() == "D":
                derrotas_fora += 1
        
        # O certo para 1X: mandante só pode ter no máximo 1 derrota e o visitante >= 2 derrotas
        if derrotas_casa <= 1 and derrotas_fora >= 2:
            # Atribui a porcentagem de confiança com base no cenário de segurança
            if derrotas_casa == 0 and derrotas_fora >= 3:
                mercados.append("1X (100%)")
            elif derrotas_casa == 0 or derrotas_fora >= 3:
                mercados.append("1X (85%)")
            else:
                mercados.append("1X (70%)")
                
        # -----------------------------------------------------------------
        # 🟦 REGRA 2X: Baseada em Vitórias no H2H Geral + Trava Recente
        # -----------------------------------------------------------------
        vitorias_fora = 0
        
        # Lê o canal exclusivo mapeado pelo h2h geral das últimas 5 partidas
        for i in range(1, 6):
            res_h2h = s.get(f"h2h_geral_res_{i}", "").strip().upper()
            if res_h2h == "FORA":
                vitorias_fora += 1
                
        # 🔒 TRAVA DE FORMA RECENTE PARA 2X: Visitante venceu e Mandante perdeu no último jogo
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
            # Log preventivo para acompanhar no GitHub Actions se o 2X falhar na trava recente
            if vitorias_fora >= 3:
                print(f"   ⚠️ 2X descartado por forma recente: Mandante={ultimo_res_mandante} (esperado 'D'), Visitante={ultimo_res_visitante} (esperado 'V')", flush=True)
                
        return mercados
        
    except Exception as e:
        print(f"   ❌ Erro ao processar mercado de Dupla Chance: {e}", flush=True)
        return []
