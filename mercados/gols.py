"""
REGRAS DE MERCADO - GOLS (CASA EM CASA / VISITANTE FORA)
1. Filtro Inicial de Recorrência Estrita: Ambos os times devem ter NO MÍNIMO 4/5 no recorte recente.
2. Multi-Mercado: Retorna todos os mercados que passarem nos filtros simultaneamente (+1.5, +2.5, -3.5, -4.5).
"""

def calcular_porcentagem_gols(c, f):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    # ➔ PASSO 1: Regra Estrita (Ambos no mínimo 4 de 5)
    if c < 4 or f < 4:
        return 0

    # ➔ PASSO 2: Definição de Confiança
    if c == 5 and f == 5:
        return 100
        
    return 80  # Retorna 80% para (4 e 4) ou (4 e 5)

def verificar_gols(s):
    """
    Recebe o dicionário 's' e retorna TODOS os mercados de gols 
    que passarem simultaneamente no filtro de recorrência (mínimo 4/5 para ambos).
    """
    if not isinstance(s, dict):
        return []

    # Mapeamento e cálculo das porcentagens de cada mercado com os dados filtrados de Casa/Fora
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0))
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("fora_35_under", 0))
    pct_15  = calcular_porcentagem_gols(s.get("casa_15", 0), s.get("fora_15", 0))
    pct_25  = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))

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
    
