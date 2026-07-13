#testes/teste_jogadores.py

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

def verificar_destaques_jogadores(historico_chutes, quantidade_jogos=5, nome_liga="", elenco_casa=None, elenco_fora=None, nome_casa="MANDANTE", nome_fora="VISITANTE"):
    """
    Analisa os destaques de chutes baseando-se nos elencos capturados.
    Filtra os últimos 5 jogos reais do jogador.
    """
    if isinstance(quantidade_jogos, dict) or quantidade_jogos == 3:
        quantidade_jogos = 5

    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_JOGADORES:
        return []

    mercados_aprovados = []
    dados_chutes = {}
    
    if not isinstance(historico_chutes, dict) or not historico_chutes:
        return mercados_aprovados

    elenco_casa_set = set(elenco_casa) if elenco_casa else set()
    elenco_fora_set = set(elenco_fora) if elenco_fora else set()

    for jogador, lista_valores in historico_chutes.items():
        if not isinstance(lista_valores, list) or not lista_valores:
            continue
            
        # Define a qual time o jogador pertence usando os elencos reais
        if jogador in elenco_fora_set:
            time_pertence = "fora"
        elif jogador in elenco_casa_set:
            time_pertence = "casa"
        else:
            # Fallback seguro caso não ache em nenhum elenco explicitamente
            continue

        # Como as listas estão alinhadas com o index global de 10 jogos,
        # pegamos os valores válidos (diferentes de zero se ele não jogou, ou simplesmente os últimos do histórico)
        valores_filtrados = [v for v in lista_valores if v is not None]
        
        # Pega os últimos N jogos que o robô processou para este jogador
        valores_analise = valores_filtrados[-quantidade_jogos:] if len(valores_filtrados) >= quantidade_jogos else valores_filtrados
        
        while len(valores_analise) < quantidade_jogos:
            valores_analise.append(0)
            
        media_real = sum(valores_analise) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in valores_analise if qtd >= 1)
        
        dados_chutes[jogador] = {
            "media": media_real,
            "jogos_com_sucesso": jogos_com_sucesso, 
            "time": time_pertence
        }

    if dados_chutes:
        jogadores_casa = [j for j in dados_chutes.keys() if dados_chutes[j]["time"] == "casa"]
        jogadores_fora = [j for j in dados_chutes.keys() if dados_chutes[j]["time"] == "fora"]
        
        top_casa = sorted(jogadores_casa, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)
        top_fora = sorted(jogadores_fora, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), reverse=True)

        selecionados = []
        if top_casa: selecionados.append((top_casa[0], "casa"))
        if top_fora: selecionados.append((top_fora[0], "fora"))
        
        for jogador, lado in selecionados:
            res_c = dados_chutes[jogador]
            
            # 🛑 TRAVA DE SEGURANÇA: Média real >= 1.0 E sucesso em pelo menos 3 dos 5 jogos
            if res_c["media"] < 1.0 or res_c["jogos_com_sucesso"] < 3:
                continue

            sigla = gerar_sigla_time(nome_fora, "VIS") if lado == "fora" else gerar_sigla_time(nome_casa, "CAS")
            nome_formatated = limpar_nome_jogador(jogador)

            mercados_aprovados.append({
                "texto": f"Chutes no gol: {sigla} {nome_formatated} | Méd: {res_c['media']:.1f}",
                "chave": "CHUTES_ALVO"
            })

    return mercados_aprovados

def verificar_destaques_faltas(historico_faltas, quantidade_jogos=5, nome_liga="", elenco_casa=None, elenco_fora=None, nome_casa="MANDANTE", nome_fora="VISITANTE"):
    """
    Analisa os destaques de faltas sofridas baseando-se nos elencos capturados.
    Ordenação e travas idênticas ao mercado de chutes.
    """
    if isinstance(quantidade_jogos, dict) or quantidade_jogos == 3:
        quantidade_jogos = 5

    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_JOGADORES:
        return []

    mercados_aprovados = []
    dados_faltas = {}
    
    if not isinstance(historico_faltas, dict) or not historico_faltas:
        return mercados_aprovados

    elenco_casa_set = set(elenco_casa) if elenco_casa else set()
    elenco_fora_set = set(elenco_fora) if elenco_fora else set()

    for jogador, lista_valores in historico_faltas.items():
        if not isinstance(lista_valores, list) or not lista_valores:
            continue
            
        if jogador in elenco_fora_set:
            time_pertence = "fora"
        elif jogador in elenco_casa_set:
            time_pertence = "casa"
        else:
            continue

        valores_filtrados = [v for v in lista_valores if v is not None]
        valores_analise = valores_filtrados[-quantidade_jogos:] if len(valores_filtrados) >= quantidade_jogos else valores_filtrados

        while len(valores_analise) < quantidade_jogos:
            valores_analise.append(0)
            
        media_real = sum(valores_analise) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in valores_analise if qtd >= 1)
        
        dados_faltas[jogador] = {
            "media": media_real,
            "jogos_com_sucesso": jogos_com_sucesso,
            "time": time_pertence
        }

    if dados_faltas:
        jogadores_casa = [j for j in dados_faltas.keys() if dados_faltas[j]["time"] == "casa"]
        jogadores_fora = [j for j in dados_faltas.keys() if dados_faltas[j]["time"] == "fora"]
        
        # 🟢 Ajustado para ordenar por sucesso e depois por média, igual aos chutes
        top_casa = sorted(jogadores_casa, key=lambda k: (dados_faltas[k]["jogos_com_sucesso"], dados_faltas[k]["media"]), reverse=True)
        top_fora = sorted(jogadores_fora, key=lambda k: (dados_faltas[k]["jogos_com_sucesso"], dados_faltas[k]["media"]), reverse=True)

        selecionados = []
        if top_casa: selecionados.append((top_casa[0], "casa"))
        if top_fora: selecionados.append((top_fora[0], "fora"))
        
        for jogador, lado in selecionados:
            res_f = dados_faltas[jogador]
            
            # 🛑 TRAVA DE SEGURANÇA: Média real >= 1.0 E sucesso em pelo menos 3 dos 5 jogos
            if res_f["media"] < 1.0 or res_f["jogos_com_sucesso"] < 3:
                continue

            sigla = gerar_sigla_time(nome_fora, "VIS") if lado == "fora" else gerar_sigla_time(nome_casa, "CAS")
            nome_formatated = limpar_nome_jogador(jogador)

            mercados_aprovados.append({
                "texto": f"Faltas Sofridas: {sigla} {nome_formatated} | Méd: {res_f['media']:.1f}",
                "chave": "FALTAS_SOFRIDAS"
            })

    return mercados_aprovados
        
