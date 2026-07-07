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

def gerar_sigla_time(nome_time, padrao="TIM"):
    """Gera uma sigla de 3 letras em maiúsculo para o time (Ex: Jordânia -> JOR)"""
    if not nome_time or not isinstance(nome_time, str):
        return padrao
    # Limpa espaços e pega as 3 primeiras letras em maiúsculo
    nome_limpo = nome_time.strip().replace(" ", "").replace(".", "")
    if len(nome_limpo) >= 3:
        return nome_limpo[:3].upper()
    return nome_limpo.upper()

def limpar_nome_jogador(nome_completo):
    """Remove posições como 'Atacante', 'Ponta', 'Meio-campista' do final do nome."""
    posicoes = ["Atacante", "Ponta", "Meio-campista", "Meia-atacante", "Lateral", "Zagueiro", "Ala", "Goleiro"]
    nome_limpo = nome_completo
    for posicao in posicoes:
        if nome_limpo.endswith(posicao):
            nome_limpo = nome_limpo[:-len(posicao)].strip()
    return nome_limpo

def verificar_destaques_jogadores(historico_chutes, quantidade_jogos=3, nome_liga="", elenco_casa=None, elenco_fora=None, nome_casa="MANDANTE", nome_fora="VISITANTE"):
    """
    Analisa os destaques de chutes recebendo os nomes tratados dos times enviados pelo main.py.
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
        media_real = sum(valores_analise) / quantidade_jogos
        
        # 🟢 SUBTRAÇÃO NO FINAL DA MÉDIA: Remove 1.0 direto da média real calculada
        media_ajustada = media_real - 1.0
        
        jogos_com_sucesso = sum(1 for qtd in valores_analise if qtd >= 1)
        
        dados_chutes[jogador] = {
            "media": media_ajustada, 
            "jogos_com_sucesso": jogos_com_sucesso, 
            "time": time_pertence
        }

    if dados_chutes:
        jogadores_casa = [j for j in dados_chutes.keys() if dados_chutes[j]["time"] == "casa"]
        jogadores_fora = [j for j in dados_chutes.keys() if dados_chutes[j]["time"] == "fora"]
        
        if not jogadores_fora and len(jogadores_casa) > 1:
            geral_ordenado = sorted(dados_chutes.keys(), key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)
            jogadores_casa = [geral_ordenado[0]]
            jogadores_fora = [geral_ordenado[1]]

        top_casa = sorted(jogadores_casa, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)
        top_fora = sorted(jogadores_fora, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)

        selecionados = []
        if top_casa: selecionados.append((top_casa[0], "casa"))
        if top_fora: selecionados.append((top_fora[0], "fora"))
        
        for jogador, lado in selecionados:
            res_c = dados_chutes[jogador]
            
            # 🛑 TRAVA DE DESCARTE: De 0.0 a 0.9 (menor que 1.0) descarta o jogador do bilhete
            if res_c["media"] < 1.0:
                continue

            sigla = gerar_sigla_time(nome_fora, "VIS") if lado == "fora" else gerar_sigla_time(nome_casa, "CAS")
            nome_formatated = limpar_nome_jogador(jogador)

            mercados_aprovados.append({
                "texto": f"Chutes no gol: {sigla} {nome_formatated} | Méd: {res_c['media']:.1f}",
                "chave": "CHUTES_ALVO"
            })

    return mercados_aprovados

def verificar_destaques_faltas(historico_faltas, quantidade_jogos=3, nome_liga="", elenco_casa=None, elenco_fora=None, nome_casa="MANDANTE", nome_fora="VISITANTE"):
    """
    Analisa os destaques de faltas sofridas recebendo os nomes tratados dos times enviados pelo main.py.
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
            if elenco_fora and player in elenco_fora: # Mantendo consistência do seu mapeamento interno
                time_pertence = "fora"
            elif elenco_casa and jogador in elenco_casa:
                time_pertence = "casa"
            valores_analise = valores_copia

        while len(valores_analise) < quantidade_jogos:
            valores_analise.append(0)
            
        valores_analise = valores_analise[:quantidade_jogos]
        media_real = sum(valores_analise) / quantidade_jogos
        
        # 🟢 SUBTRAÇÃO NO FINAL DA MÉDIA: Remove 1.0 direto da média real calculada
        media_ajustada = media_real - 1.0
        
        dados_faltas[jogador] = {
            "media": media_ajustada,
            "time": time_pertence
        }

    if dados_faltas:
        jogadores_casa = [j for j in dados_faltas.keys() if dados_faltas[j]["time"] == "casa"]
        jogadores_fora = [j for j in dados_faltas.keys() if dados_faltas[j]["time"] == "fora"]
        
        if not jogadores_fora and len(jogadores_casa) > 1:
            geral_ordenado = sorted(dados_faltas.keys(), key=lambda k: dados_faltas[k]["media"], reverse=True)
            jogadores_casa = [geral_ordenado[0]]
            jogadores_fora = [geral_ordenado[1]]

        top_casa = sorted(jogadores_casa, key=lambda k: dados_faltas[k]["media"], reverse=True)
        top_fora = sorted(jogadores_fora, key=lambda k: dados_faltas[k]["media"], reverse=True)

        selecionados = []
        if top_casa: selecionados.append((top_casa[0], "casa"))
        if top_fora: selecionados.append((top_fora[0], "fora"))
        
        for jogador, lado in selecionados:
            res_f = dados_faltas[jogador]
            
            # 🛑 TRAVA DE DESCARTE: De 0.0 a 0.9 (menor que 1.0) descarta o jogador do bilhete
            if res_f["media"] < 1.0:
                continue

            sigla = gerar_sigla_time(nome_fora, "VIS") if lado == "fora" else gerar_sigla_time(nome_casa, "CAS")
            nome_formatated = limpar_nome_jogador(jogador)

            mercados_aprovados.append({
                "texto": f"Faltas Sofridas: {sigla} {nome_formatated} | Méd: {res_f['media']:.1f}",
                "chave": "FALTAS_SOFRIDAS"
            })

    return mercados_aprovados
            
