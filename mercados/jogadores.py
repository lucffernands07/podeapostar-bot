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
    Filtra jogadores com médias estritamente maiores que 1.0.
    Retorna dados estruturados e a string formatada para logs e envios.
    """
    if not acumulador_scouts:
        print("⏩ [HISTÓRICO INCOMPLETO] Sem dados de scouts de jogadores para calcular.")
        return {"aprovado": False, "scouts_formatados": ""}

    linhas_scouts_geral = []
    lista_jogadores_qualificados = []

    # --- CÁLCULO E FORMATAÇÃO DE MÉDIAS ---
    # Processa o mandante (T1) e depois o visitante (T2)
    for time_alvo in [t1, t2]:
        jogadores_do_time = {k: v for k, v in acumulador_scouts.items() if v['time'] == time_alvo.upper()}
        
        linhas_chutes = []
        linhas_faltas = []
        
        for nome_jogador, d in jogadores_do_time.items():
            media_chutes = d['chutes'] / d['c_jogos'] if d['c_jogos'] > 0 else 0
            media_faltas = d['faltas'] / d['f_jogos'] if d['f_jogos'] > 0 else 0
            
            # Condição estrita: média obrigatoriamente > 1.0
            if media_chutes > 1.0:
                linhas_chutes.append(f"Chutes no gol: {nome_jogador} média {media_chutes:.1f}")
                lista_jogadores_qualificados.append({
                    "jogador": nome_jogador,
                    "time": time_alvo,
                    "mercado": "Chutes no gol",
                    "media": round(media_chutes, 2)
                })
                
            if media_faltas > 1.0:
                linhas_faltas.append(f"Faltas sofridas: {nome_jogador} média {media_faltas:.1f}")
                lista_jogadores_qualificados.append({
                    "jogador": nome_jogador,
                    "time": time_alvo,
                    "mercado": "Faltas sofridas",
                    "media": round(media_faltas, 2)
                })

        # Se houver dados do time, agrupa no formato exato solicitado
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
            
