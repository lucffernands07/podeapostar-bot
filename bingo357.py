import re

def extrair_porcentagem(texto_mercado):
    """
    Extrai o número de dentro dos parênteses (ex: 85) do texto do mercado.
    Se não encontrar, retorna 0.
    """
    try:
        match = re.search(r'\((\d+)%\)', texto_mercado)
        return int(match.group(1)) if match else 0
    except:
        return 0

def extrair_odd(odd_str):
    """Converte a string da odd (ex: '1,44') para float."""
    try:
        return float(odd_str.replace(',', '.'))
    except:
        return 1.0

def montar_bilhetes_estrategicos(lista_jogos):
    """
    Organiza os jogos da lista geral em 3 categorias inteligentes:
    Bingo 3: Maiores Odds (Valor)
    Bingo 5: Equilíbrio entre Odd e %
    Bingo 7: Maiores % (Segurança)
    """
    bilhetes = []
    if not lista_jogos:
        return bilhetes

    # --- ESTRATÉGIA 1: BINGO 3 (MELHORES ODDS) ---
    # Foco em buscar o maior retorno financeiro dentro da lista aprovada.
    if len(lista_jogos) >= 3:
        # Ordena da maior Odd para a menor
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)
        bilhetes.append({
            "id": "BINGO3", 
            "nome": "🔥 BINGO 3: MAIORES ODDS (VALOR)", 
            "jogos": lista_bingo3[:3]
        })

    # --- ESTRATÉGIA 2: BINGO 5 (EQUILÍBRIO ODD + %) ---
    # Busca jogos que tenham boa probabilidade mas com odds que valham a pena.
    if len(lista_jogos) >= 5:
        def score_equilibrio(j):
            pct = extrair_porcentagem(j['mercado'])
            odd = extrair_odd(j['odd'])
            # Score: Dá peso 70% para a estatística e 30% para o valor da odd
            return (pct * 0.7) + (odd * 15) 

        lista_bingo5 = sorted(lista_jogos, key=score_equilibrio, reverse=True)
        bilhetes.append({
            "id": "BINGO5", 
            "nome": "💰 BINGO 5: MELHORES ODDS & % (EQUILÍBRIO)", 
            "jogos": lista_bingo5[:5]
        })

    # --- ESTRATÉGIA 3: BINGO 7 (MAIORES %) ---
    # Foco total em probabilidade de acerto. Pega os 'tanques' da lista (85%, 100%).
    if len(lista_jogos) >= 7:
        # Ordena da maior Porcentagem para a menor
        lista_bingo7 = sorted(lista_jogos, key=lambda x: extrair_porcentagem(x['mercado']), reverse=True)
        bilhetes.append({
            "id": "BINGO7", 
            "nome": "🍀 BINGO 7: MAIORES % (SEGURANÇA)", 
            "jogos": lista_bingo7[:7]
        })

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    """
    Formata os bilhetes para o Telegram com o layout profissional.
    """
    if not bilhetes:
        return ""

    blocos = []
    for b in bilhetes:
        corpo = f"*{b['nome']}*\n"
        jogos_texto = []
        odd_acumulada = 1.0

        for j in b['jogos']:
            chave = f"{j['time_casa']}x{j['time_fora']}"
            # Tenta pegar o link capturado pelo links.py, senão gera um link de busca
            link = cache_links.get(chave, f"https://br.betano.com/search?q={j['time_casa']}".replace(" ", "%20"))
            
            item = (
                f"⏱️ {j['horario']} | {j['liga']}\n"
                f"🏟️ {j['time_casa']} x {j['time_fora']}\n"
                f"🔶 {j['mercado']} | Odd: {j['odd']}\n"
                f"🌐 [Abrir na Betano]({link})" 
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
    
