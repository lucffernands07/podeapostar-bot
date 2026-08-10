# mercados/vitorias.py
from mercados.chance_dupla import verificar_chance_dupla  # Importa a regra de chance dupla

def verificar_vitorias(stats):
    """
    Regras de Vitória Casa e Vitória Fora.
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

    # Captura das métricas do dicionário
    vitorias_casa = int(stats.get("casa_vitorias_recente", 0) or 0)
    vitorias_fora = int(stats.get("fora_vitorias_recente", 0) or 0)
    
    derrotas_fora = int(stats.get("visitante_derrotas_fora", 0) or 0)
    sem_derrota_fora = int(stats.get("visitante_sem_derrota_fora", 0) or 0)
    gols_sofridos_fora = float(stats.get("visitante_gols_sofridos_fora", 0) or 0)

    # -----------------------------------------------------------------
    # 🏠 VITÓRIA CASA (Padrão América de Cali, Rapid Vienna, Palmeiras)
    # -----------------------------------------------------------------
    condicao_casa = (vitorias_casa >= 4) and (derrotas_fora >= 3 and gols_sofridos_fora >= 8)

    if condicao_casa:
        pct = "100%" if vitorias_casa == 5 else ("85%" if vitorias_casa == 4 else "70%")
        retorno.append(f"Vitória Casa ({pct})")

    # -----------------------------------------------------------------
    # ✈️ VITÓRIA FORA (Padrão Barracas Central, Gimnasia L.P.)
    # -----------------------------------------------------------------
    condicao_fora = (gols_sofridos_fora <= 5 and sem_derrota_fora >= 4) and (vitorias_casa == 0)

    if condicao_fora:
        pct = "100%" if vitorias_fora == 5 else ("85%" if vitorias_fora == 4 else "70%")
        retorno.append(f"Vitória Fora ({pct})")

    return retorno
    
