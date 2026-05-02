"""
REGRAS DE MERCADO - GOLS (VERSÃO FINAL)
Regra 1: Mínimo 4/5 INDIVIDUAL em ambos os times (Aprovação Direta).
Regra 2: Se não passar na R1, aceita 3/5 se o ÚLTIMO JOGO de ambos atingiu a meta.
"""

def verificar_ultimo_jogo(gols_time, alvo):
    """
    Valida se o último jogo individual atingiu a meta do mercado.
    """
    if alvo == 1.5: return gols_time >= 2
    if alvo == 2.5: return gols_time >= 3
    if alvo == 4.5: return gols_time <= 4 # Para o mercado de Under
    return False

def calcular_chance_v2(c, f, ultimo_c, ultimo_f, alvo):
    """
    Aplica a lógica de filtragem solicitada:
    - Regra 1: 4/5 ou 5/5 em cada um dos times (Casa >= 4 E Fora >= 4).
    - Regra 2: Se cair para 3/5, exige que o último jogo individual de cada um bata a meta.
    """
    
    # --- REGRA 1: 4/5 AMBOS (APROVAÇÃO DIRETA) ---
    if c >= 4 and f >= 4:
        if c == 5 and f == 5: return "100%"
        return "85%"
    
    # --- REGRA 2: 3/5 AMBOS + ÚLTIMO JOGO (VALIDAÇÃO) ---
    if c >= 3 and f >= 3:
        # Verifica se o último jogo de CADA UM bateu a meta (Ex: +1.5 gols = 2 gols no jogo)
        passou_casa = verificar_ultimo_jogo(ultimo_c, alvo)
        passou_fora = verificar_ultimo_jogo(ultimo_f, alvo)
        
        if passou_casa and passou_fora:
            return "70%"
            
    return None

def verificar_gols(s):
    """
    Analisa os mercados de gols com base nas estatísticas brutas (Individual e H2H).
    """
    # Gols dos últimos jogos individuais
    u_c = s.get("ultimo_gols_casa", 0)
    u_f = s.get("ultimo_gols_fora", 0)

    # Probabilidades
    ch15 = calcular_chance_v2(s.get("casa_15", 0), s.get("fora_15", 0), u_c, u_f, 1.5)
    ch25 = calcular_chance_v2(s.get("casa_25", 0), s.get("fora_25", 0), u_c, u_f, 2.5)
    ch45_under = calcular_chance_v2(s.get("casa_45_under", 0), s.get("fora_45_under", 0), u_c, u_f, 4.5)
    
    resultados = []

    # --- LÓGICA DE PRIORIDADE ---

    # 1. UNDER 4.5 (Prioridade de Segurança)
    if ch45_under and not ch15:
        resultados.append({
            "mercado": "-4.5 Gols",
            "confianca": ch45_under,
            "tipo": "UNDER"
        })
        return resultados

    # 2. OVER 1.5
    if ch15:
        resultados.append({
            "mercado": "+1.5 Gols",
            "confianca": ch15,
            "tipo": "OVER_15"
        })
    
    # 3. OVER 2.5
    if ch25:
        resultados.append({
            "mercado": "+2.5 Gols",
            "confianca": ch25,
            "tipo": "OVER_25"
        })

    return resultados
    
