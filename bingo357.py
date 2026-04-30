import re

def extrair_porcentagem(texto_mercado):
    try:
        match = re.search(r'\((\d+)%\)', texto_mercado)
        return int(match.group(1)) if match else 0
    except:
        return 0

def extrair_odd(odd_str):
    try:
        if not odd_str or odd_str == "N/A":
            return 1.0
        return float(odd_str.replace(',', '.'))
    except:
        return 1.0

def montar_bilhetes_estrategicos(lista_jogos):
    bilhetes = []
    if not lista_jogos:
        return bilhetes

    # --- BINGO 3 ---
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: MAIORES ODDS (VALOR)", "jogos": lista_bingo3[:3]})

    # --- BINGO 5 ---
    if len(lista_jogos) >= 5:
        def score_equilibrio(j):
            pct = extrair_porcentagem(j['mercado'])
            odd = extrair_odd(j['odd'])
            return (pct * 0.7) + (odd * 15) 
        lista_bingo5 = sorted(lista_jogos, key=score_equilibrio, reverse=True)
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: MELHORES ODDS & % (EQUILÍBRIO)", "jogos": lista_bingo5[:5]})

    # --- BINGO 7 ---
    if len(lista_jogos) >= 7:
        lista_bingo7 = sorted(lista_jogos, key=lambda x: extrair_porcentagem(x['mercado']), reverse=True)
        bilhetes.append({"id": "BINGO7", "nome": "🍀 BINGO 7: MAIORES % (SEGURANÇA)", "jogos": lista_bingo7[:7]})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    if not bilhetes:
        return ""

    blocos = []
    for b in bilhetes:
        corpo = f"*{b['nome']}*\n"
        jogos_texto = []
        odd_acumulada = 1.0

        for j in b['jogos']:
            chave = f"{j['time_casa']}x{j['time_fora']}"
            link_cru = cache_links.get(chave, f"https://br.betano.com/search?q={j['time_casa']}")
            
            # LIMPEZA CRÍTICA: O Telegram quebra o link se houver ) ou espaços dentro do ( ) do Markdown
            # Vamos encodar os parênteses e espaços para o link não "vazar"
            link_limpo = link_cru.replace(" ", "%20").replace("(", "%28").replace(")", "%29").strip()
            
            # Formato Markdown: [Texto](Link) - Sem espaços entre eles!
            item = (
                f"⏱️ {j['horario']} | {j['liga']}\n"
                f"🏟️ {j['time_casa']} x {j['time_fora']}\n"
                f"🔶 {j['mercado']} | Odd: {j['odd']}\n"
                f"🌐 [Abrir na Betano]({link_limpo})"
            )
            jogos_texto.append(item)
            
            try:
                odd_acumulada *= extrair_odd(j['odd'])
            except: pass

        corpo += "\n" + "\n\n".join(jogos_texto)
        corpo += f"\n\n📈 *Odd Total: {odd_acumulada:.2f}*\n"
        corpo += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)

    return "\n\n".join(blocos)
    
