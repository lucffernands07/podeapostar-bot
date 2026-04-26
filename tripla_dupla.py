def montar_bilhetes_estrategicos(lista_mercados):
    # ... (Mantenha toda a sua função montar_bilhetes_estrategicos igual, ela está perfeita) ...
    mercados_validos = []
    for m in lista_mercados:
        try:
            odd_str = str(m.get('odd', '0')).replace(',', '.')
            m['odd_val'] = float(odd_str)
            if m['odd_val'] > 1.0:
                mercados_validos.append(m)
        except ValueError:
            continue

    bilhetes_finais = []
    jogos_globais_usados = set()

    def buscar_tripla(nome, filtro_min, filtro_max, lista_fonte):
        tripla = []
        odd_acumulada = 1.0
        candidatos = [
            m for m in lista_fonte 
            if filtro_min <= m['odd_val'] <= filtro_max 
            and f"{m['horario']}_{m['time_casa']}" not in jogos_globais_usados
        ]
        for m in candidatos:
            if len(tripla) < 3:
                tripla.append(m)
                odd_acumulada *= m['odd_val']
                jogos_globais_usados.add(f"{m['horario']}_{m['time_casa']}")
        if len(tripla) == 3 and odd_acumulada >= 1.70:
            return {"tipo": nome, "jogos": tripla, "total": round(odd_acumulada, 2)}
        return None

    t1 = buscar_tripla("🎯 TRIPLA 1.30 A 1.40", 1.30, 1.40, mercados_validos)
    if t1: bilhetes_finais.append(t1)
    t2 = buscar_tripla("🔥 TRIPLA ACIMA DE 1.40", 1.41, 2.50, mercados_validos)
    if t2: bilhetes_finais.append(t2)
    t3 = buscar_tripla("🏆 TRIPLA ACIMA DE 1.50", 1.51, 3.50, mercados_validos)
    if t3: bilhetes_finais.append(t3)

    return bilhetes_finais

def formatar_para_telegram(bilhetes):
    if not bilhetes:
        return "⚠️ Não foi possível montar triplas com os critérios selecionados hoje."
        
    mensagem = ""
    for b in bilhetes:
        mensagem += f"*{b['tipo']}*\n"
        for j in b['jogos']:
            # --- CRIAÇÃO DO LINK DE BUSCA ---
            # Removemos caracteres especiais que podem quebrar a URL e trocamos espaços por +
            termo_busca = f"{j['time_casa']} x {j['time_fora']} Betano".replace(" ", "+")
            link_google = f"https://www.google.com/search?q={termo_busca}"
            
            mensagem += f"⏱️ {j['horario']} | {j['time_casa']} x {j['time_fora']}\n"
            mensagem += f"🔶 {j['mercado']} | Odd: {j['odd']}\n"
            # Inserindo o link formatado para o Telegram (Markdown)
            mensagem += f"🌐 [Abrir na Betano]({link_google})\n\n"
            
        mensagem += f"📈 *Odd Total: {b['total']}*\n"
        mensagem += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    return mensagem
