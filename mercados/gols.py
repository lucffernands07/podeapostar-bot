"""
REGRAS DE MERCADO - GOLS (REESTRUTURAÇÃO COMPLETA)
1. Filtro Inicial de Recorrência: Exige no mínimo 4/5 para todos os mercados (+1.5, +2.5 e -4.5).
2. Trava de H2H Mandatória: O último jogo do confronto direto DEVE bater o mercado escolhido.
3. Decisão por Maior Confiança: Ganha o mercado que atingir a maior porcentagem (%).
4. Critério de Desempate Estrito: Se houver empate na %, a prioridade de saída é: -4.5 ➔ +1.5 ➔ +2.5.
"""

def verificar_ultimo_jogo(gols_placar_texto, alvo):
    try:
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

def calcular_porcentagem_gols(c, f, ultimo_h2h, alvo):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    # ➔ PASSO 1: Exige no mínimo 4/5 para ambos os times
    if c < 4 or f < 4:
        return 0

    # ➔ PASSO 2: O último confronto direto (H2H) DEVE bater o mercado
    if not verificar_ultimo_jogo(ultimo_h2h, alvo):
        return 0

    # Se passou nas travas, calcula o peso da % (5/5 e 5/5 = 100%, mistos ou 4/5 = 85%)
    if c == 5 and f == 5:
        return 100
    return 85

def verificar_gols(s):
    """
    Recebe o dicionário 's' do main.py e processa a hierarquia exata solicitada
    """
    if not isinstance(s, dict):
        return []

    # Extração segura do placar em texto do último confronto direto (H2H)
    u_h2h = s.get("h2h_placar_1", "")

    # Mapeamento e cálculo das porcentagens de cada mercado seguindo os Passos 1 e 2
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0), u_h2h, 4.5)
    pct_15  = calcular_porcentagem_gols(s.get("casa_15", 0), s.get("fora_15", 0), u_h2h, 1.5)
    pct_25  = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0), u_h2h, 2.5)

    # ➔ PASSO 3 & 4: Escolha baseada em Maior Porcentagem com Desempate por Prioridade
    # Criamos uma lista ordenada estritamente pela sua regra de desempate (-4.5 > +1.5 > +2.5)
    candidatos = [
        {"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45", "pct": pct_m45, "prioridade": 3},
        {"mercado": f"+1.5 Gols ({pct_15}%)",  "tipo": "GOLS_15",  "pct": pct_15,  "prioridade": 2},
        {"mercado": f"+2.5 Gols ({pct_25}%)",  "tipo": "GOLS_25",  "pct": pct_25,  "prioridade": 1}
    ]

    # Filtra apenas quem passou nos critérios (porcentagem maior que zero)
    aprovados = [c for c in candidatos if c["pct"] > 0]

    if not aprovados:
        return []

    # Ordena primeiro pela maior Porcentagem (Passo 3) e depois pela Prioridade (Passo 4)
    # O Python ordena de forma crescente, então invertemos com reverse=True
    aprovados.sort(key=lambda x: (x["pct"], x["prioridade"]), reverse=True)

    # Pega o vencedor absoluto do topo da esteira
    vencedor = aprovados[0]

    # Retorna o formato correto exigido pelo seu robô
    return [{"mercado": vencedor["mercado"], "tipo": vencedor["tipo"]}]
    
