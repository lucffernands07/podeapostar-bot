"""
REGRAS DE MERCADO - GOLS (VERSÃO 2.0)
Regra 1: Mínimo 4/5 em ambos os times (Confiança Direta).
Regra 2 (Backup): 3/5 em ambos + Validação do último jogo individual (Soma de gols).
"""

def verificar_ultimo_jogo(gols_time, alvo):
    """
    Valida se o último jogo individual atingiu a meta do mercado.
    Ex: Para +1.5, o último jogo precisa ter >= 2 gols.
    """
    if alvo == 1.5: return gols_time >= 2
    if alvo == 2.5: return gols_time >= 3
    if alvo == 4.5: return gols_time <= 4 # Para o mercado de Under
    return False

def calcular_chance_v2(c, f, ultimo_c, ultimo_f, alvo):
    """
    Aplica a nova regra de filtragem:
    - Regra 1: 4/5 ou 5/5 em ambos.
    - Regra 2: 3/5 em ambos + validação do último jogo.
    """
    # REGRA 1: Mínimo 4/5 ambos (Independente do último jogo)
    if c >= 4 and f >= 4:
        if c == 5 and f == 5: return "100%"
        return "85%"
    
    # REGRA 2: 3/5 em ambos + Último jogo individual batendo a meta
    if c >= 3 and f >= 3:
        passou_casa = verificar_ultimo_jogo(ultimo_c, alvo)
        passou_fora = verificar_ultimo_jogo(ultimo_f, alvo)
        
        if passou_casa and passou_fora:
            return "70%"
            
    return None

def verificar_gols(s):
    """
    Analisa os mercados de gols com base nas estatísticas e resultados recentes.
    """
    # 1. Captura de dados (Soma de gols do ÚLTIMO JOGO de cada um)
    # Certifique-se que o main.py envia 'ultimo_gols_casa' e 'ultimo_gols_fora'
    u_c = s.get("ultimo_gols_casa", 0)
    u_f = s.get("ultimo_gols_fora", 0)

    # 2. Cálculos de probabilidade
    ch15 = calcular_chance_v2(s.get("casa_15", 0), s.get("fora_15", 0), u_c, u_f, 1.5)
    ch25 = calcular_chance_v2(s.get("casa_25", 0), s.get("fora_25", 0), u_c, u_f, 2.5)
    ch45_under = calcular_chance_v2(s.get("casa_45_under", 0), s.get("fora_45_under", 0), u_c, u_f, 4.5)
    
    resultados = []

    # --- LÓGICA DE PRIORIDADE ---

    # PRIORIDADE 1: -4.5 GOLS (UNDER)
    if ch45_under and not ch15:
        resultados.append({
            "mercado": "-4.5 Gols",
            "confianca": ch45_under,
            "tipo": "UNDER"
        })
        return resultados

    # PRIORIDADE 2: +1.5 GOLS
    if ch15:
        resultados.append({
            "mercado": "+1.5 Gols",
            "confianca": ch15,
            "tipo": "OVER_15"
        })
    
    # PRIORIDADE 3: +2.5 GOLS
    if ch25:
        resultados.append({
            "mercado": "+2.5 Gols",
            "confianca": ch25,
            "tipo": "OVER_25"
        })

    return resultados
    
