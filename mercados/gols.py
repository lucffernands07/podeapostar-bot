"""
REGRAS DE MERCADO - GOLS (REESTRUTURAÇÃO COMPLETA)
1. Filtro Inicial de Recorrência Estrita: Ambos os times devem ter NO MÍNIMO 4/5.
2. Trava de H2H Mandatória: [DESATIVADA] Não exige mais histórico de confronto direto.
3. Multi-Mercado: Retorna todos os mercados que passarem nos filtros simultaneamente.
"""

def verificar_ultimo_jogo(gols_placar_texto, alvo):
    # Função mantida para compatibilidade
    try:
        import re
        placar_limpo = re.sub(r'\(\d+\)', '', str(gols_placar_texto))
        numeros = re.findall(r'\d+', placar_limpo)
        if len(numeros) < 2: return False
        
        g_t = int(numeros[0]) + int(numeros[1])
        
        if alvo == 1.5: return g_t >= 2
        if alvo == 2.5: return g_t >= 3
        if alvo == 3.5: return g_t <= 3  # Máximo 3 gols
        if alvo == 4.5: return g_t <= 4
    except:
        return False
    return False

def calcular_porcentagem_gols(c, f, ultimo_h2h, alvo):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    # ➔ PASSO 1: Regra Estrita (Ambos no mínimo 4 de 5)
    if c < 4 or f < 4:
        return 0

    # ➔ PASSO 2: Trava de Confronto Direto (H2H) - DESATIVADA
    # if not verificar_ultimo_jogo(ultimo_h2h, alvo):
    #     return 0

    # --- DEFINIÇÃO DAS ETIQUETAS DE PORCENTAGEM PARA O RANKING ---
    if c == 5 and f == 5:
        return 100
        
    return 80  # Retorna 80% para (4 e 4) ou (4 e 5)

def verificar_gols(s):
    """
    Recebe o dicionário 's' do main.py e retorna TODOS os mercados de gols 
    que passarem simultaneamente no filtro de recorrência (mínimo 4/5 para ambos).
    """
    if not isinstance(s, dict):
        return []

    # Extração segura do placar em texto do último confronto direto (H2H)
    u_h2h = s.get("h2h_placar_1", "")

    # Mapeamento e cálculo das porcentagens de cada mercado
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0), u_h2h, 4.5)
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("fora_35_under", 0), u_h2h, 3.5)
    pct_15  = calcular_porcentagem_gols(s.get("casa_15", 0), s.get("fora_15", 0), u_h2h, 1.5)
    pct_25  = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0), u_h2h, 2.5)

    mercados_aprovados = []

    # Adiciona os mercados válidos
    if pct_m45 > 0:
        mercados_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})
        
    if pct_m35 > 0:
        mercados_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})
        
    if pct_15 > 0:
        mercados_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})
        
    if pct_25 > 0:
        mercados_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})

    return mercados_aprovados
