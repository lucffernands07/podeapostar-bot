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

    # Ordenar por maior odd para garantir que a Quina e o de 7 peguem os melhores valores
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
            return {
                "tipo": nome,
                "jogos": combinada,
                "total": round(odd_acumulada, 2)
            }
        return None

    # 1. TRIPLA SEGURANÇA (1.30 - 1.40) - 3 jogos
    t1 = buscar_combinada("🎯 TRIPLA SEGURANÇA (1.30 - 1.40)", 1.30, 1.40, mercados_validos, 3)
    if t1: bilhetes_finais.append(t1)

    # 2. TRIPLA VALOR (ACIMA DE 1.40) - 3 jogos
    t2 = buscar_combinada("🔥 TRIPLA VALOR (ACIMA 1.40)", 1.41, 2.50, mercados_validos, 3)
    if t2: bilhetes_finais.append(t2)

    # 3. A QUINA DAS MELHORES (Melhores Odds que sobraram) - 5 jogos
    # Sem filtro de teto para pegar o que há de melhor
    q1 = buscar_combinada("💰 QUINA DE OURO (5 MELHORES)", 1.20, 5.00, mercados_validos, 5)
    if q1: bilhetes_finais.append(q1)

    # 4. O BILHETE DE 7 (Sorte Grande) - 7 jogos
    s7 = buscar_combinada("🚀 BILHETE DA SORTE (7 JOGOS)", 1.20, 5.00, mercados_validos, 7)
    if s7: bilhetes_finais.append(s7)

    return bilhetes_finais

def formatar_para_telegram(bilhetes):
    if not bilhetes:
        return "⚠️ Não foi possível montar os bilhetes com as odds extraídas."
        
    mensagem = ""
    for b in bilhetes:
        mensagem += f"*{b['tipo']}*\n"
        for j in b['jogos']:
            termo_busca = f"{j['time_casa']} x {j['time_fora']} Betano".replace(" ", "+")
            link_google = f"https://www.google.com/search?q={termo_busca}"
            
            mensagem += f"⏱️ {j['horario']} | {j['time_casa']} x {j['time_fora']}\n"
            mensagem += f"🔶 {j['mercado']} | Odd: {j['odd']}\n"
            mensagem += f"🌐 [Abrir na Betano]({link_google})\n\n"
            
        mensagem += f"📈 *Odd Total: {b['total']}*\n"
        mensagem += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    return mensagem
