"""
REGRAS DE MERCADO - GOLS
1. Prioridade Máxima: -4.5 Gols se o jogo for estatisticamente "Under" (Sem tendência de Over).
2. Over 1.5/2.5: Ativado apenas se a recorrência combinada for de 4/5 (70%) ou 5/5 (85%-100%).
3. Filtro de Segurança: Evita sugerir Over e Under no mesmo jogo para manter a coerência do bilhete.
4. Independência: Não utiliza travas manuais do último jogo, focando na média estatística dos últimos 5.
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

    # --- REGRA 1: 4/5 AMBOS (APROVAÇÃO DIRETA) ---
    if c >= 4 and f >= 4:
        if c == 5 and f == 5: return "100%"
        return "85%"
    
    # --- REGRA 2: 3/5 AMBOS + ÚLTIMO JOGO ---
    if c >= 3 and f >= 3:
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
