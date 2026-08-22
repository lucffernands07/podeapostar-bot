"""
REGRAS DE MERCADO - CHANCE DUPLA (1X / X2) USANDO TRAVA H2H (2025/2026)
O filtro de confronto direto (H2H) é exigido como trava para validar o mercado.
Com regra de descarte mútuo: se ambos passarem, os dois são eliminados.
"""

def verificar_chance_dupla(s):
    """
    Recebe o dicionário 's' (contendo os dados do H2H do Superscore) 
    e retorna mercados de Chance Dupla aprovados (1X ou X2).
    Se ambos forem verdadeiros, ambos são descartados.
    """
    if not isinstance(s, dict):
        return []

    # --- CAPTURA DE DADOS DO H2H (2025/2026, Máx 5 jogos) ---
    h2h_total = int(s.get("h2h_jogos_total", 0) or 0)
    vitorias_t1 = int(s.get("h2h_vitorias_t1", 0) or 0)      # Vitórias do Mandante no H2H
    vitorias_t2 = int(s.get("h2h_vitorias_t2", 0) or 0)      # Vitórias do Visitante no H2H
    empates = int(s.get("h2h_empates", 0) or 0)              # Empates no H2H

    # Se não houver jogos suficientes no H2H para validar a regra, já retorna vazio
    if h2h_total == 0:
        return []

    # Jogos em que o mandante pontuou no H2H (Vitórias + Empates)
    mandante_sem_derrota_h2h = vitorias_t1 + empates
    # Jogos em que o visitante pontuou no H2H (Vitórias + Empates)
    visitante_sem_derrota_h2h = vitorias_t2 + empates

    # Variáveis de controle para testar cada lado de forma independente
    tem_1x = False
    tem_x2 = False
    pct_1x = 80
    pct_x2 = 80

    # ----------------------------------------------------------
    # 🟢 REGRA 1X (Casa ou Empate no H2H)
    # Trava: O mandante não perdeu a maioria dos confrontos diretos recentes
    # ----------------------------------------------------------
    # Exemplo de regra baseada na proporção ou quantidade dos últimos confrontos diretos
    condicao_1x = (mandante_sem_derrota_h2h >= 3) and (vitorias_t2 == 0 or vitorias_t1 >= vitorias_t2)

    if condicao_1x:
        tem_1x = True
        pct_1x = 100 if mandante_sem_derrota_h2h == h2h_total else 80

    # ----------------------------------------------------------
    # 🟢 REGRA X2 (Fora ou Empate no H2H)
    # Trava: O visitante não perdeu a maioria dos confrontos diretos recentes
    # ----------------------------------------------------------
    condicao_x2 = (visitante_sem_derrota_h2h >= 3) and (vitorias_t1 == 0 or vitorias_t2 >= vitorias_t1)

    if condicao_x2:
        tem_x2 = True
        pct_x2 = 100 if visitante_sem_derrota_h2h == h2h_total else 80

    # ----------------------------------------------------------
    # 🛑 TRAVA DE DESCARTE MÚTUO
    # Se os dois baterem no mesmo jogo, anula os dois (retorna vazio).
    # ----------------------------------------------------------
    if tem_1x and tem_x2:
        print(f"      ⚠️ CONFLITO DE CHANCE DUPLA (H2H): 1X e X2 passaram juntos. Jogo descartado.")
        return []

    # Se apenas um passou, adiciona ele normalmente à lista
    mercados_aprovados = []
    if tem_1x:
        mercados_aprovados.append({"mercado": f"Dupla Chance: 1X ({pct_1x}%)", "tipo": "DC_1X"})
    if tem_x2:
        mercados_aprovados.append({"mercado": f"Dupla Chance: X2 ({pct_x2}%)", "tipo": "DC_X2"})

    return mercados_aprovados
