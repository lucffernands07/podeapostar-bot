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
    """ Prioridade visual: 1. Gols, 2. 1X, 3. Ambas, 4. Vitória, 5. 2X """
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

    # --- BINGO 3: VALOR ---
    if len(lista_jogos) >= 3:
        lista_bingo3 = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)[:3]
        lista_bingo3.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO3", "nome": "🔥 BINGO 3: VALOR", "jogos": lista_bingo3})

    # --- BINGO 5: ESTRUTURADO ---
    if len(lista_jogos) >= 5:
        bingo5_selecao = []
        maiores_odds = sorted(lista_jogos, key=lambda x: extrair_odd(x['odd']), reverse=True)[:3]
        bingo5_selecao.extend(maiores_odds)
        restantes = [j for j in lista_jogos if j not in bingo5_selecao]
        maiores_porcentagens = sorted(restantes, key=lambda x: extrair_porcentagem(x['mercado']), reverse=True)[:2]
        bingo5_selecao.extend(maiores_porcentagens)
        if len(bingo5_selecao) < 5:
            sobra = [j for j in lista_jogos if j not in bingo5_selecao]
            bingo5_selecao.extend(sobra[:(5 - len(bingo5_selecao))])
        bingo5_selecao.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO5", "nome": "💰 BINGO 5: ESTRUTURADO", "jogos": bingo5_selecao[:5]})

    # --- BINGO 7: SEGURANÇA ---
    if len(lista_jogos) >= 7:
        lista_bingo7 = sorted(lista_jogos, key=lambda x: (extrair_porcentagem(x['mercado']) / extrair_odd(x['odd'])), reverse=True)[:7]
        lista_bingo7.sort(key=lambda x: x['horario'])
        bilhetes.append({"id": "BINGO7", "nome": "🍀 BINGO 7: SEGURANÇA", "jogos": lista_bingo7})

    return bilhetes

def formatar_para_telegram(bilhetes, cache_links):
    if not bilhetes: return ""
    blocos = []
    
    for b in bilhetes:
        corpo = f"*{b['nome']}*\n\n"
        odd_total = 1.0
        
        # --- NOVO: Agrupamento de Mercados por Jogo ---
        agrupados = {}
        for j in b['jogos']:
            # Criamos uma chave única baseada no horário e nos times
            chave_jogo = f"{j['horario']}_{j['time_casa']}_{j['time_fora']}"
            
            if chave_jogo not in agrupados:
                agrupados[chave_jogo] = {
                    "horario": j['horario'],
                    "liga": j['liga'],
                    "time_casa": j['time_casa'],
                    "time_fora": j['time_fora'],
                    "mercados": [], # Aqui guardamos as linhas de odd
                    "link": cache_links.get(f"{j['time_casa']}x{j['time_fora']}", "https://www.betano.bet.br/sport/futebol/")
                }
            
            # Adiciona o mercado à lista deste jogo específico
            agrupados[chave_jogo]["mercados"].append({
                "texto": f"🔶 {j['mercado']} | Odd: {j['odd']}",
                "prioridade": prioridade_mercado(j['mercado'])
            })
            
            # A ODD TOTAL continua sendo multiplicada individualmente por cada mercado selecionado
            odd_total *= extrair_odd(j['odd'])

        # --- MONTAGEM DO TEXTO FINAL DOS JOGOS ---
        lista_blocos_jogos = []
        for chave in agrupados:
            dados = agrupados[chave]
            
            # Ordena os mercados dentro do jogo pela prioridade (Gols > 1X > Ambas...)
            dados["mercados"].sort(key=lambda x: x['prioridade'])
            
            linhas_mercados = "\n".join([m['texto'] for m in dados["mercados"]])
            
            link_limpo = dados['link'].replace(" ", "%20").replace("(", "%28").replace(")", "%29").strip()
            
            bloco_jogo = (
                f"⏱️ {dados['horario']} | {dados['liga']}\n"
                f"🏟️ {dados['time_casa']} x {dados['time_fora']}\n"
                f"{linhas_mercados}\n"
                f"🌐 [Abrir na Betano]({link_limpo})"
            )
            lista_blocos_jogos.append(bloco_jogo)

        corpo += "\n\n".join(lista_blocos_jogos)
        corpo += f"\n\n📈 *Odd Total: {odd_total:.2f}*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        blocos.append(corpo)
    
    return "\n\n".join(blocos)
            
