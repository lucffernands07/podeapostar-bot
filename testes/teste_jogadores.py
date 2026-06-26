# 🟢 LISTA BRANCA: Apenas ligas de elite que comprovadamente abrem mercados de jogadores na Betano
LIGAS_ELITE_JOGADORES = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Brasileirão Série B", "Argentina - Liga Profesional", "Mundo - Copa do Mundo",
    "Copa do Mundo",
    "Champions League", "Inglaterra - Premier League", "Espanha - LaLiga",
    "Alemanha - Bundesliga", "Italia - Serie A", "França - Ligue 1",
    "Europa - League", "Inglaterra - FA Cup", "Espanha - Copa del Rey",
    "Alemanha - DFB Pokal", "Portugal - Primeira Liga", "Países Baixos - Eredivisie",
    "Mundo - Amistoso Internacional"
]

def verificar_destaques_jogadores(historico_chutes, quantidade_jogos=3, nome_liga="", elenco_casa=None, elenco_fora=None):
    """
    Analisa os destaques de chutes, garantindo 1 jogador do Mandante e 1 do Visitante.
    """
    if isinstance(quantidade_jogos, dict):
        quantidade_jogos = 3

    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_JOGADORES:
        return []

    mercados_aprovados = []
    dados_chutes = {}
    
    if not isinstance(historico_chutes, dict) or not historico_chutes:
        return mercados_aprovados

    # 1. PROCESSAMENTO COMPLETO
    for jogador, lista_valores in historico_chutes.items():
        if not isinstance(lista_valores, list):
            continue
            
        valores_copia = list(lista_valores)
        while len(valores_copia) < quantidade_jogos:
            valores_copia.append(0)
            
        valores_analise = valores_copia[:quantidade_jogos]
        media = sum(valores_analise) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in valores_analise if qtd >= 1)
        
        # Identifica o time (se os elencos forem passados, senão divide por ordem de aparição)
        time_pertence = "casa"
        if elenco_fora and jogador in elenco_fora:
            time_pertence = "fora"
        elif elenco_casa and jogador in elenco_casa:
            time_pertence = "casa"

        dados_chutes[jogador] = {
            "media": media, 
            "jogos_com_sucesso": games_sucesso := jogos_com_sucesso, 
            "valores": valores_analise,
            "time": time_pertence
        }

    if dados_chutes:
        # Ordena por sucesso e média
        jogadores_ordenados = sorted(
            dados_chutes.keys(), 
            key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), 
            reverse=True
        )
        
        # 🟢 SELEÇÃO BALANCEADA: Pega o melhor de cada lado
        top_casa = [j for j in jogadores_ordenados if dados_chutes[j]["time"] == "casa"]
        top_fora = [j for j in jogadores_ordenados if dados_chutes[j]["time"] == "fora"]
        
        # Se os elencos não vieram definidos por parâmetro, dividimos a lista original ao meio como fallback de segurança
        if not elenco_casa and not elenco_fora:
            metade = len(jogadores_ordenados) // 2
            top_casa = jogadores_ordenados[:metade]
            top_fora = jogadores_ordenados[metade:]

        selecionados = []
        if top_casa: selecionados.append(top_casa[0])
        if top_fora: selecionados.append(top_fora[0])
        
        for jogador in selecionados:
            res_c = dados_chutes[jogador]
            if res_c["jogos_com_sucesso"] >= 2 or res_c["media"] >= 1.0:
                mercados_aprovados.append({
                    "texto": f"Chutes no Alvo: {jogador} (Frequência: {res_c['jogos_com_sucesso']}/{quantidade_jogos}j | Méd: {res_c['media']:.1f})",
                    "chave": "CHUTES_ALVO"
                })

    return mercados_aprovados


def verificar_destaques_faltas(historico_faltas, quantidade_jogos=3, nome_liga="", elenco_casa=None, elenco_fora=None):
    """
    Garante o melhor de faltas do mandante e o melhor do visitante no confronto.
    """
    if isinstance(quantidade_jogos, dict):
        quantidade_jogos = 3

    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_JOGADORES:
        return []

    mercados_aprovados = []
    dados_faltas = {}
    
    if not isinstance(historico_faltas, dict) or not historico_faltas:
        return mercados_aprovados

    # 1. PROCESSAMENTO DE MÉDIAS
    for jogador, lista_valores in historico_faltas.items():
        if not isinstance(lista_valores, list):
            continue
            
        valores_copia = list(lista_valores)
        while len(valores_copia) < quantidade_jogos:
            valores_copia.append(0)
            
        valores_analise = valores_copia[:quantidade_jogos]
        media = sum(valores_analise) / quantidade_jogos
        
        time_pertence = "casa"
        if elenco_fora and jogador in elenco_fora:
            time_pertence = "fora"
        elif elenco_casa and jogador in elenco_casa:
            time_pertence = "casa"

        dados_faltas[jogador] = {
            "media": media,
            "valores": valores_analise,
            "time": time_pertence
        }

    # 2. SELEÇÃO BALANCEADA (1 Mandante + 1 Visitante)
    if dados_faltas:
        jogadores_ordenados = sorted(
            dados_faltas.keys(), 
            key=lambda k: dados_faltas[k]["media"], 
            reverse=True
        )
        
        top_casa = [j for j in jogadores_ordenados if dados_faltas[j]["time"] == "casa"]
        top_fora = [j for j in jogadores_ordenados if dados_faltas[j]["time"] == "fora"]

        if not elenco_casa and not elenco_fora:
            metade = len(jogadores_ordenados) // 2
            top_casa = jogadores_ordenados[:metade]
            top_fora = jogadores_ordenados[metade:]

        selecionados = []
        if top_casa: selecionados.append(top_casa[0])
        if top_fora: selecionados.append(top_fora[0])
        
        for jogador in selecionados:
            res_f = dados_faltas[jogador]
            if res_f["media"] > 0.5:
                mercados_aprovados.append({
                    "texto": f"Faltas Sofridas: {jogador} (Méd: {res_f['media']:.1f})",
                    "chave": "FALTAS_SOFRIDAS"
                })

    return mercados_aprovados
    
