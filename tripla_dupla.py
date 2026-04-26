def montar_bilhetes_estrategicos(lista_mercados):
    mercados_validos = []
    for m in lista_mercados:
        try:
            odd_str = str(m.get('odd', '0')).replace(',', '.')
            m['odd_val'] = float(odd_str)
            if m['odd_val'] > 1.0:
                mercados_validos.append(m)
        except ValueError:
            continue

    # Ordenamos a fonte por maior ODD para priorizar valor na escolha
    mercados_validos.sort(key=lambda x: x['odd_val'], reverse=True)

    bilhetes_finais = []
    jogos_globais_usados = set()

    def buscar_combinada(nome, filtro_min, filtro_max, lista_fonte, quantidade):
        combinada = []
        odd_acumulada = 1.0
        
        candidatos = [
            m for m in lista_fonte 
            if filtro_min <= m['odd_val'] <= filtro_max 
            and f"{m['horario']}_{m['time_casa']}" not in jogos_globais_usados
        ]
        
        for m in candidatos:
            if len(combinada) < quantidade:
                combinada.append(m)
                odd_acumulada *= m['odd_val']
                jogos_globais_usados.add(f"{m['horario']}_{m['time_casa']}")
        
        if len(combinada) == quantidade:
            # ORGANIZAÇÃO: Horário primeiro, depois Liga
            combinada.sort(key=lambda x: (x['horario'], x['liga']))
            return {
                "tipo": nome,
                "jogos": combinada,
                "total": round(odd_acumulada, 2)
            }
        return None

    # Montagem seguindo a nova hierarquia
    t1 = buscar_combinada("🎯 TRIPLA SEGURANÇA (1.30 - 1.40)", 1.30, 1.40, mercados_validos, 3)
    if t1: bilhetes_finais.append(t1)

    t2 = buscar_combinada("🔥 TRIPLA VALOR (ACIMA 1.40)", 1.41, 2.50, mercados_validos, 3)
    if t2: bilhetes_finais.append(t2)

    q1 = buscar_combinada("💰 QUINA DE OURO (5 MELHORES)", 1.20, 5.00, mercados_validos, 5)
    if q1: bilhetes_finais.append(q1)

    s7 = buscar_combinada("🚀 BILHETE DA SORTE (7 JOGOS)", 1.20, 5.00, mercados_validos, 7)
    if s7: bilhetes_finais.append(s7)

    return bilhetes_finais

def formatar_para_telegram(bilhetes):
    if not bilhetes:
        return "⚠️ Não foi possível montar os bilhetes estratégicos."
        
    mensagem = ""
    for b in bilhetes:
        mensagem += f"*{b['tipo']}*\n"
        for j in b['jogos']:
            termo_busca = f"{j['time_casa']} x {j['time_fora']} Betano".replace(" ", "+")
            link_google = f"https://www.google.com/search?q={termo_busca}"
            
            mensagem += f"⏱️ {j['horario']} | {j['liga']}\n" # Adicionei a liga aqui também
            mensagem += f"🏟️ {j['time_casa']} x {j['time_fora']}\n"
            mensagem += f"🔶 {j['mercado']} | Odd: {j['odd']}\n"
            mensagem += f"🌐 [Abrir na Betano]({link_google})\n\n"
            
        mensagem += f"📈 *Odd Total: {b['total']}*\n"
        mensagem += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    return mensagem
    
