import re
from . import jogadores # Importa o módulo onde fica a trava de validação de liga elite

def analisar_dados_escanteios(cantos_mandante_h2h, cantos_visitante_h2h, nome_liga="", quantidade_jogos=3, dados_incompletos=False):
    """
    Processa os históricos de escanteios totais coletados na nova raspagem.
    Retorna estritamente o valor médio final combinado dos últimos jogos se for liga elite.
    """
    nome_liga_limpo = nome_liga.strip() if nome_liga else "Liga Não Informada"

    # 🟢 TRAVA DE SEGURANÇA: Validação da Liga Elite antes de processar
    permite_coletivos = jogadores.validar_liga_para_jogadores(nome_liga_limpo)
    if not permite_coletivos:
        print(f"      ⏩ [OTIMIZAÇÃO ESCANTEIOS] Pulando média de escanteios para {nome_liga_limpo} (Não é liga Elite).")
        return {"aprovado": False}

    # Garante que possuímos a amostragem completa de jogos passados exigida
    if len(cantos_mandante_h2h) < quantidade_jogos or len(cantos_visitante_h2h) < quantidade_jogos:
        print(f"⏩ [HISTÓRICO INCOMPLETO] Dados de escanteios insuficientes para o confronto.")
        return {"aprovado": False}

    # 🚨 BLINDAGEM: Converte todos os valores extraídos para INT limpando possíveis espaços ou strings
    try:
        jogos_mandante_total = [int(str(x).strip()) for x in cantos_mandante_h2h[:quantidade_jogos]]
        jogos_visitante_total = [int(str(x).strip()) for x in cantos_visitante_h2h[:quantidade_jogos]]
    except Exception as e_conv:
        print(f"⚠️ [ERRO CONVERSÃO] Erro ao converter dados de cantos para números: {e_conv}")
        return {"aprovado": False}

    # 🛑 🚨 TRAVA DE DADOS ZERADOS/INCOMPLETOS:
    # Descarta se a flag do scraper veio True OU se qualquer jogo das duas listas contiver 0
    if dados_incompletos or (0 in jogos_mandante_total) or (0 in jogos_visitante_total):
        print(f"⏩ [DESCARTADO] Jogo com estatísticas de escanteio ausentes/zeradas: Mandante {jogos_mandante_total} | Visitante {jogos_visitante_total}")
        return {"aprovado": False}

    # --- CÁLCULO DAS MÉDIAS REAIS ---
    total_cantos_acumulados = sum(jogos_mandante_total) + sum(jogos_visitante_total)
    media_geral_confronto = total_cantos_acumulados / (quantidade_jogos * 2)

    # 🛑 REGRA DE SEGURANÇA: Descarta se a média combinada for menor que 4.0
    if media_geral_confronto < 4.0:
        print(f"⏩ [REJEITADO] Média de escanteios muito baixa ({media_geral_confronto:.2f}). Confronto descartado.")
        return {"aprovado": False}

    # Média isolada para auditoria
    media_historico_mandante = sum(jogos_mandante_total) / quantidade_jogos
    media_historico_visitante = sum(jogos_visitante_total) / quantidade_jogos

    # 📊 TEXTO SIMPLIFICADO: Retorna apenas o rótulo com o valor exato da média combinada
    texto_mercado = f"Média Escanteios: {media_geral_confronto:.1f}"

    # Log detalhado para monitorar a execução no terminal
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
    
