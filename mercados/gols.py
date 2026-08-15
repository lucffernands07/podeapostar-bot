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

    # Suas validações anteriores de porcentagem...
    c_15 = int(s.get("casa_15", 0) or 0)
    f_15 = int(s.get("fora_15", 0) or 0)
    
    if c_15 < 2 or f_15 < 2:
        return []

    pct_15 = calcular_porcentagem_gols(c_15, f_15)
    pct_25 = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("casa_35_under", 0))
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("casa_45_under", 0))

    # 🟢 PEGANDO AS POSIÇÕES DA TABELA PASSADAS PELA RASPAGEM
    m_pos = s.get("mandante_posicao")
    v_pos = s.get("visitante_posicao")

    overs_aprovados = []
    unders_aprovados = []

    # Exemplo de Aplicação da sua Regra de Tabela:
    tem_disparidade = False
    tem_proximidade = False

    if m_pos is not None and v_pos is not None:
        diferenca = abs(m_pos - v_pos)
        if diferenca >= 8:  # Exemplo: Grande diferença de posições (G4 x Z4)
            tem_disparidade = True
        elif diferenca <= 3: # Exemplo: Times muito próximos na tabela
            tem_proximidade = True

    # ==========================================================
    # AVALIAÇÃO DE OVERS (Favorecido por Disparidade/Topo vs Fundo)
    # ==========================================================
    if pct_15 >= 80 and (not m_pos or not v_pos or tem_disparidade or m_pos < 10):
        overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})

    if pct_25 == 100 and tem_disparidade:
        overs_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})

    # ==========================================================
    # AVALIAÇÃO DE UNDERS (Favorecido por Proximidade na Tabela)
    # ==========================================================
    if tem_proximidade and pct_m45 >= 60:
        unders_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})

    if tem_proximidade and pct_m35 >= 60:
        unders_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})

    # Retorno padrão de exclusão mútua
    if overs_aprovados:
        return overs_aprovados
    else:
        return unders_aprovados
