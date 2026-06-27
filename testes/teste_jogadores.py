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
    Analisa os destaques de chutes, garantindo 1 jogador do Mandante e 1 do Visitante sem duplicar.
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
        
        # Identifica o time com fallback dinâmico inteligente
        time_pertence = "casa"
        if elenco_fora and jogador in elenco_fora:
            time_pertence = "fora"
        elif elenco_casa and jogador in elenco_casa:
            time_pertence = "casa"
        else:
            # 🟢 FALLBACK: Se o scraper falhar na string do nome por conta de acentos/abreviação,
            # olhamos se o jogador possui histórico preenchido na janela correspondente ao visitante.
            # (Últimos índices da lista indicam jogos capturados na seção 2 do H2H)
            meio = len(valores_copia) // 2
            if sum(valores_copia[meio:]) > sum(valores_copia[:meio]):
                time_pertence = "fora"

        dados_chutes[jogador] = {
            "media": media, 
            "jogos_com_sucesso": jogos_com_sucesso, 
            "valores": valores_analise,
            "time": time_pertence
        }

    if dados_chutes:
        jogadores_ordenados = sorted(
            dados_chutes.keys(), 
            key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), 
            reverse=True
        )
        
        # SELEÇÃO SEPARADA POR TIME
        top_casa = [j for j in jogadores_ordenados if dados_chutes[j]["time"] == "casa"]
        top_fora = [j for j in jogadores_ordenados if dados_chutes[j]["time"] == "fora"]
        
        selecionados = []
        
        # Se os elencos mapeados não existirem ou falharem em separar os lados, faz a divisão justa no ranking
        if not top_casa or not top_fora:
            if jogadores_ordenados:
                selecionados.append(jogadores_ordenados[0])  # O melhor absoluto (Geralmente Mandante)
            # Varre o ranking para achar o primeiro jogador que pertença ou se comporte como o outro lado
            for j in jogadores_ordenados[1:]:
                if dados_chutes[j]["time"] != dados_chutes[jogadores_ordenados[0]]["time"]:
                    selecionados.append(j)
                    break
            # Margem de segurança caso todos caiam no mesmo balde padrão
            if len(selecionados) < 2 and len(jogadores_ordenados) > 1:
                selecionados.append(jogadores_ordenados[1])
        else:
            # Se temos os dois lados mapeados com sucesso, pega o top 1 de cada
            if top_casa: selecionados.append(top_casa[0])
            if top_fora: selecionados.append(top_fora[0])

        # Remove qualquer duplicata residual por segurança absoluta
        selecionados = list(dict.fromkeys(selecionados))
        
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
    Garante o melhor de faltas do mandante e o melhor do visitante no confronto sem duplicações.
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
        
        # Identifica o time com fallback dinâmico inteligente
        time_pertence = "casa"
        if elenco_fora and jogador in elenco_fora:
            time_pertence = "fora"
        elif elenco_casa and jogador in elenco_casa:
            time_pertence = "casa"
        else:
            meio = len(valores_copia) // 2
            if sum(valores_copia[meio:]) > sum(valores_copia[:meio]):
                time_pertence = "fora"

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

        selecionados = []
        
        # Tratamento de Fallback robusto se os blocos caírem no mesmo lado por falta de string idêntica
        if not top_casa or not top_fora:
            if jogadores_ordenados:
                selecionados.append(jogadores_ordenados[0])
            for j in jogadores_ordenados[1:]:
                if dados_faltas[j]["time"] != dados_faltas[jogadores_ordenados[0]]["time"]:
                    selecionados.append(j)
                    break
            if len(selecionados) < 2 and len(jogadores_ordenados) > 1:
                selecionados.append(jogadores_ordenados[1])
        else:
            if top_casa: selecionados.append(top_casa[0])
            if top_fora: selecionados.append(top_fora[0])

        selecionados = list(dict.fromkeys(selecionados))
        
        for jogador in selecionados:
            res_f = dados_faltas[jogador]
            if res_f["media"] > 0.5:
                mercados_aprovados.append({
                    "texto": f"Faltas Sofridas: {jogador} (Méd: {res_f['media']:.1f})",
                    "chave": "FALTAS_SOFRIDAS"
                })

    return mercados_aprovados
    
