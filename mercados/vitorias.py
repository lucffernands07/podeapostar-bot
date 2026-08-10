# mercados/vitorias.py
from mercados.chance_dupla import verificar_chance_dupla  # Importa a regra de chance dupla

def verificar_vitorias(stats):
    """
    Regras de Vitória Casa e Vitória Fora padronizadas com as chaves do chance_dupla.py.
    Trava de Segurança: Se o jogo for aprovado em Chance Dupla (1X ou X2), 
    os mercados de Vitória Simples são descartados.
    """
    retorno = []
    
    if not isinstance(stats, dict):
        return retorno

    # 🛑 TRAVA DE SEGURANÇA: Se tem Chance Dupla, descarta Vitória Simples
    chance_dupla_aprovada = verificar_chance_dupla(stats)
    if chance_dupla_aprovada:
        return []  # Retorna vazio, anulando a vitória simples para este jogo

    # Captura das métricas unificadas no padrão de chance_dupla.py
    mandante_vitorias_casa = int(stats.get("mandante_vitorias_casa", 0) or 0)
    visitante_vitorias_fora = int(stats.get("visitante_vitorias_fora", 0) or 0) # Padronizado
    
    visitante_derrotas_fora = int(stats.get("visitante_derrotas_fora", 0) or 0)
    visitante_sem_derrota_fora = int(stats.get("visitante_sem_derrota_fora", 0) or 0)
    visitante_gols_sofridos_fora = float(stats.get("visitante_gols_sofridos_fora", 0) or 0)

    # -----------------------------------------------------------------
    # 🏠 VITÓRIA CASA 
    # -----------------------------------------------------------------
    condicao_casa = (mandante_vitorias_casa >= 4) and (visitante_derrotas_fora >= 3 and visitante_gols_sofridos_fora >= 8)

    if condicao_casa:
        pct = "100%" if mandante_vitorias_casa == 5 else ("85%" if mandante_vitorias_casa == 4 else "70%")
        retorno.append(f"Vitória Casa ({pct})")

    # -----------------------------------------------------------------
    # ✈️ VITÓRIA FORA 
    # -----------------------------------------------------------------
    condicao_fora = (visitante_gols_sofridos_fora <= 5 and visitante_sem_derrota_fora >= 4) and (mandante_vitorias_casa == 0)

    if condicao_fora:
        pct = "100%" if visitante_vitorias_fora == 5 else ("85%" if visitante_vitorias_fora == 4 else "70%")
        retorno.append(f"Vitória Fora ({pct})")

    return retorno
    
