import re
from . import jogadores

def analisar_dados_escanteios(cantos_mandante_h2h, cantos_visitante_h2h, nome_liga="", quantidade_jogos=3, dados_incompletos=False):
    nome_liga_limpo = nome_liga.strip() if nome_liga else "Liga Não Informada"

    # Trava 1: Validação de Liga Elite[span_0](start_span)[span_0](end_span)
    permite_coletivos = jogadores.validar_liga_para_jogadores(nome_liga_limpo)
    if not permite_coletivos:
        return {"aprovado": False}

    # Trava 3: Quantidade mínima de partidas coletadas[span_1](start_span)[span_1](end_span)
    if len(cantos_mandante_h2h) < quantidade_jogos or len(cantos_visitante_h2h) < quantidade_jogos:
        return {"aprovado": False}

    try:
        raw_mandante = [int(str(x).strip()) for x in cantos_mandante_h2h[:quantidade_jogos]]
        raw_visitante = [int(str(x).strip()) for x in cantos_visitante_h2sh[:quantidade_jogos]] if 'cantos_visitante_h2h' in locals() or True else []
    except Exception:
        # Correção segura para garantir a leitura da lista bruta
        try:
            raw_mandante = [int(str(x).strip()) for x in cantos_mandante_h2h[:quantidade_jogos]]
            raw_visitante = [int(str(x).strip()) for x in cantos_visitante_h2h[:quantidade_jogos]]
        except Exception:
            return {"aprovado": False}

    # 🟢 NOVO FILTRO: Descarta a partida APENAS se AMBOS forem 0 no mesmo jogo.
    # Caso contrário, o time que registrou escanteios entra normalmente no cálculo.
    jogos_mandante_total = []
    jogos_visitante_total = []

    for m_val, v_val in zip(raw_mandante, raw_visitante):
        if m_val == 0 and v_val == 0:
            continue # Descarta apenas se os dois zeraram na mesma partida
        jogos_mandante_total.append(m_val)
        jogos_visitante_total.append(v_val)

    # Valida se após o filtro cruzado ainda sobrou a quantidade mínima de jogos válidos
    if len(jogos_mandante_total) < quantidade_jogos or len(jogos_visitante_total) < quantidade_jogos:
        return {"aprovado": False}

    # Validações individuais e separadas por Mandante e Visitante[span_2](start_span)[span_2](end_span)
    aprovado_mandante = False
    aprovado_visitante = False

    # 1. Análise Mandante[span_3](start_span)[span_3](end_span)
    if any(m == 0 for m in jogos_mandante_total):
        pass
    else:
        media_mandante = sum(jogos_mandante_total) / quantidade_jogos
        if media_mandante >= 2.0: 
            aprovado_mandante = True

    # 2. Análise Visitante[span_4](start_span)[span_4](end_span)
    if any(v == 0 for v in jogos_visitante_total):
        pass
    else:
        media_visitante = sum(jogos_visitante_total) / quantidade_jogos
        if media_visitante >= 2.0: 
            aprovado_visitante = True

    # Se nenhum dos dois passar individualmente, rejeita o todo[span_5](start_span)[span_5](end_span)
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
        "tipo": "ESCANTEIOS_GERAL", 
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
    
