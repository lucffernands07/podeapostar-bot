def montar_bilhetes_estrategicos(lista_jogos):
    """
    Monta os bilhetes por estratégia: Tripla Segurança, Tripla Valor e Quina de Ouro.
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

    # 3. QUINA DE OURO (5 Jogos) - Os 5 melhores da lista geral
    if len(lista_jogos) >= 5:
        bilhetes.append({"id": "QUINA", "nome": "💰 QUINA DE OURO (5 MELHORES)", "jogos": lista_jogos[:5]})

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
            # Pega o link real do cache ou manda para a busca da Betano como fallback
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

        # Junta os jogos do bilhete
        corpo += "\n\n".join(jogos_texto)
        corpo += f"\n\n📈 Odd Total: {odd_acumulada:.2f}\n"
        corpo += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)

    return "\n\n".join(blocos)
    
