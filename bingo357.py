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

    # Ordenação por Prioridade e depois por %
    jogos_ordenados = sorted(lista_jogos, key=lambda x: (prioridade_mercado(x['mercado']), -extrair_porcentagem(x['mercado'])))

    # --- BINGO 5: ESTRUTURADO (3 GOLS + 2 VALOR) ---
    if len(lista_jogos) >= 5:
        bingo5_selecao = []
        # Slots conforme sua regra
        vaga_gols = [j for j in jogos_ordenados if 1.20 <= extrair_odd(j['odd']) <= 1.39 and "gols" in j['mercado'].lower()]
        vaga_media = [j for j in jogos_ordenados if 1.40 <= extrair_odd(j['odd']) <= 1.50]
        vaga_alta = [j for j in jogos_ordenados if extrair_odd(j['odd']) >= 1.51]

        bingo5_selecao.extend(vaga_gols[:3])
        
        vaga_media = [j for j in vaga_media if j not in bingo5_selecao]
        if vaga_media: bingo5_selecao.append(vaga_media[0])
        
        vaga_alta = [j for j in vaga_alta if j not in bingo5_selecao]
        if vaga_alta: bingo5_selecao.append(vaga_alta[0])

        # Preenchimento se faltar jogo específico
        if len(bingo5_selecao) < 5:
            resto = [j for j in jogos_ordenados if j not in bingo5_selecao]
            bingo5_selecao.extend(resto[:(5 - len(bingo5_selecao))])

        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: ESTRUTURADO", "jogos": bingo5_selecao[:5]})

    # BINGO 3 e BINGO 7 (Lógicas de apoio)
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: VALOR", "jogos": lista_bingo3[:3]})

    if len(lista_jogos) >= 7:
        lista_bingo7 = sorted(lista_jogos, key=lambda x: (extrair_porcentagem(x['mercado']) / extrair_odd(x['odd'])), reverse=True)
        bilhetes.append({"id": "BINGO7", "nome": "🍀 BINGO 7: SEGURANÇA", "jogos": lista_bingo7[:7]})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    """ Função que estava faltando no seu arquivo e causava o erro crítico """
    if not bilhetes: return ""
    blocos = []
    for b in bilhetes:
        corpo = f"*{b['nome']}*\n"
        jogos_texto = []
        odd_total = 1.0
        for j in b['jogos']:
            chave = f"{j['time_casa']}x{j['time_fora']}"
            link_cru = cache_links.get(chave, f"https://br.betano.com/search?q={j['time_casa']}")
            link_limpo = link_cru.replace(" ", "%20").replace("(", "%28").replace(")", "%29").strip()
            item = f"⏱️ {j['horario']} | {j['liga']}\n🏟️ {j['time_casa']} x {j['time_fora']}\n🔶 {j['mercado']} | Odd: {j['odd']}\n🌐 [Abrir na Betano]({link_limpo})"
            jogos_texto.append(item)
            odd_total *= extrair_odd(j['odd'])
        corpo += "\n" + "\n\n".join(jogos_texto) + f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)
    return "\n\n".join(blocos)
