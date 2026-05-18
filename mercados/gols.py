"""
REGRAS DE MERCADO - GOLS
1. Prioridade Máxima: -4.5 Gols se o jogo for estatisticamente "Under" (Sem tendência de Over).
2. Over 1.5/2.5 (100% / 85%): Ativado por aprovação direta se ambos os times tiverem recorrência mínima de 4/5 nos últimos 5 jogos.
3. Over 1.5/2.5 (70%): Ativado apenas se um dos times tiver exatamente 3/5 e o outro tiver no mínimo 4/5, exigindo validação de Over no último jogo de ambos.
4. Filtro de Segurança: Evita sugerir Over e Under no mesmo jogo para manter a coerência do bilhete.
"""
"""
REGRAS DE MERCADO - GOLS (CORREÇÃO: STRING INDICES ERROR)
"""

def verificar_ultimo_jogo(gols_time, alvo):
    try:
        # Garante que gols_time seja tratado como número
        g_t = int(gols_time)
        if alvo == 1.5: return g_t >= 2
        if alvo == 2.5: return g_t >= 3
        if alvo == 4.5: return g_t <= 4
    except:
        return False
    return False

def calcular_chance_v2(c, f, ultimo_c, ultimo_f, alvo):
    # Força os valores para inteiros para evitar erro de string
    try:
        c, f = int(c), int(f)
    except:
        return None

    # --- REGRA 1: AMBOS COM NO MÍNIMO 4/5 (APROVAÇÃO DIRETA) ---
    if c >= 4 and f >= 4:
        if c == 5 and f == 5: return "100%"
        return "85%"
    
    # --- REGRA 2: UM TIME COM 3/5 E O OUTRO COM NO MÍNIMO 4/5 + ÚLTIMO JOGO ---
    # Traduzindo: (Casa tem 3 E Fora >= 4) OU (Fora tem 3 E Casa >= 4)
    combinacao_valida = (c == 3 and f >= 4) or (f == 3 and c >= 4)
    
    if combinacao_valida:
        if verificar_ultimo_jogo(ultimo_c, alvo) and verificar_ultimo_jogo(ultimo_f, alvo):
            return "70%"
            
    return None

def verificar_gols(s):
    """
    Recebe o dicionário 's' do main.py
    """
    if not isinstance(s, dict):
        return []

    # Extração segura dos dados
    u_c = s.get("ultimo_gols_casa", 0)
    u_f = s.get("ultimo_gols_fora", 0)

    # Cálculo das chances
    ch15 = calcular_chance_v2(s.get("casa_15", 0), s.get("fora_15", 0), u_c, u_f, 1.5)
    ch25 = calcular_chance_v2(s.get("casa_25", 0), s.get("fora_25", 0), u_c, u_f, 2.5)
    ch45_under = calcular_chance_v2(s.get("casa_45_under", 0), s.get("fora_45_under", 0), u_c, u_f, 4.5)
    
    resultados = []

    if ch25:
        resultados.append({"mercado": f"+2.5 Gols ({ch25})", "tipo": "GOLS_25"})
    elif ch15:
        resultados.append({"mercado": f"+1.5 Gols ({ch15})", "tipo": "GOLS_15"})
    
    if ch45_under and not ch15:
        # MUDE DE 'UNDER_45' PARA 'GOLS_M45'
        resultados.append({"mercado": f"-4.5 Gols ({ch45_under})", "tipo": "GOLS_M45"}) 

    return resultados
