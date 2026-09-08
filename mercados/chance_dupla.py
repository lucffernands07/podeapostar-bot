"""
REGRAS DE MERCADO - CHANCE DUPLA (1X / X2) ATUALIZADO
- 1X: Mínimo 3 vitórias do mandante em casa (sendo nos 3 últimos jogos) E mínimo 3 derrotas do visitante fora (sendo nos 3 últimos jogos).
- X2: Mínimo 4 vitórias do visitante fora (sendo nos 3 últimos jogos) E mínimo 4 derrotas do mandante em casa (sendo nos 3 últimos jogos).
- Trava de Descarte Mútuo: Se ambos passarem, o jogo é descartado.
"""

def verificar_chance_dupla(s):
    """
    Recebe o dicionário 's' e retorna mercados de Chance Dupla aprovados (1X ou X2).
    Se ambos forem verdadeiros, ambos são descartados.
    """
    if not isinstance(s, dict):
        return []

    # --- CAPTURA DE DADOS DE SEQUÊNCIA DOS ÚLTIMOS JOGOS ---
    # Como a raspagem costuma ordenar do mais recente para o mais antigo (ex: _1, _2, _3...),
    # vamos verificar diretamente os resultados dos 3 últimos jogos (1, 2 e 3).
    
    # Exemplo de verificação de resultados nas chaves da raspagem:
    # Vamos conferir se os últimos 3 jogos de mandante em casa foram vitórias (gols mandante > gols visitante)
    try:
        m_vitoria_c1 = str(s.get("t1_resultado_1", "")).upper() == "V" or int(s.get("t1_gols_favor_1", 0) or 0) > int(s.get("t1_gols_contra_1", 0) or 0)
        m_vitoria_c2 = str(s.get("t1_resultado_2", "")).upper() == "V" or int(s.get("t1_gols_favor_2", 0) or 0) > int(s.get("t1_gols_contra_2", 0) or 0)
        m_vitoria_c3 = str(s.get("t1_resultado_3", "")).upper() == "V" or int(s.get("t1_gols_favor_3", 0) or 0) > int(s.get("t1_gols_contra_3", 0) or 0)
    except:
        m_vitoria_c1, m_vitoria_c2, m_vitoria_c3 = False, False, False

    # Derrotas do mandante em casa nos 3 últimos jogos (gols mandante < gols visitante)
    try:
        m_derrota_c1 = str(s.get("t1_resultado_1", "")).upper() == "D" or int(s.get("t1_gols_favor_1", 0) or 0) < int(s.get("t1_gols_contra_1", 0) or 0)
        m_derrota_c2 = str(s.get("t1_resultado_2", "")).upper() == "D" or int(s.get("t1_gols_favor_2", 0) or 0) < int(s.get("t1_gols_contra_2", 0) or 0)
        m_derrota_c3 = str(s.get("t1_resultado_3", "")).upper() == "D" or int(s.get("t1_gols_favor_3", 0) or 0) < int(s.get("t1_gols_contra_3", 0) or 0)
    except:
        m_derrota_c1, m_derrota_c2, m_derrota_c3 = False, False, False

    # Vitórias do visitante fora nos 3 últimos jogos (gols visitante > gols mandante)
    try:
        v_vitoria_f1 = str(s.get("t2_resultado_1", "")).upper() == "V" or int(s.get("t2_gols_favor_1", 0) or 0) > int(s.get("t2_gols_contra_1", 0) or 0)
        v_vitoria_f2 = str(s.get("t2_resultado_2", "")).upper() == "V" or int(s.get("t2_gols_favor_2", 0) or 0) > int(s.get("t2_gols_contra_2", 0) or 0)
        v_vitoria_f3 = str(s.get("t2_resultado_3", "")).upper() == "V" or int(s.get("t2_gols_favor_3", 0) or 0) > int(s.get("t2_gols_contra_3", 0) or 0)
    except:
        v_vitoria_f1, v_vitoria_f2, v_vitoria_f3 = False, False, False

    # Derrotas do visitante fora nos 3 últimos jogos (gols visitante < gols mandante)
    try:
        v_derrota_f1 = str(s.get("t2_resultado_1", "")).upper() == "D" or int(s.get("t2_gols_favor_1", 0) or 0) < int(s.get("t2_gols_contra_1", 0) or 0)
        v_derrota_f2 = str(s.get("t2_resultado_2", "")).upper() == "D" or int(s.get("t2_gols_favor_2", 0) or 0) < int(s.get("t2_gols_contra_2", 0) or 0)
        v_derrota_f3 = str(s.get("t2_resultado_3", "")).upper() == "D" or int(s.get("t2_gols_favor_3", 0) or 0) < int(s.get("t2_gols_contra_3", 0) or 0)
    except:
        v_derrota_f1, v_derrota_f2, v_derrota_f3 = False, False, False

    # Totais gerais coletados do dicionário (ex: mandante_vitorias_casa, visitante_derrotas_fora, etc.)
    m_tot_vitorias_casa = int(s.get("mandante_vitorias_casa", 0) or 0)
    m_tot_derrotas_casa = int(s.get("mandante_derrotas_casa", 0) or max(0, 5 - int(s.get("mandante_sem_derrota_casa", 0) or 0)))
    
    v_tot_vitorias_fora = int(s.get("visitante_vitorias_fora", 0) or 0)
    v_tot_derrotas_fora = int(s.get("visitante_derrotas_fora", 0) or max(0, 5 - int(s.get("visitante_sem_derrota_fora", 0) or 0)))

    # Variáveis de controle
    tem_1x = False
    tem_2x = False
    pct_1x = 80
    pct_2x = 80

    # ----------------------------------------------------------
    # 🟢 REGRA 1X
    # Mandante: Mínimo 3 vitórias no total E vitórias nos 3 últimos jogos em casa.
    # Visitante: Mínimo 3 derrotas no total E derrotas nos 3 últimos jogos fora.
    # ----------------------------------------------------------
    ultimos_tres_mandante_vitorias = (m_vitoria_c1 and m_vitoria_c2 and m_vitoria_c3)
    ultimos_tres_visitante_derrotas = (v_derrota_f1 and v_derrota_f2 and v_derrota_f3)

    condicao_1x = (m_tot_vitorias_casa >= 3 and ultimos_tres_mandante_vitorias) and \
                  (v_tot_derrotas_fora >= 3 and ultimos_tres_visitante_derrotas)

    if condicao_1x:
        tem_1x = True
        pct_1x = 100 if m_tot_vitorias_casa == 5 else 80

    # ----------------------------------------------------------
    # 🟢 REGRA X2
    # Visitante: Mínimo 4 vitórias no total E vitórias nos 3 últimos jogos fora.
    # Mandante: Mínimo 4 derrotas no total E derrotas nos 3 últimos jogos em casa.
    # ----------------------------------------------------------
    ultimos_tres_visitante_vitorias = (v_vitoria_f1 and v_vitoria_f2 and v_vitoria_f3)
    ultimos_tres_mandante_derrotas = (m_derrota_c1 and m_derrota_c2 and m_derrota_c3)

    condicao_x2 = (v_tot_vitorias_fora >= 4 and ultimos_tres_visitante_vitorias) and \
                  (m_tot_derrotas_casa >= 4 and ultimos_tres_mandante_derrotas)

    if condicao_x2:
        tem_2x = True
        pct_2x = 100 if v_tot_vitorias_fora == 5 else 80

    # ----------------------------------------------------------
    # 🛑 TRAVA DE DESCARTE MÚTUO
    # ----------------------------------------------------------
    if tem_1x and tem_2x:
        print(f"      ⚠️ CONFLITO DE CHANCE DUPLA: 1X e X2 passaram juntos. Jogo descartado.")
        return []

    # Adiciona os mercados aprovados
    mercados_aprovados = []
    if tem_1x:
        mercados_aprovados.append({"mercado": f"Dupla Chance: 1X ({pct_1x}%)", "tipo": "DC_1X"})
    if tem_2x:
        mercados_aprovados.append({"mercado": f"Dupla Chance: X2 ({pct_2x}%)", "tipo": "DC_X2"})

    return mercados_aprovados
    
