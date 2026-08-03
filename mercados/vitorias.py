# mercados/vitorias.py

def verificar_vitorias(stats):
    """
    Regras de Vitória Casa e Vitória Fora baseadas nos 7 exemplos reais:
    
    - Vitória Casa: Mandante competitivo (>= 3 vitórias) AND 
                    (Visitante perdeu >= 3 jogos fora OU levou >= 8 gols fora).
                    
    - Vitória Fora: Visitante sólido na defesa (<= 6 gols sofridos fora AND >= 3 jogos sem perder) AND 
                    (Mandante com 0 vitórias em casa OU Visitante com >= 3 vitórias fora).
    """
    retorno = []
    
    if not isinstance(stats, dict):
        return retorno

    # Captura das métricas do dicionário
    vitorias_casa = int(stats.get("casa_vitorias_recente", 0) or 0)
    vitorias_fora = int(stats.get("fora_vitorias_recente", 0) or 0)
    
    derrotas_fora = int(stats.get("visitante_derrotas_fora", 0) or 0)
    sem_derrota_fora = int(stats.get("visitante_sem_derrota_fora", 0) or 0)
    gols_sofridos_fora = float(stats.get("visitante_gols_sofridos_fora", 0) or 0)

    # -----------------------------------------------------------------
    # 🏠 VITÓRIA CASA (Padrão América de Cali, Rapid Vienna, Palmeiras)
    # -----------------------------------------------------------------
    condicao_casa = (vitorias_casa >= 3) and (derrotas_fora >= 3 or gols_sofridos_fora >= 8)

    if condicao_casa:
        pct = "100%" if vitorias_casa == 5 else ("85%" if vitorias_casa == 4 else "70%")
        retorno.append(f"Vitória Casa ({pct})")

    # -----------------------------------------------------------------
    # ✈️ VITÓRIA FORA (Padrão Barracas Central, Gimnasia L.P.)
    # -----------------------------------------------------------------
    condicao_fora = (gols_sofridos_fora <= 6 and sem_derrota_fora >= 3) and (vitorias_casa == 0 or vitorias_fora >= 3)

    if condicao_fora:
        pct = "100%" if vitorias_fora == 5 else ("85%" if vitorias_fora == 4 else "70%")
        retorno.append(f"Vitória Fora ({pct})")

    return retorno
    
