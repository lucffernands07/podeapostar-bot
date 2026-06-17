# mercados/jogadores.py

def verificar_destaques_jogadores(historico_chutes, historico_faltas, quantidade_jogos=3):
    """
    Processa os históricos brutos extraídos pelo Selenium, calcula as médias
    e retorna os mercados aprovados com base nos critérios de corte.
    """
    mercados_aprovados = []
    
    # 📈 REGRA: CHUTES NO ALVO (Exige Média >= 1.0)
    medias_chutes = {}
    for jogador, lista_valores in historico_chutes.items():
        # Preenche com zero caso o jogador não tenha entrado em alguma das partidas
        while len(lista_valores) < quantidade_jogos:
            lista_valores.append(0)
        medias_chutes[jogador] = sum(lista_valores) / quantidade_jogos

    if medias_chutes:
        melhor_chutador = max(medias_chutes, key=medias_chutes.get)
        media_c = medias_chutes[melhor_chutador]
        if media_c >= 1.0:
            mercados_aprovados.append({
                "texto": f"Chutes no Alvo: {melhor_chutador} (Média {media_c:.1f})",
                "chave": "CHUTES_ALVO"
            })

    # 📉 REGRA: FALTAS SOFRIDAS (Exige Média >= 1.5)
    medias_faltas = {}
    for jogador, lista_valores in historico_faltas.items():
        while len(lista_valores) < quantidade_jogos:
            lista_valores.append(0)
        medias_faltas[jogador] = sum(lista_valores) / quantidade_jogos

    if medias_faltas:
        mais_cacado = max(medias_faltas, key=medias_faltas.get)
        media_f = medias_faltas[mais_cacado]
        if media_f >= 1.5:
            mercados_aprovados.append({
                "texto": f"Faltas Sofridas: {mais_cacado} (Média {media_f:.1f})",
                "chave": "FALTAS_SOFRIDAS"
            })

    return mercados_aprovados
