"""
REGRAS DE MERCADO - VITÓRIAS (CASA / FORA) USANDO TRAVA H2H (2025/2026)
Mercado de maior risco: exige rigor estatístico superior à Chance Dupla baseado no confronto direto.
"""

def verificar_vitorias(s):
    """
    Recebe o dicionário 's' (contendo os dados do H2H do Superscore) 
    e retorna mercados de Vitórias aprovados (Vitória Casa ou Vitória Fora).
    Se ambos baterem ou se as condições não forem estritamente fortes, descarta.
    """
    mercados_aprovados = []
    if not isinstance(s, dict):
        return mercados_aprovados

    # --- CAPTURA DE DADOS DO H2H (2025/2026, Máx 5 jogos) ---
    h2h_total = int(s.get("h2h_jogos_total", 0) or 0)
    vitorias_t1 = int(s.get("h2h_vitorias_t1", 0) or 0)      # Vitórias do Mandante no H2H
    vitorias_t2 = int(s.get("h2h_vitorias_t2", 0) or 0)      # Vitórias do Visitante no H2H
    empates = int(s.get("h2h_empates", 0) or 0)              # Empates no H2H

    # Se não houver histórico H2H válido para os anos recentes, descarta por segurança
    if h2h_total == 0:
        return []

    tem_vitoria_casa = False
    tem_vitoria_fora = False

    # ----------------------------------------------------------
    # 🟢 REGRA VITÓRIA CASA (Nível Acima da Dupla Chance 1X)
    # Exige superioridade clara do mandante nos confrontos diretos recentes
    # ----------------------------------------------------------
    # Exemplo de trava rigorosa: Mandante venceu a maioria e o visitante não venceu nenhuma
    condicao_vitoria_casa = (vitorias_t1 >= 3) and (vitorias_t2 == 0)

    if condicao_vitoria_casa:
        tem_vitoria_casa = True

    # ----------------------------------------------------------
    # 🟢 REGRA VITÓRIA FORA (Nível Acima da Dupla Chance X2)
    # Exige superioridade clara do visitante nos confrontos diretos recentes
    # ----------------------------------------------------------
    condicao_vitoria_fora = (vitorias_t2 >= 3) and (vitorias_t1 == 0)

    if condicao_vitoria_fora:
        tem_vitoria_fora = True

    # ----------------------------------------------------------
    # 🛑 TRAVA DE DESCARTE MÚTUO
    # Se os dois lados apontarem vitória seca, o jogo é inconclusivo e anula.
    # ----------------------------------------------------------
    if tem_vitoria_casa and tem_vitoria_fora:
        print(f"      ⚠️ CONFLITO DE VITÓRIAS (H2H): Vitória Casa e Vitória Fora passaram juntas. Jogo descartado.")
        return []

    if tem_vitoria_casa:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Casa", 
            "tipo": "VITORIA_CASA"
        })
    
    if tem_vitoria_fora:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Fora", 
            "tipo": "VITORIA_FORA"
        })

    return mercados_aprovados
