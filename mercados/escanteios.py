import re

def analisar_dados_escanteios(cantos_mandante_h2h, cantos_visitante_h2h, nome_liga="", quantidade_jogos=3, dados_incompletos=False):
    nome_liga_limpo = nome_liga.strip() if nome_liga else "Liga Não Informada"

    # Trava: Quantidade mínima de partidas coletadas
    if len(cantos_mandante_h2h) < quantidade_jogos or len(cantos_visitante_h2h) < quantidade_jogos:
        return {"aprovado": False}

    if dados_incompletos:
        return {"aprovado": False}

    try:
        jogos_mandante_total = [int(str(x).strip()) for x in cantos_mandante_h2h[:quantidade_jogos]]
        jogos_visitante_total = [int(str(x).strip()) for x in cantos_visitante_h2h[:quantidade_jogos]]
    except Exception:
        return {"aprovado": False}

    # Validações individuais e separadas por Mandante e Visitante
    aprovado_mandante = False
    aprovado_visitante = False

    # 1. Análise Mandante
    if any(m == 0 for m in jogos_mandante_total):
        pass
    else:
        media_mandante = sum(jogos_mandante_total) / quantidade_jogos
        if media_mandante >= 2.0: # Ajuste o critério individual se necessário
            aprovado_mandante = True

    # 2. Análise Visitante
    if any(v == 0 for v in jogos_visitante_total):
        pass
    else:
        media_visitante = sum(jogos_visitante_total) / quantidade_jogos
        if media_visitante >= 2.0: # Ajuste o critério individual se necessário
            aprovado_visitante = True

    # Se nenhum dos dois passar individualmente, rejeita o todo
    if not aprovado_mandante and not aprovado_visitante:
        return {"aprovado": False}

    total_mandante = sum(jogos_mandante_total)
    total_visitante = sum(jogos_visitante_total)
    total_cantos_acumulados = total_mandante + total_visitante
    media_geral_confronto = total_cantos_acumulados / (quantidade_jogos * 2)

    media_historico_mandante = total_mandante / quantidade_jogos
    media_historico_visitante = total_visitante / quantidade_jogos

    texto_mercado = f"Média Escanteios: {media_geral_confronto:.1f}"

    log_detalhado = (
        f"  🏟️ {nome_liga_limpo}\n"
        f"  ➔ Média nos jogos do Mandante: {media_historico_mandante:.2f} cantos {jogos_mandante_total}\n"
        f"  ➔ Média nos jogos do Visitante: {media_historico_visitante:.2f} cantos {jogos_visitante_total}\n"
        f"  ➔ Média Geral Combinada: {media_geral_confronto:.2f}\n"
    )

    return {
        "aprovado": True,
        "tipo": "ESCANTEIOS_GERAL", # 🔑 Chave mantida para compatibilidade
        "tipo_mandante": "ESCANTEIOS_MANDANTE",
        "tipo_visitante": "ESCANTEIOS_VISITANTE",
        "aprovado_mandante": aprovado_mandante,
        "aprovado_visitante": aprovado_visitante,
        "total_mandante": total_mandante,
        "total_visitante": total_visitante,
        "total_confronto": total_cantos_acumulados,
        "media_confronto": round(media_geral_confronto, 2),
        "mercado": texto_mercado, 
        "log_detalhado_cantos": log_detalhado
    }
