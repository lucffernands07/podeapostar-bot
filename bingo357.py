def montar_bilhetes_estrategicos(lista_jogos):
    """
    Agrupa os jogos filtrados em bilhetes temáticos.
    """
    bilhetes = []
    
    # Separadores por categoria
    jogos_seguranca = []  # 1X, 2X, Vitória Casa e -4.5 Gols
    jogos_gols = []       # +1.5 e +2.5 Gols
    jogos_btts = []       # Ambas Marcam
    
    for jogo in lista_jogos:
        m = jogo['mercado']
        
        # --- AJUSTE: Adicionando Vitória Casa na categoria de Segurança ---
        if "Vitória Casa" in m or "1X" in m or "2X" in m or "-4.5" in m:
            jogos_seguranca.append(jogo)
            
        elif "Ambas" in m:
            jogos_btts.append(jogo)
            
        elif "+1.5" in m or "+2.5" in m:
            jogos_gols.append(jogo)

    # 1. Montagem do BILHETE DE SEGURANÇA 🛡️
    # Agrupa de 2 em 2 ou 3 em 3 para manter a odd entre 1.80 e 2.50
    for i in range(0, len(jogos_seguranca), 3):
        grupo = jogos_seguranca[i:i+3]
        if len(grupo) >= 2:
            bilhetes.append({
                "nome": "BILHETE DE SEGURANÇA 🛡️",
                "jogos": grupo
            })

    # 2. Montagem do BILHETE DE GOLS ⚽
    for i in range(0, len(jogos_gols), 3):
        grupo = jogos_gols[i:i+3]
        if len(grupo) >= 2:
            bilhetes.append({
                "nome": "BILHETE DE GOLS ⚽",
                "jogos": grupo
            })

    # 3. Montagem do BILHETE AMBAS MARCAM 🔥
    for i in range(0, len(jogos_btts), 2):
        grupo = jogos_btts[i:i+2]
        if len(grupo) >= 2:
            bilhetes.append({
                "nome": "BILHETE AMBAS MARCAM 🔥",
                "jogos": grupo
            })

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
            
            # Formatação de cada linha do bilhete
            texto_final += f"📍 [{j['time_casa']} x {j['time_fora']}]({link})\n"
            texto_final += f"👉 {j['mercado']} | Odd: {j['odd']}\n"
            
            # Cálculo da Odd acumulada (opcional para exibição)
            try:
                odd_total *= float(j['odd'].replace(',', '.'))
            except:
                pass
        
        texto_final += f"💰 *Odd Total: {odd_total:.2f}*\n"
        texto_final += "\n------------------------------------\n\n"
        
    return texto_final
    
