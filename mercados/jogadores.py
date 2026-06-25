# 🟢 LISTA BRANCA: Apenas ligas de elite que comprovadamente abrem mercados de jogadores na Betano
LIGAS_ELITE_JOGADORES = [
    "Brasileirão Série A", "Copa do Brasil", "Libertadores", "Sul-Americana",
    "Brasileirão Série B", "Argentina - Liga Profesional", "Mundo - Copa do Mundo",
    "Champions League", "Inglaterra - Premier League", "Espanha - LaLiga",
    "Alemanha - Bundesliga", "Italia - Serie A", "França - Ligue 1",
    "Europa - League", "Inglaterra - FA Cup", "Espanha - Copa del Rey",
    "Alemanha - DFB Pokal", "Portugal - Primeira Liga", "Países Baixos - Eredivisie",
    "Mundo - Amistoso Internacional"
]

def verificar_destaques_jogadores(historico_chutes, quantidade_jogos=3, nome_liga=""):
    """
    Analisa os destaques de chutes, tratando falhas de forma resiliente
    para não travar a execução principal.
    """
    # Prevenção contra tipos incorretos
    if isinstance(quantidade_jogos, dict):
        quantidade_jogos = 3

    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    
    # Validação de liga
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_JOGADORES:
        return []

    mercados_aprovados = []
    dados_chutes = {}
    
    # Validação de dados de entrada
    if not isinstance(historico_chutes, dict) or not historico_chutes:
        return mercados_aprovados

    # 1. PROCESSAMENTO COMPLETO
    # Limitamos a 30 jogadores para garantir performance no Actions
    itens_processar = list(historico_chutes.items())[:30]
    
    for jogador, lista_valores in itens_processar:
        if not isinstance(lista_valores, list):
            continue
            
        valores_copia = list(lista_valores)
        # Normalização de dados (preenche com 0 se faltar jogo)
        while len(valores_copia) < quantidade_jogos:
            valores_copia.append(0)
            
        valores_analise = valores_copia[:quantidade_jogos]
            
        media = sum(valores_analise) / quantidade_jogos
        jogos_com_sucesso = sum(1 for qtd in valores_analise if qtd >= 1)
        
        dados_chutes[jogador] = {
            "media": media, 
            "jogos_com_sucesso": jogos_com_sucesso, 
            "valores": valores_analise
        }

    # 2. DEFINIÇÃO DOS MELHORES (Baseado no dicionário completo processado)
    if dados_chutes:
        # Ordenamos todos os jogadores pelo sucesso e depois pela média
        jogadores_ordenados = sorted(
            dados_chutes.keys(), 
            key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), 
            reverse=True
        )
        
        # Pega até 2 primeiros (se só existir 1, pegará 1, sem erros)
        top_jogadores = jogadores_ordenados[:2]
        
        for jogador in top_jogadores:
            # Segurança extra: garante que o jogador ainda existe no dicionário processado
            if jogador not in dados_chutes:
                continue
                
            res_c = dados_chutes[jogador]
            
            # Regra de corte aplicada individualmente para cada um dos dois
            if res_c["jogos_com_sucesso"] >= 2 or res_c["media"] >= 1.0:
                mercados_aprovados.append({
                    "texto": f"Chutes no Alvo: {jogador} (Frequência: {res_c['jogos_com_sucesso']}/{quantidade_jogos}j | Méd: {res_c['media']:.1f})",
                    "chave": "CHUTES_ALVO"
                })

    return mercados_aprovados
    
