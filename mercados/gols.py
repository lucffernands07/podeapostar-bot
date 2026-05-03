"""
REGRAS DE MERCADO - GOLS (TOTALMENTE SINCRONIZADO COM MAIN.PY)
Regra 1: Mínimo 4/5 INDIVIDUAL em ambos os times (Aprovação Direta).
Regra 2: Se cair para 3/5, exige que o ÚLTIMO JOGO de ambos tenha atingido a meta.
"""

def verificar_ultimo_jogo(gols_time, alvo):
    """
    Valida se o último jogo individual atingiu a meta numérica do mercado.
    """
    try:
        if alvo == 1.5: return gols_time >= 2
        if alvo == 2.5: return gols_time >= 3
        if alvo == 4.5: return gols_time <= 4
    except:
        return False
    return False

def calcular_chance_v2(c, f, ultimo_c, ultimo_f, alvo):
    """
    Aplica a lógica de filtragem usando as chaves do main.py:
    - Regra 1: 4/5 ou 5/5 em cada um dos times (Aprovação Direta).
    - Regra 2: 3/5 exige validação do valor numérico do último jogo.
    """
    
    # --- REGRA 1: 4/5 AMBOS (APROVAÇÃO DIRETA) ---
    # Ex: Flamengo 5/5 e Vasco 4/5 -> Entra aqui com 85%
    if c >= 4 and f >= 4:
        if c == 5 and f == 5: return "100%"
        return "85%"
    
    # --- REGRA 2: 3/5 AMBOS + ÚLTIMO JOGO (VALIDAÇÃO) ---
    if c >= 3 and f >= 3:
        passou_casa = verificar_ultimo_jogo(ultimo_c, alvo)
        passou_fora = verificar_ultimo_jogo(ultimo_f, alvo)
        
        if passou_casa and passou_fora:
            return "70%"
            
    return None

def verificar_gols(s):
    """
    Analisa os mercados usando as chaves EXATAS do stats do main.py.
    """
    # Gols numéricos extraídos na linha 106 do seu main.py
    u_c = s.get("ultimo_gols_casa", 0)
    u_f = s.get("ultimo_gols_fora", 0)

    # Probabilidades usando chaves exatas: casa_15, casa_25, casa_45_under
    ch15 = calcular_chance_v2(s.get("casa_15", 0), s.get("fora_15", 0), u_c, u_f, 1.5)
    ch25 = calcular_chance_v2(s.get("casa_25", 0), s.get("fora_25", 0), u_c, u_f, 2.5)
    ch45_under = calcular_chance_v2(s.get("casa_45_under", 0), s.get("fora_45_under", 0), u_c, u_f, 4.5)
    
    resultados = []

    # --- LÓGICA DE PRIORIDADE E FORMATAÇÃO ---

    # 1. OVER 1.5 (Identificado no main.py por "+1.5")
    if ch15:
        resultados.append({
            "mercado": f"+1.5 Gols ({ch15})",
            "tipo": "OVER_15"
        })
    
    # 2. OVER 2.5 (Identificado no main.py por "+2.5")
    if ch25:
        resultados.append({
            "mercado": f"+2.5 Gols ({ch25})",
            "tipo": "OVER_25"
        })

    # 3. UNDER 4.5 (Identificado no main.py por "-4.5")
    # Só entra se não houver tendência forte de muitos gols (opcional)
    if ch45_under and not ch25:
        resultados.append({
            "mercado": f"-4.5 Gols ({ch45_under})",
            "tipo": "UNDER"
        })

    return resultados
                          
