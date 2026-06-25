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
    # Prevenção contra dicionários acidentais na quantidade_jogos
    if isinstance(quantidade_jogos, dict):
        quantidade_jogos = 3

    nome_liga_limpo = nome_liga.strip() if nome_liga else ""
    
    if not nome_liga_limpo or nome_liga_limpo not in LIGAS_ELITE_JOGADORES:
        return []

    print(f"  ⚽ [MODULO JOGADORES] Iniciando análise para {nome_liga_limpo}.")

    mercados_aprovados = []
    dados_chutes = {}
    
    if not isinstance(historico_chutes, dict) or not historico_chutes:
        print("  ⚠️ [MODULO JOGADORES] Dicionário de chutes está VAZIO ou inválido.")
        return mercados_aprovados

    # 1. PROCESSAMENTO COMPLETO (Calcula todos os jogadores para garantir o melhor)
    for jogador, lista_valores in historico_chutes.items():
        if not isinstance(lista_valores, list):
            continue
            
        valores_copia = list(lista_valores)
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

    # 2. LOG OTIMIZADO (Exibe apenas os 3 primeiros no terminal)
    contagem_log = 0
    for jogador, dados in dados_chutes.items():
        if contagem_log < 3:
            print(f"    🏃‍♂️ Analisando {jogador}: {dados['valores']} | Média: {dados['media']:.2f} | Sucesso: {dados['jogos_com_sucesso']}/3")
            contagem_log += 1
    
    # 3. DEFINIÇÃO DOS MELHORES (Baseado no dicionário completo processado)
    if dados_chutes:
        # Ordenamos todos os jogadores pelo sucesso e depois pela média, pegando os 2 melhores
        jogadores_ordenados = sorted(
            dados_chutes.keys(), 
            key=lambda k: (dados_chutes[k]["jogos_com_sucesso"], dados_chutes[k]["media"]), 
            reverse=True
        )
        
        # Pega os 2 primeiros da lista (se existirem)
        top_2_jogadores = jogadores_ordenados[:2]
        
        for jogador in top_2_jogadores:
            res_c = dados_chutes[jogador]
            
            print(f"    ⭐ Destaque encontrado: {jogador} (Média: {res_c['media']:.2f}, Sucesso: {res_c['jogos_com_sucesso']})")
            
            # Regra de corte aplicada individualmente para cada um dos dois
            if res_c["jogos_com_sucesso"] >= 2 or res_c["media"] >= 1.0:
                print(f"    ✅ Jogador {jogador} APROVADO para o listão!")
                mercados_aprovados.append({
                    "texto": f"Chutes no Alvo: {jogador} (Frequência: {res_c['jogos_com_sucesso']}/{quantidade_jogos}j | Méd: {res_c['media']:.1f})",
                    "chave": "CHUTES_ALVO"
                })
            else:
                print(f"    ❌ Jogador {jogador} REPROVADO. Não atingiu a média de corte.")

    return mercados_aprovados
