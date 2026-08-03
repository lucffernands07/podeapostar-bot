# mercados/jogadores.py

# 🟢 LISTA BRANCA: Nomes-chave para busca flexível nas ligas de elite
LIGAS_ELITE_JOGADORES = [
    "brasileirão série a", "copa do brasil", "libertadores", "sul-americana",
    "brasileirão série b", "liga profesional", "argentina", "copa do mundo",
    "champions league", "premier league", "laliga", "bundesliga", "serie a", 
    "ligue 1", "europa league", "fa cup", "copa del rey", "dfb pokal", 
    "primeira liga", "eredivisie", "amistoso internacional"
]

def validar_liga_para_jogadores(nome_liga):
    """
    Verifica se a liga do confronto pertence às ligas permitidas (comparação flexível).
    """
    if not nome_liga:
        return False
        
    liga_limpa = nome_liga.strip().lower()
    
    for liga_permitida in LIGAS_ELITE_JOGADORES:
        if liga_permitida in liga_limpa:
            return True
            
    return False


def analisar_dados_jogadores(acumulador_scouts, t1, t2):
    """
    Processa as estatísticas individuais de chutes no gol e faltas sofridas.
    - Mandante (t1): Retorna até 2 MELHORES jogadores de cada mercado.
    - Visitante (t2): Retorna até 1 MELHOR jogador de cada mercado.
    - Trava de Mínimo de Jogos REMOVIDA: Exige apenas c_jogos > 0 para o cálculo.
    """
    if not acumulador_scouts:
        print("⏩ [HISTÓRICO INCOMPLETO] Sem dados de scouts de jogadores para calcular.")
        return {"aprovado": False, "scouts_formatados": ""}

    linhas_scouts_geral = []
    lista_jogadores_qualificados = []

    # --- CÁLCULO E SELEÇÃO DOS MELHORES ---
    for time_alvo in [t1, t2]:
        limite_jogadores = 2 if time_alvo == t1 else 1

        # Comparação flexível para nomes de times
        time_alvo_limpo = str(time_alvo).strip().lower()
        jogadores_do_time = {
            k: v for k, v in acumulador_scouts.items() 
            if str(v.get('time', '')).strip().lower() == time_alvo_limpo or time_alvo_limpo in str(v.get('time', '')).strip().lower()
        }
        
        candidatos_chutes = []
        candidatos_faltas = []
        
        for nome_jogador, d in jogadores_do_time.items():
            c_jogos = d.get('c_jogos', 0)
            f_jogos = d.get('f_jogos', 0)

            # Cálculo de médias (protegido contra divisão por zero)
            media_chutes = d.get('chutes', 0) / c_jogos if c_jogos > 0 else 0
            media_faltas = d.get('faltas', 0) / f_jogos if f_jogos > 0 else 0
            
            # 🟢 Filtro: Apenas média >= 0.5 (SEM trava de mínimo de 3 jogos)
            if media_chutes >= 0.5 and c_jogos > 0:
                candidatos_chutes.append({
                    "jogador": nome_jogador,
                    "time": time_alvo,
                    "mercado": "Chutes no gol",
                    "media": round(media_chutes, 2)
                })
                
            if media_faltas >= 0.5 and f_jogos > 0:
                candidatos_faltas.append({
                    "jogador": nome_jogador,
                    "time": time_alvo,
                    "mercado": "Faltas sofridas",
                    "media": round(media_faltas, 2)
                })

        # --- FILTRO: Seleciona top 2 para Mandante e top 1 para Visitante ---
        linhas_chutes = []
        linhas_faltas = []

        if candidatos_chutes:
            candidatos_chutes_ordenados = sorted(candidatos_chutes, key=lambda x: x['media'], reverse=True)
            top_chutes = candidatos_chutes_ordenados[:limite_jogadores]
            
            for j_chute in top_chutes:
                lista_jogadores_qualificados.append(j_chute)
                linhas_chutes.append(f"Chutes no gol: {j_chute['jogador']} média {j_chute['media']:.1f}")

        if candidatos_faltas:
            candidatos_faltas_ordenados = sorted(candidatos_faltas, key=lambda x: x['media'], reverse=True)
            top_faltas = candidatos_faltas_ordenados[:limite_jogadores]
            
            for j_falta in top_faltas:
                lista_jogadores_qualificados.append(j_falta)
                linhas_faltas.append(f"Faltas sofridas: {j_falta['jogador']} média {j_falta['media']:.1f}")

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
    
