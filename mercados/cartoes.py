import re

# 🟢 LISTA BRANCA: Apenas ligas de elite que comprovadamente abrem mercados de jogadores na Betano
LIGAS_ELITE_JOGADORES = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Brasileirão Série B", "Argentina - Liga Profesional", "Mundo - Copa do Mundo",
    "Europa - Champions League", "Inglaterra - Premier League", "Espanha - LaLiga",
    "Alemanha - Bundesliga", "Italia - Serie A", "França - Ligue 1",
    "Europa - League", "Inglaterra - FA Cup", "Espanha - Copa del Rey",
    "Alemanha - DFB Pokal", "Portugal - Primeira Liga", "Países Baixos - Eredivisie",
    "Mundo - Amistoso Internacional"
]

def analisar_dados_cartoes(historico_mandante_am, historico_mandante_vm, historico_visitante_am, historico_visitante_vm, nome_liga="", quantidade_jogos=3):
    """
    Processa os históricos brutos de cartões (já filtrados e isolados por time pelo main).
    Calcula médias reais por atleta e a média coletiva somando as médias de cada time.
    """
    # 🚀 TRAVA DE LIGA ELITE
    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_CARTOES:
        liga_print = nome_liga_limpo if nome_liga_limpo else "NOME_DA_LIGA_VAZIO"
        print(f"⏩ [TRAVA] Pulando análise de cartões para a liga '{liga_print}' (Não é considerada liga Elite ou string inválida).")
        return {}

    total_cartoes_mandante = 0
    total_cartoes_visitante = 0
    jogo_global_index = quantidade_jogos * 2 # 6 jogos no total considerando os dois blocos de 3

    # Configuração para varrer e tratar cada time (Mandante: índices 0 a 3 | Visitante: índices 3 a 6)
    config_times = [
        {"dict_am": historico_mandante_am, "dict_vm": historico_mandante_vm, "inicio_idx": 0, "fim_idx": quantidade_jogos, "tipo": "MANDANTE"},
        {"dict_am": historico_visitante_am, "dict_vm": historico_visitante_vm, "inicio_idx": quantidade_jogos, "fim_idx": jogo_global_index, "tipo": "VISITANTE"}
    ]

    relatorio_jogadores = ""

    for config in config_times:
        if not config["dict_am"]:
            continue
            
        for jogador, lista_amarelos in config["dict_am"].items():
            lista_vermelhos = config["dict_vm"].get(jogador, [])
            
            # Normaliza o tamanho preenchendo eventuais buracos
            while len(lista_amarelos) < jogo_global_index:
                lista_amarelos.append(0)
            while len(lista_vermelhos) < jogo_global_index:
                lista_vermelhos.append(0)
                
            # Soma amarelo + vermelho rodada por rodada
            lista_combinada = [lista_amarelos[x] + lista_vermelhos[x] for x in range(jogo_global_index)]
            
            # Recorta cirurgicamente apenas as partidas que pertencem a esta seleção no array global
            jogos_reais = lista_combinada[config["inicio_idx"]:config["fim_idx"]]
            am_reais = lista_amarelos[config["inicio_idx"]:config["fim_idx"]]
            vm_reais = lista_vermelhos[config["inicio_idx"]:config["fim_idx"]]
            
            soma_jogador = sum(jogos_reais)
            if config["tipo"] == "MANDANTE":
                total_cartoes_mandante += soma_jogador
            else:
                total_cartoes_visitante += soma_jogador
            
            media_real = soma_jogador / quantidade_jogos
            
            if soma_jogador > 0:
                relatorio_jogadores += f"  👤 {jogador.ljust(25)} ➔ Média Real: {media_real:.2f} cartões/jogo {jogos_reais} (Am: {am_reais} | Vm: {vm_reais})\n"

    # --- CÁLCULO DAS MÉDIAS REAIS ---
    media_mandante = total_cartoes_mandante / quantidade_jogos if quantidade_jogos > 0 else 0
    media_visitante = total_cartoes_visitante / quantidade_jogos if quantidade_jogos > 0 else 0
    media_geral_confronto = media_mandante + media_visitante

    # 📊 DEFINIÇÃO DA LINHA BASE FLUTUANTE (VALOR NUMÉRICO COM SINAL COMERCIAL)
    if media_geral_confronto >= 4.0:
        linha_base = 3.5  # Representa +3.5
        sinal = "+"
    elif media_geral_confronto >= 3.0:
        linha_base = 2.5  # Representa +2.5
        sinal = "+"
    elif media_geral_confronto >= 2.0:
        linha_base = -3.5 # Representa -3.5
        sinal = "-"
    else:
        linha_base = -2.5 # Representa -2.5
        sinal = "-"

    # 🟢 SUA REGRA MATEMÁTICA PERFEITA: Subtrai 1.0 de qualquer linha!
    if sinal == "-":
        linha_final = linha_base - 1.0  # Ex: -2.5 - 1 = -3.5
        texto_mercado = f"Cartões Totais: {linha_final}"
    else:
        linha_final = linha_base - 1.0  # Ex: 3.5 - 1 = 2.5
        texto_mercado = f"Cartões Totais: +{linha_final}"

    # Retorna o dicionário no formato padrão consumido pelo banco de dados do bot
    return {
        "aprovado": True,
        "total_mandante": total_cartoes_mandante,
        "total_visitante": total_cartoes_visitante,
        "total_confronto": total_cartoes_mandante + total_cartoes_visitante, # 🟢 Corrigido aqui!
        "media_confronto": round(media_geral_confronto, 2),
        "mercado": texto_mercado, 
        "log_detalhado_jogadores": relatorio_jogadores
    }
