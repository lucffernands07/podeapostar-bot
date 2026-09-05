"""
REGRAS DE MERCADO - AMBAS MARCAM (VERSÃO AJUSTADA)
- BTTS SIM: Soma de gols do mandante em casa >= 8 E soma de gols do visitante fora >= 8 E visitante fora ganhou por >= 3 gols.
- BTTS NÃO: Caso contrário, desde que haja no mínimo 3/5 jogos recentes com zero gol em pelo menos um dos lados.
"""

def verificar_btts(s, outros_mercados_aprovados=None, mercados_gols_aprovados=None, odds_jogo=None):
    mercados_aprovados = []
    try:
        if not isinstance(s, dict):
            return mercados_aprovados

        # Lê os placares do último jogo (mandante em casa e visitante fora)[span_0](start_span)[span_0](end_span)
        placar_mandante_casa = s.get("t1_placar_1", "")  # Ex: "2-1[span_1](start_span)"[span_1](end_span)
        placar_visitante_fora = s.get("t2_placar_1", "") # Ex: "0-3[span_2](start_span)"[span_2](end_span)

        gols_mandante_feito, gols_mandante_sofrido = 0, 0
        gols_visitante_sofrido, gols_visitante_feito = 0, 0

        # Quebra o placar do mandante em casa (Gols feitos - Gols sofridos)
        if placar_mandante_casa and "-" in placar_mandante_casa:
            partes = placar_mandante_casa.split("-")
            gols_mandante_feito = int(partes[0].strip())
            gols_mandante_sofrido = int(partes[1].strip())

        # Quebra o placar do visitante fora (Gols sofridos - Gols feitos)[span_3](start_span)[span_3](end_span)
        if placar_visitante_fora and "-" in placar_visitante_fora:
            partes = placar_visitante_fora.split("-")
            gols_visitante_sofrido = int(partes[0].strip()) #[span_4](start_span)[span_4](end_span)
            gols_visitante_feito = int(partes[1].strip())   #[span_5](start_span)[span_5](end_span)

        # Soma total de gols do mandante em casa (feitos + sofridos no último jogo)[span_6](start_span)[span_6](end_span)
        soma_gols_mandante_casa = gols_mandante_feito + gols_mandante_sofrido
        
        # Soma total de gols do visitante fora (feitos + sofridos no último jogo)[span_7](start_span)[span_7](end_span)
        soma_gols_visitante_fora = gols_visitante_feito + gols_visitante_sofrido

        # Condição de vitória do visitante fora (gols feitos > gols sofridos e >= 3)[span_8](start_span)[span_8](end_span)
        visitante_condicao_vitoria = (gols_visitante_feito >= 3 and gols_visitante_feito > gols_visitante_sofrido)

        # 🟢 REGRA BTTS SIM:[span_9](start_span)[span_9](end_span)
        if soma_gols_mandante_casa >= 8 and soma_gols_visitante_fora >= 8 and visitante_condicao_vitoria:
            mercados_aprovados.append({"mercado": "Ambas Marcam: Sim", "tipo": "BTTS_SIM"})
        else:
            # 🔴 REGRA BTTS NÃO COM FILTRO DE 3/5 JOGOS COM ZERO GOL (DE UM OU AMBOS OS LADOS)
            jogos_com_zero = 0
            
            # Verifica nos últimos jogos disponíveis armazenados nas chaves do dicionário (até 5 jogos)
            for i in range(1, 6):
                p_casa = str(s.get(f"t1_placar_{i}", ""))
                p_fora = str(s.get(f"t2_placar_{i}", ""))
                
                # Checa se o mandante passou em branco ou deixou zerado em algum dos jogos
                if p_casa and "-" in p_casa:
                    try:
                        g_feito, g_sofrido = map(int, p_casa.split("-"))
                        if g_feito == 0 or g_sofrido == 0:
                            jogos_com_zero += 1
                            continue
                    except:
                        pass
                
                # Checa se o visitante passou em branco ou deixou zerado em algum dos jogos
                if p_fora and "-" in p_fora:
                    try:
                        g_sofr, g_feit = map(int, p_fora.split("-"))
                        if g_feit == 0 or g_sofr == 0:
                            jogos_com_zero += 1
                    except:
                        pass

            # Se atingir o critério mínimo de 3 em 5 jogos com zero gol em algum dos lados, aprova o BTTS Não
            if jogos_com_zero >= 3:
                mercados_aprovados.append({"mercado": "Ambas Marcam: Não", "tipo": "BTTS_NAO"})

        return mercados_aprovados

    except Exception as e:
        print(f"      ⚠️ Erro ao processar regra Ambas Marcam: {e}")
        return mercados_aprovados
        
