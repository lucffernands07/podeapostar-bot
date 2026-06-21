# 🟢 LISTA BRANCA: Apenas ligas de elite que comprovadamente abrem mercados de jogadores na Betano
LIGAS_ELITE_JOGADORES = [
    "Brasileirão Série A",
    "Copa do Brasil",
    "Libertadores",
    "Sul-Americana",
    "Brasileirão Série B",           # Costuma abrir em rodadas cheias
    "Argentina - Liga Profesional",
    "Mundo - Copa do Mundo",
    "Champions League",
    "Inglaterra - Premier League",
    "Espanha - LaLiga",
    "Alemanha - Bundesliga",
    "Italia - Serie A",
    "França - Ligue 1",
    "Europa - League",
    "Inglaterra - FA Cup",
    "Espanha - Copa del Rey",
    "Alemanha - DFB Pokal",
    "Portugal - Primeira Liga",
    "Países Baixos - Eredivisie",
    "Mundo - Amistoso Internacional" # Amistosos de seleções principais abrem mercado
]

def verificar_destaques_jogadores(historico_chutes, quantidade_jogos=3, nome_liga=""):
    """
    Processa os históricos brutos extraídos pelo Selenium (Aba Finalizações).
    🛡️ ADICIONADA TRAVA DE LISTA BRANCA PARA LIGAS DE ELITE.
    """
    # 🚀 TRAVA REMODELADA: Se o nome vier vazio ou NÃO estiver estritamente na lista branca, barra na hora
    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_JOGADORES:
        # Fallback visual caso o nome venha nulo do scraper principal
        liga_print = nome_liga_limpo if nome_liga_limpo else "NOME_DA_LIGA_VAZIO"
        print(f"⏩ [TRAVA] Pulando análise de jogadores para a liga '{liga_print}' (Não é considerada liga Elite ou string inválida).")
        return []

    mercados_aprovados = []
    
    # 📈 REGRA: CHUTES NO ALVO
    dados_chutes = {}
    for jogador, lista_valores in historico_chutes.items():
        while len(lista_valores) < quantidade_jogos:
            lista_valores.append(0)
            
        media = sum(lista_valores) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in lista_valores if qtd >= 1)
        dados_chutes[jogador] = {"media": media, "jogos_com_sucesso": jogos_com_sucesso}

    if dados_chutes:
        melhor_chutador = max(dados_chutes, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]))
        res_c = dados_chutes[melhor_chutador]
        
        if res_c["jogos_com_sucesso"] >= 2 or res_c["media"] >= 1.0:
            mercados_aprovados.append({
                "texto": f"Chutes no Alvo: {melhor_chutador} (Frequência: {res_c['jogos_com_sucesso']}/{quantidade_jogos}j | Méd: {res_c['media']:.1f})",
                "chave": "CHUTES_ALVO"
            })

    return mercados_aprovados
