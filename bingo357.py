import re

def extrair_porcentagem(texto_mercado):
    try:
        match = re.search(r'\((\d+)%\)', texto_mercado)
        return int(match.group(1)) if match else 0
    except: return 0

def extrair_odd(odd_str):
    try:
        if not odd_str or odd_str == "N/A": return 1.0
        return float(odd_str.replace(',', '.'))
    except: return 1.0

def prioridade_mercado(mercado_texto):
    """
    Define o peso para ordenação: menor valor = maior prioridade.
    1. Gols, 2. 1X, 3. Ambas, 4. Vitória, 5. 2X
    """
    m = mercado_texto.lower()
    if "gols" in m: return 1
    if "1x" in m: return 2
    if "ambas" in m: return 3
    if "vitória" in m or "vitoria" in m: return 4
    if "2x" in m or "x2" in m: return 5
    return 6

def montar_bilhetes_estrategicos(lista_jogos):
    bilhetes = []
    if not lista_jogos: return bilhetes

    # Ordenação Geral por Prioridade de Mercado e depois por %
    jogos_ordenados = sorted(lista_jogos, key=lambda x: (prioridade_mercado(x['mercado']), -extrair_porcentagem(x['mercado'])))

    # --- BINGO 5: REGRAS DE SLOTS (VAGAS) ---
    if len(lista_jogos) >= 5:
        bingo5_selecao = []
        
        # Filtros de Odds
        vaga_gols = [j for j in jogos_ordenados if 1.20 <= extrair_odd(j['odd']) <= 1.39 and "gols" in j['mercado'].lower()]
        vaga_media = [j for j in jogos_ordenados if 1.40 <= extrair_odd(j['odd']) <= 1.50]
        vaga_alta = [j for j in jogos_ordenados if extrair_odd(j['odd']) >= 1.51]

        # 1. Preencher 3 vagas de Gols (1.20 a 1.39)
        bingo5_selecao.extend(vaga_gols[:3])

        # 2. Preencher 1 vaga de 1.40 a 1.50
        # Removemos os que já entraram (caso coincida)
        vaga_media = [j for j in vaga_media if j not in bingo5_selecao]
        if vaga_media: bingo5_selecao.append(vaga_media[0])

        # 3. Preencher 1 vaga de 1.51 para cima
        vaga_alta = [j for j in vaga_alta if j not in bingo5_selecao]
        if vaga_alta: bingo5_selecao.append(vaga_alta[0])

        # COMPLEMENTO: Se faltar jogo para fechar 5 (ex: não tem 3 de gols), preenche com o resto da lista
        if len(bingo5_selecao) < 5:
            resto = [j for j in jogos_ordenados if j not in bingo5_selecao]
            bingo5_selecao.extend(resto[:(5 - len(bingo5_selecao))])

        bilhetes.append({
            "id": "BINGO5", 
            "nome": "💰 BINGO 5: ESTRUTURADO (3 GOLS + 2 VALOR)", 
            "jogos": bingo5_selecao[:5]
        })

    # --- BINGO 3 e BINGO 7 (Mantendo lógicas anteriores ou simplificando) ---
    # (O Bingo 3 e 7 podem continuar com sua lógica original de melhores odds/porcentagens)
    
    # BINGO 3 (Top 3 Melhores Odds)
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: MÁXIMO VALOR", "jogos": lista_bingo3[:3]})

    # BINGO 7 (Top 7 Segurança: Maior % / Menor Odd)
    if len(lista_jogos) >= 7:
        lista_bingo7 = sorted(lista_jogos, key=lambda x: (extrair_porcentagem(x['mercado']) / extrair_odd(x['odd'])), reverse=True)
        bilhetes.append({"id": "BINGO7", "nome": "🍀 BINGO 7: SEGURANÇA MÁXIMA", "jogos": lista_bingo7[:7]})

    return bilhetes

# (Mantenha sua função formatar_para_telegram igual)
