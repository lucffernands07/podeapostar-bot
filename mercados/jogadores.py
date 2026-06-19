# mercados/jogadores.py

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

def verificar_destaques_jogadores(historico_chutes, historico_faltas, quantidade_jogos=3, nome_liga=""):
    """
    Processa os históricos brutos extraídos pelo Selenium.
    🛡️ ADICIONADA TRAVA DE LISTA BRANCA PARA LIGAS DE ELITE.
    """
    # 🚀 TRAVA: Se a liga atual NÃO estiver na lista branca, barra na hora
    if nome_liga and nome_liga not in LIGAS_ELITE_JOGADORES:
        print(f"⏩ [TRAVA] Pulando análise de jogadores para a liga '{nome_liga}' (Não é considerada liga Elite para jogadores).")
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

    # 📉 REGRA: FALTAS SOFRIDAS
    dados_faltas = {}
    for jogador, lista_valores in historico_faltas.items():
        while len(lista_valores) < quantidade_jogos:
            lista_valores.append(0)
            
        media = sum(lista_valores) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in lista_valores if qtd >= 1)
        dados_faltas[jogador] = {"media": media, "jogos_com_sucesso": jogos_com_sucesso}

    if dados_faltas:
        mais_cacado = max(dados_faltas, key=lambda k: (dados_faltas[k]["jogos_com_sucesso"], dados_faltas[k]["media"]))
        res_f = dados_faltas[mais_cacado]
        
        if res_f["jogos_com_sucesso"] >= 2 or res_f["media"] >= 1.0:
            mercados_aprovados.append({
                "texto": f"Faltas Sofridas: {mais_cacado} (Frequência: {res_f['jogos_com_sucesso']}/{quantidade_jogos}j | Méd: {res_f['media']:.1f})",
                "chave": "FALTAS_SOFRIDAS"
            })

    return mercados_aprovados
            
