def montar_bilhetes_estrategicos(lista_jogos):
    """
    Monta os bilhetes por quantidade (Tripla, Quina e Sete) misturando os mercados.
    """
    bilhetes = []
    if not lista_jogos:
        return bilhetes

    # 1. TRIPLA (3 Jogos) - Preferência por Odds de 1.30 a 1.40
    jogos_tripla = []
    for j in lista_jogos:
        try:
            odd_val = float(j['odd'].replace(',', '.'))
            if 1.30 <= odd_val <= 1.45:
                jogos_tripla.append(j)
            if len(jogos_tripla) == 3: break
        except: continue

    if len(jogos_tripla) == 3:
        bilhetes.append({"nome": "BINGO - TRIPLA (3 JOGOS) 🎯", "jogos": jogos_tripla})

    # 2. QUINA (5 Jogos) - Preferência por Odds acima de 1.40
    jogos_quina = []
    for j in lista_jogos:
        try:
            odd_val = float(j['odd'].replace(',', '.'))
            if odd_val >= 1.40:
                jogos_quina.append(j)
            if len(jogos_quina) == 5: break
        except: continue

    if len(jogos_quina) == 5:
        bilhetes.append({"nome": "BINGO - QUINA (5 JOGOS) 💰", "jogos": jogos_quina})

    # 3. SETE (7 Jogos) - Melhores mercados da lista (Top 7)
    if len(lista_jogos) >= 7:
        bilhetes.append({"nome": "BINGO - SETE (7 JOGOS) 🍀", "jogos": lista_jogos[:7]})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    """
    Transforma a lista de bilhetes em texto formatado para o Telegram.
    """
    texto_final = ""
    for b in bilhetes:
        texto_final += f"🏆 *{b['nome']}*\n"
        odd_total = 1.0
        for j in b['jogos']:
            chave = f"{j['time_casa']}x{j['time_fora']}"
            link = cache_links.get(chave, "#")
            texto_final += f"📍 [{j['time_casa']} x {j['time_fora']}]({link})\n"
            texto_final += f"👉 {j['mercado']} | Odd: {j['odd']}\n"
            try:
                odd_total *= float(j['odd'].replace(',', '.'))
            except: pass
        texto_final += f"💰 *Odd Acumulada: {odd_total:.2f}*\n"
        texto_final += "\n------------------------------------\n\n"
    return texto_final
    
