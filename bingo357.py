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

    # Ordenação base para os filtros
    jogos_ordenados = sorted(lista_jogos, key=lambda x: (prioridade_mercado(x['mercado']), -extrair_porcentagem(x['mercado'])))

        # --- BINGO 3: VALOR ---
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)[:3]
        # ADICIONA ESTA LINHA: Ordena os 3 escolhidos por hora
        lista_bingo3.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: ODDS ARRISCADAS", "jogos": lista_bingo3})

    # --- BINGO 5: ESTRUTURADO ---
    if len(lista_jogos) >= 5:
        # ... (sua lógica de seleção das vagas gols/media/alta continua igual) ...
        # Antes do append, ordene a seleção final:
        bingo5_selecao.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: EQUILIBRADO", "jogos": bingo5_selecao[:5]})

    # --- BINGO 7: SEGURANÇA ---
    if len(lista_jogos) >= 7:
        lista_bingo7 = sorted(lista_jogos, key=lambda x: (extrair_porcentagem(x['mercado']) / extrair_odd(x['odd'])), reverse=True)[:7]
        # ADICIONA ESTA LINHA: Ordena os 7 escolhidos por hora
        lista_bingo7.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO7", "nome": "🍀 BINGO 7: ODDS SEGURAS", "jogos": lista_bingo7})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    if not bilhetes: return ""
    blocos = []
    for b in bilhetes:
        corpo = f"{b['nome']}\n" # Nome do Bingo
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
