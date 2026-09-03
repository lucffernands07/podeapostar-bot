"""
REGRAS DE GOLS - COM REGRA DE 0x0 FORÇANDO PARA +0.5
- Over: Mínimo 4/5 (>= 80%), apenas o maior (+2.5 -> +1.5 -> +0.5)
- Regra de Exceção 0x0: Se o último jogo do mandante em casa ou visitante fora for 0x0, +1.5 ou +2.5 vira +0.5
- Under: Mínimo 4/5 (>= 80%), apenas o menor (-3.5 -> -4.5 -> -5.5)
- Regra de Ouro: Ou Over, ou Under (prioridade para Over)
"""

def calcular_porcentagem_gols(c, f):
    try:
        c, f = int(c), int(f)
    except:
        return 0

    if c < 2 or f < 2:
        return 0

    if c == 5 and f == 5:
        return 100
    elif c >= 4 and f >= 4:
        return 80
    elif c >= 3 and f >= 3:
        return 60
    else:
        return 40


def verificar_gols(s):
    if not isinstance(s, dict):
        return []

    c_15 = int(s.get("casa_15", 0) or 0)
    f_15 = int(s.get("fora_15", 0) or 0)
    
    if c_15 < 2 or f_15 < 2:
        return []

    # 1. Leitura direta das porcentagens dos 5 jogos (mínimo 4/5 = 80%)
    pct_05 = calcular_porcentagem_gols(s.get("casa_05", 0), s.get("fora_05", 0))
    pct_15 = calcular_porcentagem_gols(c_15, f_15)
    pct_25 = calcular_porcentagem_gols(s.get("casa_25", 0), s.get("fora_25", 0))
    
    pct_m35 = calcular_porcentagem_gols(s.get("casa_35_under", 0), s.get("fora_35_under", 0))
    pct_m45 = calcular_porcentagem_gols(s.get("casa_45_under", 0), s.get("fora_45_under", 0))
    pct_m55 = calcular_porcentagem_gols(s.get("casa_55_under", 0), s.get("fora_55_under", 0))

    # Captura dos resultados do último jogo para checar o 0x0
    res_t1 = str(s.s.get("t1_resultado_1", "")).upper() if hasattr(s, "get") else "" # Compatibilidade de chaves
    # Como os dicionários costumam trazer o placar ou o resultado textual, vamos verificar 
    # as chaves comuns de placar do último jogo se houver (ex: 'casa_ultimo_placar' ou similar, 
    # ou ajustamos para ler a string do resultado/placar exato que vem no seu dicionário).
    
    # Buscando o placar ou texto do último jogo nas chaves padrão do dicionário:
    # (Caso seu dicionário traga o placar em formato texto tipo "0-0" ou "0x0 nos campos de resultado")
    placar_casa_ult = str(s.get("t1_placar_1", "")).replace(" ", "")
    placar_fora_ult = str(s.get("t2_placar_1", "")).replace(" ", "")
    
    teve_zero_a_zero = ("0-0" in placar_casa_ult or "0x0" in placar_casa_ult or 
                        "0-0" in placar_fora_ult or "0x0" in placar_fora_ult)

    # Alternativa caso o 0x0 venha nos gols marcados/sofridos do último jogo (ex: 0 e 0):
    gols_c_ult = s.get("t1_gols_favor_1")
    gols_f_ult = s.get("t2_gols_favor_1")
    if (gols_c_ult == 0 and s.get("t1_gols_contra_1") == 0) or (gols_f_ult == 0 and s.get("t2_gols_contra_1") == 0):
        teve_zero_a_zero = True

    overs_aprovados = []
    unders_aprovados = []

    # ==========================================================
    # AVALIAÇÃO DE OVERS (Apenas critério estatístico >= 80%)
    # ==========================================================
    if pct_25 >= 80:  
        overs_aprovados.append({"mercado": f"+2.5 Gols ({pct_25}%)", "tipo": "GOLS_25"})
    if pct_15 >= 80:
        overs_aprovados.append({"mercado": f"+1.5 Gols ({pct_15}%)", "tipo": "GOLS_15"})
    if pct_05 >= 80:  
        overs_aprovados.append({"mercado": f"+0.5 Gols ({pct_05}%)", "tipo": "GOLS_05"})

    # ==========================================================
    # AVALIAÇÃO DE UNDERS (Apenas critério estatístico >= 80%)
    # ==========================================================
    if pct_m35 >= 80:
        unders_aprovados.append({"mercado": f"-3.5 Gols ({pct_m35}%)", "tipo": "GOLS_M35"})
    if pct_m45 >= 80:
        unders_aprovados.append({"mercado": f"-4.5 Gols ({pct_m45}%)", "tipo": "GOLS_M45"})
    if pct_m55 >= 80:
        unders_aprovados.append({"mercado": f"-5.5 Gols ({pct_m55}%)", "tipo": "GOLS_M55"})

    # ==========================================================
    # APLICAÇÃO DAS REGRAS DE SELEÇÃO E CONVERSÃO DO 0x0
    # ==========================================================
    
    if overs_aprovados:
        # Pega o maior over inicialmente (o primeiro da lista)
        escolha = overs_aprovados[0]
        
        # REGRA DO 0x0: Se deu +1.5 ou +2.5 e teve 0x0 no último jogo, rebaixa para +0.5 (se o 0.5 for válido >= 80%)
        if teve_zero_a_zero and escolha["tipo"] in ["GOLS_15", "GOLS_25"]:
            # Procura se o +0.5 está disponível nos aprovados
            over_05 = next((item for item in overs_aprovados if item["tipo"] == "GOLS_05"), None)
            if over_05:
                escolha = over_05 # Transforma em +0.5 com segurança!
                
        return [escolha]
    
    elif unders_aprovados:
        # Se não tem over mas tem under, pega o menor (-3.5 > -4.5 > -5.5)
        return [unders_aprovados[0]]
    
    return []
                                 
