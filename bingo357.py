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
    """ Prioridade: 1. Gols, 2. 1X, 3. Ambas, 4. Vitória, 5. 2X """
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

    # Ordenação base por Prioridade de Mercado e Porcentagem
    jogos_ordenados = sorted(lista_jogos, key=lambda x: (prioridade_mercado(x['mercado']), -extrair_porcentagem(x['mercado'])))

    # --- BINGO 3: VALOR (ODDS MAIS ALTAS) ---
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)[:3]
        lista_bingo3.sort(key=lambda x: x['horario']) # Ordena por hora
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: VALOR", "jogos": lista_bingo3})

    # --- BINGO 5: ESTRUTURADO (3 GOLS + 2 VALOR) ---
    if len(lista_jogos) >= 5:
        bingo5_selecao = []
        # Slots conforme sua regra original
        vaga_gols = [j for j in jogos_ordenados if 1.20 <= extrair_odd(j['odd']) <= 1.39 and "gols" in j['mercado'].lower()]
        vaga_media = [j for j in jogos_ordenados if 1.40 <= extrair_odd(j['odd']) <= 1.50]
        vaga_alta = [j for j in jogos_ordenados if extrair_odd(j['odd']) >= 1.51]

        # Preenche os slots
        bingo5_selecao.extend(vaga_gols[:3])
        
        vaga_media = [j for j in vaga_media if j not in bingo5_selecao]
        if vaga_media: bingo5_selecao.append(vaga_media[0])
        
        vaga_alta = [j for j in vaga_alta if j not in bingo5_selecao]
        if vaga_alta: bingo5_selecao.append(vaga_alta[0])

        # Preenchimento de segurança se faltar jogo nos critérios acima
        if len(bingo5_selecao) < 5:
            resto = [j for j in jogos_ordenados if j not in bingo5_selecao]
            bingo5_selecao.extend(resto[:(5 - len(bingo5_selecao))])

        # ORDENAÇÃO POR HORA (Essencial para o log e visualização)
        bingo5_selecao.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: ESTRUTURADO", "jogos": bingo5_selecao[:5]})

    # --- BINGO 7: SEGURANÇA ---
    if len(lista_jogos) >= 7:
        lista_bingo7 = sorted(lista_jogos, key=lambda x: (extrair_porcentagem(x['mercado']) / extrair_odd(x['odd'])), reverse=True)[:7]
        lista_bingo7.sort(key=lambda x: x['horario']) # Ordena por hora
        bilhetes.append({"id": "BINGO7", "nome": "🍀 BINGO 7: SEGURANÇA", "jogos": lista_bingo7})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    if not bilhetes: return ""
    blocos = []
    for b in bilhetes:
        corpo = f"*{b['nome']}*\n"
        jogos_texto = []
        odd_total = 1.0
        for j in b['jogos']:
            # Mantendo suas chaves e lógica de link idênticas
            chave = f"{j['time_casa']}x{j['time_fora']}"
            link_cru = cache_links.get(chave, f"https://www.betano.bet.br/sport/futebol/")
            link_limpo = link_cru.replace(" ", "%20").replace("(", "%28").replace(")", "%29").strip()
            
            item = f"⏱️ {j['horario']} | {j['liga']}\n🏟️ {j['time_casa']} x {j['time_fora']}\n🔶 {j['mercado']} | Odd: {j['odd']}\n🌐 [Abrir na Betano]({link_limpo})"
            jogos_texto.append(item)
            odd_total *= extrair_odd(j['odd'])
            
        corpo += "\n" + "\n\n".join(jogos_texto) + f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)
    
    return "\n\n".join(blocos)
    
