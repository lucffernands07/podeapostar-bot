def montar_bilhetes_estrategicos(lista_mercados):
    """
    Organiza os mercados minerados em dois bilhetes específicos:
    1. Tripla Estratégica: Odds entre 1.30 e 1.40 (Total min 1.70)
    2. Bilhete de Valor: Dupla ou Tripla (Total min 1.70)
    """
    
    # 1. Limpeza e conversão de tipos
    mercados_validos = []
    for m in lista_mercados:
        try:
            # Garante que a odd seja float, tratando N/A e vírgulas
            odd_str = str(m.get('odd', '0')).replace(',', '.')
            m['odd_val'] = float(odd_str)
            if m['odd_val'] > 1.0:
                mercados_validos.append(m)
        except ValueError:
            continue

    bilhetes_finais = []
    jogos_usados = set() # Para evitar o mesmo jogo no mesmo bilhete

    # --- BILHETE 1: TRIPLA ESTRATÉGICA (1.30 - 1.40) ---
    tripla_est = []
    odd_total_est = 1.0
    
    # Filtra candidatos na sua faixa de confiança
    candidatos_est = [m for m in mercados_validos if 1.30 <= m['odd_val'] <= 1.40]
    
    for m in candidatos_est:
        identificador_jogo = f"{m['horario']}_{m['time_casa']}"
        if len(tripla_est) < 3 and identificador_jogo not in jogos_usados:
            tripla_est.append(m)
            odd_total_est *= m['odd_val']
            jogos_usados.add(identificador_jogo)

    if len(tripla_est) >= 2 and odd_total_est >= 1.70:
        bilhetes_finais.append({
            "tipo": "🎯 TRIPLA ESTRATÉGICA",
            "jogos": tripla_est,
            "total": round(odd_total_est, 2)
        })

    # --- BILHETE 2: BILHETE DE VALOR (DUPLA/TRIPLA MIN 1.70) ---
    bilhete_valor = []
    odd_total_val = 1.0
    # Limpa jogos usados para o segundo bilhete poder repetir o jogo se for outro mercado 
    # (ou mantenha se quiser diversificar 100%)
    jogos_usados_val = set() 

    # Pega o restante dos mercados que tenham odds razoáveis (ex: acima de 1.20)
    restante = [m for m in mercados_validos if m['odd_val'] >= 1.20]
    
    # Ordena por odd maior para tentar bater o 1.70 com menos jogos (Duplas)
    restante.sort(key=lambda x: x['odd_val'], reverse=True)

    for m in restante:
        identificador_jogo = f"{m['horario']}_{m['time_casa']}"
        if odd_total_val < 1.70 and identificador_jogo not in jogos_usados_val:
            bilhete_valor.append(m)
            odd_total_val *= m['odd_val']
            jogos_usados_val.add(identificador_jogo)

    if odd_total_val >= 1.70:
        bilhetes_finais.append({
            "tipo": "🔥 BILHETE DE VALOR",
            "jogos": bilhete_valor,
            "total": round(odd_total_val, 2)
        })

    return bilhetes_finais

def formatar_para_telegram(bilhetes):
    """Transforma os objetos de bilhete em texto pronto para o Telegram"""
    mensagem = ""
    for b in bilhetes:
        mensagem += f"*{b['tipo']}*\n"
        for j in b['jogos']:
            mensagem += f"⏱️ {j['horario']} | {j['time_casa']} x {j['time_fora']}\n"
            mensagem += f"🔶 {j['mercado']} | Odd: {j['odd']}\n\n"
        mensagem += f"📈 *Odd Total: {b['total']}*\n"
        mensagem += "---" * 3 + "\n\n"
    return mensagem
