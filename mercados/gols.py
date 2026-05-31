"""
REGRAS DE MERCADO - GOLS (ATUALIZADO)
1. Prioridade Máxima: -4.5 Gols se o jogo for estatisticamente "Under" (Sem tendência de Over).
2. Over 1.5/2.5 (100% / 85%): Requer recorrência mínima de 4/5 nos últimos 5 jogos E obrigatoriamente +1.5/+2.5 no último jogo do H2H.
3. Over 1.5/2.5 (70%): Ativado se um dos times tiver exatamente 3/5 e o outro no mínimo 4/5, exigindo validação de Over no último jogo de ambos E no último H2H.
4. Filtro de Segurança: Evita sugerir Over e Under no mesmo jogo para manter a coerência do bilhete.
"""

def verificar_ultimo_jogo(gols_placar_texto, alvo):
    try:
        # Usa regex para extrair os números do texto do placar (ex: "3-1" -> [3, 1])
        import re
        numeros = re.findall(r'\d+', str(gols_placar_texto))
        if len(numeros) < 2: return False
        
        g_t = int(numeros[0]) + int(numeros[1])
        
        if alvo == 1.5: return g_t >= 2
        if alvo == 2.5: return g_t >= 3
        if alvo == 4.5: return g_t <= 4
    except:
        return False
    return False

def calcular_chance_v3(c, f, ultimo_c, ultimo_f, ultimo_h2h, alvo):
    try:
        c, f = int(c), int(f)
    except:
        return None

    # 🔒 TRAVA MANDATÓRIA: Independente da porcentagem (100%, 85% ou 70%), 
    # o último jogo do H2H TEM que bater o alvo de gols.
    if alvo in [1.5, 2.5]:
        if not verificar_ultimo_jogo(ultimo_h2h, alvo):
            return None

    # --- REGRA 1: AMBOS COM NO MÍNIMO 4/5 (APROVAÇÃO DIRETA) ---
    if c >= 4 and f >= 4:
        if c == 5 and f == 5: return "100%"
        return "85%"
    
    # --- REGRA 2: UM TIME COM 3/5 E O OUTRO COM NO MÍNIMO 4/5 + ÚLTIMO JOGO ---
    combinacao_valida = (c == 3 and f >= 4) or (f == 3 and c >= 4)
    
    if combinacao_valida:
        # Valida o último jogo isolado de cada time
        if verificar_ultimo_jogo(str(ultimo_c), alvo) and verificar_ultimo_jogo(str(ultimo_f), alvo):
            return "70%"
            
    return None

def verificar_gols(s):
    """
    Recebe o dicionário 's' do main.py
    """
    if not isinstance(s, dict):
        return []

    # Extração segura dos dados de gols dos últimos jogos isolados
    u_c = s.get("ultimo_gols_casa", 0)
    u_f = s.get("ultimo_gols_fora", 0)
    
    # Extração do placar em texto do último confronto direto (H2H)
    u_h2h = s.get("h2h_placar_1", "")

    # Cálculo das chances passando o u_h2h como novo critério
    ch15 = calcular_chance_v3(s.get("casa_15", 0), s.get("fora_15", 0), u_c, u_f, u_h2h, 1.5)
    ch25 = calcular_chance_v3(s.get("casa_25", 0), s.get("fora_25", 0), u_c, u_f, u_h2h, 2.5)
    
    # Para o Under 4.5, mantemos a lógica anterior (não exige a trava de Over do H2H)
    try:
        c_45 = int(s.get("casa_45_under", 0))
        f_45 = int(s.get("fora_45_under", 0))
        ch45_under = "85%" if (c_45 >= 4 and f_45 >= 4) else None
    except:
        ch45_under = None
    
    resultados = []

    if ch25:
        resultados.append({"mercado": f"+2.5 Gols ({ch25})", "tipo": "GOLS_25"})
    elif ch15:
        resultados.append({"mercado": f"+1.5 Gols ({ch15})", "tipo": "GOLS_15"})
    
    if ch45_under and not ch15:
        resultados.append({"mercado": f"-4.5 Gols ({ch45_under})", "tipo": "GOLS_M45"}) 

    return resultados
    
