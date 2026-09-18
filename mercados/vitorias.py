"""
REGRAS DE MERCADO - VITÓRIAS (CASA / FORA)
- Vitória Casa: Casa mínimo 4/5 vitórias E fora 4/5 derrotas.
- Vitória Fora: Fora mínimo 4/5 vitórias E casa 4/5 derrotas.
- Trava de Descarte Mútuo: Se ambos passarem, o jogo é descartado.
"""

def contar_resultados(lista_resultados, tipo_alvo):
    if not isinstance(lista_resultados, list):
        return 0
    count = 0
    for r in lista_resultados:
        res = str(r).strip().upper()
        if res == tipo_alvo:
            count += 1
    return count

def verificar_vitorias(s):
    mercados_aprovados = []
    if not isinstance(s, dict):
        return mercados_aprovados

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

    # Fallback automático pelos gols caso o texto do resultado não venha preenchido
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

    # Regras de Vitórias Secas:
    # Vitória Casa: Casa mínimo 4/5 vitórias E fora 4/5 derrotas
    condicao_vitoria_casa = (vitorias_mandante >= 4) and (derrotas_visitante >= 4)
    
    # Vitória Fora: Fora mínimo 4/5 vitórias E casa 4/5 derrotas
    condicao_vitoria_fora = (vitorias_visitante >= 4) and (derrotas_mandante >= 4)

    # Trava de Descarte Mútuo
    if condicao_vitoria_casa and condicao_vitoria_fora:
        print(f"      ⚠️ CONFLITO DE VITÓRIAS: Vitória Casa e Fora passaram juntas. Jogo descartado.")
        return []

    if condicao_vitoria_casa:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Casa", 
            "tipo": "VITORIA_CASA"
        })
    
    if condicao_vitoria_fora:
        mercados_aprovados.append({
            "mercado": "Resultado Final: Vitória Fora", 
            "tipo": "VITORIA_FORA"
        })

    return mercados_aprovados
 
