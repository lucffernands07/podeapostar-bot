import re
from . import jogadores

def analisar_dados_escanteios(cantos_mandante_h2h, cantos_visitante_h2h, nome_liga="", quantidade_jogos=3, dados_incompletos=False):
    nome_liga_limpo = nome_liga.strip() if nome_liga else "Liga Não Informada"

    # Trava 1: Validação de Liga Elite
    permite_coletivos = jogadores.validar_liga_para_jogadores(nome_liga_limpo)
    if not permite_coletivos:
        return {"aprovado": False}

    # Trava 3: Quantidade mínima de partidas coletadas
    if len(cantos_mandante_h2h) < quantidade_jogos or len(cantos_visitante_h2h) < quantidade_jogos:
        return {"aprovado": False}

    try:
        jogos_mandante_total = [int(str(x).strip()) for x in cantos_mandante_h2h[:quantidade_jogos]]
        jogos_visitante_total = [int(str(x).strip()) for x in cantos_visitante_h2h[:quantidade_jogos]]
    except Exception:
        return {"aprovado": False}

    # 🛑 TRAVA: Se em QUALQUER partida o TOTAL combinando Mandante + Visitante for 0, descarta!
    for m, v in zip(jogos_mandante_total, jogos_visitante_total):
        if (m + v) == 0:
            print(f"⏩ [DESCARTADO ESCANTEIOS] Partida com total de escanteios zerado ({m} + {v} = 0) para {nome_liga_limpo}.")
            return {"aprovado": False}

    total_cantos_acumulados = sum(jogos_mandante_total) + sum(jogos_visitante_total)
    media_geral_confronto = total_cantos_acumulados / (quantidade_jogos * 2)

    if media_geral_confronto < 4.0:
        return {"aprovado": False}

    media_historico_mandante = sum(jogos_mandante_total) / quantidade_jogos
    media_historico_visitante = sum(jogos_visitante_total) / quantidade_jogos

    texto_mercado = f"Média Escanteios: {media_geral_confronto:.1f}"

    log_detalhado = (
        f"  🏟️ {nome_liga_limpo}\n"
        f"  ➔ Média nos jogos do Mandante: {media_historico_mandante:.2f} cantos {jogos_mandante_total}\n"
        f"  ➔ Média nos jogos do Visitante: {media_historico_visitante:.2f} cantos {jogos_visitante_total}\n"
        f"  ➔ Média Geral Combinada: {media_geral_confronto:.2f}\n"
    )

    return {
        "aprovado": True,
        "total_mandante": sum(jogos_mandante_total),
        "total_visitante": sum(jogos_visitante_total),
        "total_confronto": total_cantos_acumulados,
        "media_confronto": round(media_geral_confronto, 2),
        "mercado": texto_mercado, 
        "log_detalhado_cantos": log_detalhado
    }
    
