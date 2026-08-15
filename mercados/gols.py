"""
REGRAS DE GOLS - VERSÃO AJUSTADA ÀS CHAVES DA RASPAGEM
Com trava de integridade de dados para abortar caso a raspagem falhe.
Ordem de Prioridade e Exclusão:
- Se houver Over (+1.5 ou +2.5), os Unders são vetados.
- Se houver Under (-3.5 ou -4.5), os Overs são vetados.
"""

def calcular_porcentagem_gols(c, f):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    if c < 2 or f < 2:
        return 0

    if c == 5 and f == 5:
        return 100
    elif c >= 4 and f >= 4:
        return 80
    elif c >= 3 and f >= 3:
        return 60
    else:
        return 40


def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    # 🛑 TRAVA DE SEGURANÇA: Validação de Integridade da Amostra
    try:
        c_15 = int(s.get("casa_15", 0) or 0)
        f_15 = int(s.get("fora_15", 0) or 0)
    except (ValueError, TypeError):
        c_15, f_15 = 0, 0

    # Se a raspagem não conseguiu coletar dados consistentes dos últimos jogos, aborta para evitar falsos unders
    if c_15 < 2 or f_15 < 2:
        print(f"      ⚠️ ALERTA DE LOG: Dados insuficientes ou falha na raspagem. Mercado de gols cancelado.")
        return []

    # Recorrência dos times nos últimos 5 jogos (usando as chaves corretas que a raspagem entrega)
    pct_15  = calcular_porcentagem_gols(s.get("casa_15", 0), s.get("fora_15", 0))
    pct_25  = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))
    
    # Nota: A raspagem atual gera apenas chaves de under globais (casa_35_under e casa_45_under). 
    # Mapeamos para ambos os lados utilizarem a mesma base coletada de forma segura.
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("casa_35_under", 0))
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("casa_45_under", 0))

    # Métricas de estatística defensiva/ofensiva disponíveis na raspagem atual
    mandante_gols_sofridos = float(s.get("mandante_gols_sofridos_casa", 0) or 0)
    visitante_gols_sofridos = float(s.get("visitante_gols_sofridos_fora", 0) or 0)

    # Média estimada de gols do confronto baseada nos gols sofridos e aproveitamento geral
    media_total_confronto = (mandante_gols_sofridos + visitante_gols_sofridos) / 2.5

    overs_aprovados = []
    unders_aprovados = []

    # Trava de risco contra goleadas baseada nos gols sofridos fora do visitante
    visitante_peneira = visitante_gols_sofridos >= 7
    pode_apostar_under = not visitante_peneira

    # ==========================================================
    # AVALIAÇÃO DE OVERS (+1.5 e +2.5) [Ajustado para 80% e 100%]
    # ==========================================================
    if pct_15 >= 80:
        overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})

    if pct_25 == 100:
        if media_total_confronto >= 2.4:
            overs_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})

    # ==========================================================
    # AVALIAÇÃO DE UNDERS (-4.5 e -3.5)
    # ==========================================================
    if pode_apostar_under and pct_m45 >= 60:
        if media_total_confronto <= 3.2:
            unders_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})

    if pode_apostar_under and pct_m35 >= 60:
        if media_total_confronto <= 2.6:
            unders_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})

    # ==========================================================
    # TRAVA DE EXCLUSÃO MÚTUA (NUNCA MISTURA OVER COM UNDER)
    # ==========================================================
    if overs_aprovados:
        return overs_aprovados
    else:
        return unders_aprovados
    
