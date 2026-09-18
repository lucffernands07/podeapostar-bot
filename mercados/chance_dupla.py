"""
REGRAS DE MERCADO - CHANCE DUPLA (1X / X2)
- 1X: Casa mínimo 3/5 vitórias E fora 4/5 derrotas.
- X2: Fora mínimo 3/5 vitórias E casa 4/5 derrotas.
- Trava de Descarte Mútuo: Se ambos passarem, o jogo é descartado.
"""

def contar_resultados(lista_resultados, tipo_alvo):
    """
    Conta quantos resultados na lista correspondem ao tipo ('V' para vitória, 'D' para derrota).
    Aceita tanto letras ('V', 'D') quanto cálculo direto por placar se necessário.
    """
    if not isinstance(lista_resultados, list):
        return 0
    count = 0
    for r in lista_resultados:
        res = str(r).strip().upper()
        if res == tipo_alvo:
            count += 1
    return count

def verificar_chance_dupla(s):
    if not isinstance(s, dict):
        return []

    # Extrai os resultados dos últimos 5 jogos (do 1 ao 5)
    # Supondo que a raspagem traga chaves como t1_resultado_1 até t1_resultado_5
    try:
        res_mandante = [
            s.get("t1_resultado_1"), s.get("t1_resultado_2"), 
            s.get("t1_resultado_3"), s.get("t1_resultado_4"), s.get("t1_resultado_5")
        ]
        res_visitante = [
            s.get("t2_resultado_1"), s.get("t2_resultado_2"), 
            s.get("t2_resultado_3"), s.get("t2_resultado_4"), s.get("t2_resultado_5")
        ]
    except:
        return []

    # Se faltar dados nas chaves de texto de resultado, tenta deduzir pelos gols (favor vs contra)
    # Caso os resultados venham vazios, podemos preencher com base nos gols:
    for i in range(1, 6):
        if not res_mandante[i-1]:
            gf = s.get(f"t1_gols_favor_{i}")
            gc = s.get(f"t1_gols_contra_{i}")
            if gf is not None and gc is not None:
                if int(gf) > int(gc): res_mandante[i-1] = "V"
                elif int(gf) < int(gc): res_mandante[i-1] = "D"
                else: res_mandante[i-1] = "E"

        if not res_visitante[i-1]:
            gf = s.get(f"t2_gols_favor_{i}")
            gc = s.get(f"t2_gols_contra_{i}")
            if gf is not None and gc is not None:
                if int(gf) > int(gc): res_visitante[i-1] = "V"
                elif int(gf) < int(gc): res_visitante[i-1] = "D"
                else: res_visitante[i-1] = "E"

    vitorias_mandante = contar_resultados(res_mandante, "V")
    derrotas_mandante = contar_resultados(res_mandante, "D")
    
    vitorias_visitante = contar_resultados(res_visitante, "V")
    derrotas_visitante = contar_resultados(res_visitante, "D")

    # Regras Chance Dupla:
    # 1X: Casa min 3/5 vitórias E fora 4/5 derrotas
    condicao_1x = (vitorias_mandante >= 3) and (derrotas_visitante >= 4)
    
    # X2: Fora min 3/5 vitórias E casa 4/5 derrotas
    condicao_x2 = (vitorias_visitante >= 3) and (derrotas_mandante >= 4)

    # Trava de Descarte Mútuo
    if condicao_1x and condicao_x2:
        print(f"      ⚠️ CONFLITO DE CHANCE DUPLA: 1X e X2 passaram juntos. Jogo descartado.")
        return []

    mercados_aprovados = []
    if condicao_1x:
        mercados_aprovados.append({"mercado": "Dupla Chance: 1X", "tipo": "DC_1X"})
    if condicao_x2:
        mercados_aprovados.append({"mercado": "Dupla Chance: X2", "tipo": "DC_X2"})

    return mercados_aprovados
    
