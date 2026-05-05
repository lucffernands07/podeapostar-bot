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

    # --- BINGO 3: VALOR (Mantido) ---
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)[:3]
        lista_bingo3.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: VALOR", "jogos": lista_bingo3})

    # --- BINGO 5: NOVO CRITÉRIO (3 ODDS + 2 PORCENTAGENS) ---
    if len(lista_jogos) >= 5:
        bingo5_selecao = []
        
        # 1. Seleciona os 3 jogos com as MAIORES ODDS
        maiores_odds = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)[:3]
        bingo5_selecao.extend(maiores_odds)

        # 2. Filtra o que sobrou para pegar as melhores porcentagens
        restantes = [j for j in lista_jogos if j not in bingo5_selecao]
        maiores_porcentagens = sorted(restantes, key=lambda x: extrair_porcentagem(x['mercado']), reverse=True)[:2]
        bingo5_selecao.extend(maiores_porcentagens)

        # Caso ainda falte jogo (segurança), pega o que vier pela frente
        if len(bingo5_selecao) < 5:
            sobra = [j for j in lista_jogos if j not in bingo5_selecao]
            bingo5_selecao.extend(sobra[:(5 - len(bingo5_selecao))])

        # Organiza por horário para o bilhete ficar em ordem cronológica
        bingo5_selecao.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: ESTRUTURADO", "jogos": bingo5_selecao[:5]})

    # --- BINGO 7: SEGURANÇA (Mantido) ---
    if len(lista_jogos) >= 7:
        lista_bingo7 = sorted(lista_jogos, key=lambda x: (extrair_porcentagem(x['mercado']) / extrair_odd(x['odd'])), reverse=True)[:7]
        lista_bingo7.sort(key=lambda x: x['horario'])
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
    
