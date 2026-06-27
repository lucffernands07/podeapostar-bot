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
    Analisa os destaques de chutes, GARANTINDO o melhor do Mandante e o melhor do Visitante.
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

    for jogador, lista_valores in historico_chutes.items():
        if not isinstance(lista_valores, list):
            continue
            
        valores_copia = list(lista_valores)
        
        # 🟢 IDENTIFICAÇÃO DO TIME POR POSIÇÃO NO HISTÓRICO (À prova de falhas)
        # Se a lista tem mais elementos que a quantidade de jogos (ex: 6 posições),
        # significa que os jogos do visitante estão no final da lista.
        time_pertence = "casa"
        if len(valores_copia) > quantidade_jogos:
            # Se a soma da segunda metade for maior ou se os primeiros jogos forem zerados
            meio = len(valores_copia) // 2
            if sum(valores_copia[meio:]) > 0 and sum(valores_copia[:meio]) == 0:
                time_pertence = "fora"
            valores_analise = valores_copia[:quantidade_jogos] if time_pertence == "casa" else valores_copia[meio:meio+quantidade_jogos]
        else:
            # Fallback por strings de elenco se a lista for curta
            if elenco_fora and jogador in elenco_fora:
                time_pertence = "fora"
            elif elenco_casa and jogador in elenco_casa:
                time_pertence = "casa"
            valores_analise = valores_copia

        while len(valores_analise) < quantidade_jogos:
            valores_analise.append(0)
            
        valores_analise = valores_analise[:quantidade_jogos]
        media = sum(valores_analise) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in valores_analise if qtd >= 1)
        
        dados_chutes[jogador] = {
            "media": media, 
            "jogos_com_sucesso": jogos_com_sucesso, 
            "time": time_pertence
        }

    if dados_chutes:
        # Separa os jogadores em duas listas reais baseado no time identificado
        jogadores_casa = [j for j in dados_chutes.keys() if dados_chutes[j]["time"] == "casa"]
        jogadores_fora = [j for j in dados_chutes.keys() if dados_chutes[j]["time"] == "fora"]
        
        # 🟢 SE NINGUÉM CAIU NO FORA (Sinal de que elencos falharam e a lista veio unificada de tamanho curto)
        # Forçamos uma separação real por amostragem pareada, e não cortando a pior metade
        if not jogadores_fora and len(jogadores_casa) > 1:
            # Ordena geral
            geral_ordenado = sorted(dados_chutes.keys(), key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)
            # O primeiro vai para a casa, o segundo melhor vai para o visitante para garantir o confronto
            jogadores_casa = [geral_ordenado[0]]
            jogadores_fora = [geral_ordenado[1]]

        # Ordena cada lado de forma independente pelos melhores desempenhos
        top_casa = sorted(jogadores_casa, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)
        top_fora = sorted(jogadores_fora, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)

        selecionados = []
        if top_casa: selecionados.append(top_casa[0])
        if top_fora: selecionados.append(top_fora[0])
        
        # Remove duplicados redundantes
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
    Garante o melhor de faltas do mandante e o melhor do visitante sem misturar os rankings.
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

    for jogador, lista_valores in historico_faltas.items():
        if not isinstance(lista_valores, list):
            continue
            
        valores_copia = list(lista_valores)
        
        time_pertence = "casa"
        if len(valores_copia) > quantidade_jogos:
            meio = len(valores_copia) // 2
            if sum(valores_copia[meio:]) > 0 and sum(valores_copia[:meio]) == 0:
                time_pertence = "fora"
            valores_analise = valores_copia[:quantidade_jogos] if time_pertence == "casa" else valores_copia[meio:meio+quantidade_jogos]
        else:
            if elenco_fora and jogador in elenco_fora:
                time_pertence = "fora"
            elif elenco_casa and jogador in elenco_casa:
                time_pertence = "casa"
            valores_analise = valores_copia

        while len(valores_analise) < quantidade_jogos:
            valores_analise.append(0)
            
        valores_analise = valores_analise[:quantidade_jogos]
        media = sum(valores_analise) / quantidade_jogos
        
        dados_faltas[jogador] = {
            "media": media,
            "time": time_pertence
        }

    if dados_faltas:
        jogadores_casa = [j for j in dados_faltas.keys() if dados_faltas[j]["time"] == "casa"]
        jogadores_fora = [j for j in dados_faltas.keys() if dados_faltas[j]["time"] == "fora"]
        
        # Força separação justa se o mapeamento de time falhar completamente
        if not jogadores_fora and len(jogadores_casa) > 1:
            geral_ordenado = sorted(dados_faltas.keys(), key=lambda k: dados_faltas[k]["media"], reverse=True)
            jogadores_casa = [geral_ordenado[0]]
            jogadores_fora = [geral_ordenado[1]]

        top_casa = sorted(jogadores_casa, key=lambda k: dados_faltas[k]["media"], reverse=True)
        top_fora = sorted(jogadores_fora, key=lambda k: dados_faltas[k]["media"], reverse=True)

        selecionados = []
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
        
