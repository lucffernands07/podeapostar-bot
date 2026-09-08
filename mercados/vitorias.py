"""
REGRAS DE MERCADO - VITÓRIAS (CASA / FORA) ATUALIZADO
- Vitória Casa: 
  * 3 vitórias seguidas do mandante em casa.
  * Média de gols feitos pelo mandante >= 2.0 nos últimos 3 jogos em casa.
  * Média de gols sofridos pelo visitante >= 2.0 nos últimos 3 jogos fora.
- Vitória Fora: 
  * 3 vitórias seguidas do visitante fora.
  * Média de gols feitos pelo visitante >= 2.0 nos últimos 3 jogos fora.
  * Média de gols sofridos pelo mandante >= 2.0 nos últimos 3 jogos em casa.
- Trava de Descarte Mútuo: Se ambos passarem, o jogo é descartado.
"""

def verificar_vitorias(s):
    mercados_aprovados = []
    if not isinstance(s, dict):
        return mercados_aprovados

    # --- 1. CAPTURA DOS DADOS DOS 3 ÚLTIMOS JOGOS ---
    try:
        # Mandante em casa (1 = mais recente, 3 = mais antigo)
        m_gf1 = int(s.get("t1_gols_favor_1", 0) or 0)
        m_gc1 = int(s.get("t1_gols_contra_1", 0) or 0)
        
        m_gf2 = int(s.get("t1_gols_favor_2", 0) or 0)
        m_gc2 = int(s.get("t1_gols_contra_2", 0) or 0)
        
        m_gf3 = int(s.get("t1_gols_favor_3", 0) or 0)
        m_gc3 = int(s.get("t1_gols_contra_3", 0) or 0)

        # Visitante fora (1 = mais recente, 3 = mais antigo)
        v_gf1 = int(s.get("t2_gols_favor_1", 0) or 0)
        v_gc1 = int(s.get("t2_gols_contra_1", 0) or 0)
        
        v_gf2 = int(s.get("t2_gols_favor_2", 0) or 0)
        v_gc2 = int(s.get("t2_gols_contra_2", 0) or 0)
        
        v_gf3 = int(s.get("t2_gols_favor_3", 0) or 0)
        v_gc3 = int(s.get("t2_gols_contra_3", 0) or 0)
    except:
        return []

    # --- 2. VALIDAÇÃO DE RESULTADOS (3 VITÓRIAS SEGUIDAS) ---
    m_vitoria_1 = m_gf1 > m_gc1
    m_vitoria_2 = m_gf2 > m_gc2
    m_vitoria_3 = m_gf3 > m_gc3
    mandante_3_vitorias = m_vitoria_1 and m_vitoria_2 and m_vitoria_3

    v_vitoria_1 = v_gf1 > v_gc1
    v_vitoria_2 = v_gf2 > v_gc2
    v_vitoria_3 = v_gf3 > v_gc3
    visitante_3_vitorias = v_vitoria_1 and v_vitoria_2 and v_vitoria_3

    # --- 3. CÁLCULO DE MÉDIAS DOS ÚLTIMOS 3 JOGOS ---
    # Gols Feitos
    media_gf_mandante = (m_gf1 + m_gf2 + m_gf3) / 3.0
    media_gf_visitante = (v_gf1 + v_gf2 + v_gf3) / 3.0

    # Gols Sofridos (Gols Contra)
    media_gc_mandante = (m_gc1 + m_gc2 + m_gc3) / 3.0
    media_gc_visitante = (v_gc1 + v_gc2 + v_gc3) / 3.0

    tem_vitoria_casa = False
    tem_vitoria_fora = False

    # ----------------------------------------------------------
    # 🟢 REGRA VITÓRIA CASA
    # Mandante 3 vitórias em casa + Média gols feitos >= 2.0
    # Visitante com média de gols sofridos fora >= 2.0
    # ----------------------------------------------------------
    if mandante_3_vitorias and (media_gf_mandante >= 2.0) and (media_gc_visitante >= 2.0):
        tem_vitoria_casa = True

    # ----------------------------------------------------------
    # 🟢 REGRA VITÓRIA FORA
    # Visitante 3 vitórias fora + Média gols feitos >= 2.0
    # Mandante com média de gols sofridos em casa >= 2.0
    # ----------------------------------------------------------
    if visitante_3_vitorias and (media_gf_visitante >= 2.0) and (media_gc_mandante >= 2.0):
        tem_vitoria_fora = True

    # ----------------------------------------------------------
    # 🛑 TRAVA DE DESCARTE MÚTUO
    # ----------------------------------------------------------
    if tem_vitoria_casa and tem_vitoria_fora:
        print(f"      ⚠️ CONFLITO DE VITÓRIAS: Vitória Casa e Fora passaram juntas. Jogo descartado.")
        return []

    # Adiciona os mercados aprovados
    if tem_vitoria_casa:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Casa", 
            "tipo": "VITORIA_CASA"
        })
    
    if tem_vitoria_fora:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Fora", 
            "tipo": "VITORIA_FORA"
        })

    return mercados_aprovados
    
