# mercados/jogadores.py

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

def validar_liga_para_jogadores(nome_liga):
    """
    Verifica se a liga do confronto pertence à lista de ligas elite permitidas.
    Retorna True se for permitido raspar estatísticas de jogadores, caso contrário False.
    """
    if not nome_liga:
        return False
        
    liga_limpa = nome_liga.strip()
    
    # Validação direta ou busca parcial (caso o nome da liga venha com acréscimos)
    for liga_permitida in LIGAS_ELITE_JOGADORES:
        if liga_permitida.lower() in liga_limpa.lower() or liga_limpa.lower() in liga_permitida.lower():
            return True
            
    return False


def analisar_dados_jogadores(acumulador_scouts, t1, t2):
    """
    Processa as estatísticas individuais de chutes no gol e faltas sofridas.
    - Mandante (t1): Retorna os até 2 MELHORES jogadores de cada mercado.
    - Visitante (t2): Retorna apenas o 1 MELHOR jogador de cada mercado.
    - Trava de Amostra: Exige que o jogador tenha atuado em pelo menos 3 jogos.
    """
    if not acumulador_scouts:
        print("⏩ [HISTÓRICO INCOMPLETO] Sem dados de scouts de jogadores para calcular.")
        return {"aprovado": False, "scouts_formatados": ""}

    linhas_scouts_geral = []
    lista_jogadores_qualificados = []

    # --- CÁLCULO E SELEÇÃO DOS MELHORES ---
    # Processa o mandante (T1) e depois o visitante (T2)
    for time_alvo in [t1, t2]:
        # Define o limite baseado na condição: Mandante (T1) = 2, Visitante (T2) = 1
        limite_jogadores = 2 if time_alvo == t1 else 1

        jogadores_do_time = {k: v for k, v in acumulador_scouts.items() if v['time'] == time_alvo.upper()}
        
        candidatos_chutes = []
        candidatos_faltas = []
        
        for nome_jogador, d in jogadores_do_time.items():
            # 🟢 TRAVA DE SEGURANÇA: Mínimo de 3 jogos disputados para considerar a média válida
            MIN_JOGOS = 3

            media_chutes = d['chutes'] / d['c_jogos'] if d['c_jogos'] > 0 else 0
            media_faltas = d['faltas'] / d['f_jogos'] if d['f_jogos'] > 0 else 0
            
            # Adiciona aos candidatos se a média for >= 0.5 E tiver atuado em pelo menos 3 jogos
            if media_chutes >= 0.5 and d['c_jogos'] >= MIN_JOGOS:
                candidatos_chutes.append({
                    "jogador": nome_jogador,
                    "time": time_alvo,
                    "mercado": "Chutes no gol",
                    "media": round(media_chutes, 2)
                })
                
            # Adiciona aos candidatos se a média for >= 0.5 E tiver atuado em pelo menos 3 jogos
            if media_faltas >= 0.5 and d['f_jogos'] >= MIN_JOGOS:
                candidatos_faltas.append({
                    "jogador": nome_jogador,
                    "time": time_alvo,
                    "mercado": "Faltas sofridas",
                    "media": round(media_faltas, 2)
                })

        # --- FILTRO: Seleciona top 2 para Mandante (T1) e top 1 para Visitante (T2) ---
        linhas_chutes = []
        linhas_faltas = []

        if candidatos_chutes:
            # Ordena decrescente pela média e aplica o corte dinâmico
            candidatos_chutes_ordenados = sorted(candidatos_chutes, key=lambda x: x['media'], reverse=True)
            top_chutes = candidatos_chutes_ordenados[:limite_jogadores]
            
            for j_chute in top_chutes:
                lista_jogadores_qualificados.append(j_chute)
                linhas_chutes.append(f"Chutes no gol: {j_chute['jogador']} média {j_chute['media']:.1f}")

        if candidatos_faltas:
            # Ordena decrescente pela média e aplica o corte dinâmico
            candidatos_faltas_ordenados = sorted(candidatos_faltas, key=lambda x: x['media'], reverse=True)
            top_faltas = candidatos_faltas_ordenados[:limite_jogadores]
            
            for j_falta in top_faltas:
                lista_jogadores_qualificados.append(j_falta)
                linhas_faltas.append(f"Faltas sofridas: {j_falta['jogador']} média {j_falta['media']:.1f}")

        # Se houver dados qualificados para o time, adiciona nas linhas de log/bloco
        if linhas_chutes or linhas_faltas:
            linhas_scouts_geral.append(f"{time_alvo.capitalize()}:")
            for l in linhas_chutes:
                linhas_scouts_geral.append(l)
            for l in linhas_faltas:
                linhas_scouts_geral.append(l)

    # Montagem do bloco de texto final
    separador = "="*50
    texto_scouts_bloco = ""
    if linhas_scouts_geral:
        texto_scouts_bloco = f"\n{separador}\n" + "\n".join(linhas_scouts_geral) + f"\n{separador}"
    
    return {
        "aprovado": len(lista_jogadores_qualificados) > 0,
        "jogadores_qualificados": lista_jogadores_qualificados,
        "scouts_formatados": texto_scouts_bloco
                                                 }
    
