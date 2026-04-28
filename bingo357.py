def montar_bilhetes_estrategicos(lista_jogos):
    """
    Monta os bilhetes por estratégia: Tripla Segurança, Tripla Valor, Quina de Ouro 
    e o novo Bingo de 7 (Odds mais baixas).
    """
    bilhetes = []
    if not lista_jogos:
        return bilhetes

    # 1. TRIPLA SEGURANÇA (3 Jogos) - Odds entre 1.25 e 1.40
    jogos_seguranca = []
    for j in lista_jogos:
        try:
            odd_val = float(j['odd'].replace(',', '.'))
            if 1.25 <= odd_val <= 1.40:
                jogos_seguranca.append(j)
            if len(jogos_seguranca) == 3: break
        except: continue
    
    if len(jogos_seguranca) == 3:
        bilhetes.append({"id": "SEG", "nome": "🎯 TRIPLA SEGURANÇA (1.25 - 1.40)", "jogos": jogos_seguranca})

    # 2. TRIPLA VALOR (3 Jogos) - Odds acima de 1.40
    jogos_valor = []
    for j in lista_jogos:
        try:
            odd_val = float(j['odd'].replace(',', '.'))
            if odd_val > 1.40:
                jogos_valor.append(j)
            if len(jogos_valor) == 3: break
        except: continue
    
    if len(jogos_valor) == 3:
        bilhetes.append({"id": "VALOR", "nome": "🔥 TRIPLA VALOR (ACIMA 1.40)", "jogos": jogos_valor})

    # 3. QUINA DE OURO (5 Jogos) - Os 5 primeiros da lista original (mais recentes/topo)
    if len(lista_jogos) >= 5:
        bilhetes.append({"id": "QUINA", "nome": "💰 QUINA DE OURO (5 MELHORES)", "jogos": lista_jogos[:5]})

    # 4. BINGO DE 7 (Odds mais baixas da lista geral)
    if len(lista_jogos) >= 7:
        # Ordena a lista geral por Odd (da menor para a maior) e pega as 7 primeiras
        lista_ordenada_por_odd = sorted(
            lista_jogos, 
            key=lambda x: float(x['odd'].replace(',', '.'))
        )
        jogos_bingo_7 = lista_ordenada_por_odd[:7]
        bilhetes.append({"id": "BINGO7", "nome": "🍀 SETE DA SORTE (MAIOR PROBABILIDADE)", "jogos": jogos_bingo_7})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    """
    Transforma a lista de bilhetes no layout profissional com links e separadores.
    """
    if not bilhetes:
        return ""

    blocos = []
    for b in bilhetes:
        corpo = f"{b['nome']}\n"
        jogos_texto = []
        odd_acumulada = 1.0

        for j in b['jogos']:
            chave = f"{j['time_casa']}x{j['time_fora']}"
            # Melhorei o fallback do link para substituir espaços por + para a busca da Betano
            link = cache_links.get(chave, f"https://br.betano.com/search?q={j['time_casa']}".replace(" ", "%20"))
            
            item = (
                f"⏱️ {j['horario']} | {j['liga']}\n"
                f"🏟️ {j['time_casa']} x {j['time_fora']}\n"
                f"🔶 {j['mercado']} | Odd: {j['odd']}\n"
                f"🌐 [Abrir na Betano]({link})"
            )
            jogos_texto.append(item)
            
            try:
                odd_acumulada *= float(j['odd'].replace(',', '.'))
            except: pass

        corpo += "\n\n".join(jogos_texto)
        corpo += f"\n\n📈 Odd Total: {odd_acumulada:.2f}\n"
        corpo += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)

    return "\n\n".join(blocos)
    
