# mercados/jogadores.py

def verificar_destaques_jogadores(historico_chutes, historico_faltas, quantidade_jogos=3):
    """
    Processa os históricos brutos extraídos pelo Selenium.
    Aprova o jogador se ele tiver pelo menos 1 ação em pelo menos 2 dos 3 jogos,
    OU se a média dele for maior ou igual a 1.0.
    """
    mercados_aprovados = []
    
    # 📈 REGRA: CHUTES NO ALVO
    dados_chutes = {}
    for jogador, lista_valores in historico_chutes.items():
        while len(lista_valores) < quantidade_jogos:
            lista_valores.append(0)
            
        # Calcula a média e conta em quantos jogos ele fez pelo menos 1 chute
        media = sum(lista_valores) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in lista_valores if qtd >= 1)
        
        # Guarda o maior peso para o critério de desempate no max()
        dados_chutes[jogador] = {"media": media, "jogos_com_sucesso": jogos_com_sucesso}

    if dados_chutes:
        # Define o melhor com base na consistência de jogos e depois na média
        melhor_chutador = max(dados_chutes, key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]))
        res_c = dados_chutes[melhor_chutador]
        
        # VALIDAÇÃO: Passa se teve sucesso em 2 de 3 jogos OU se a média geral for >= 1.0
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
        
        # VALIDAÇÃO: Passa se teve sucesso em 2 de 3 jogos OU se a média geral for >= 1.0
        if res_f["jogos_com_sucesso"] >= 2 or res_f["media"] >= 1.0:
            mercados_aprovados.append({
                "texto": f"Faltas Sofridas: {mais_cacado} (Frequência: {res_f['jogos_com_sucesso']}/{quantidade_jogos}j | Méd: {res_f['media']:.1f})",
                "chave": "FALTAS_SOFRIDAS"
            })

    return mercados_aprovados
