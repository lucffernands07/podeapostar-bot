def verificar_chance_dupla(s):
    sugestoes = []
    
    # 1. MOMENTO ATUAL (Último jogo individual de cada time)
    casa_ult = s.get("casa_ult_res", "") 
    fora_ult = s.get("fora_ult_res", "") 
    
    # 2. CONFRONTO DIRETO (Dados coletados apenas dos 2 últimos H2H)
    # Essas chaves vêm do ajuste que fizemos na função do teste_main.py
    derrotas_h2h_casa = s.get("h2h_ult2_derrotas_t1", 0)
    derrotas_h2h_fora = s.get("h2h_ult2_derrotas_t2", 0)

    # --- REGRA 1X (Dupla Chance Casa) ---
    # Requisitos: Casa V ou E / Fora D / Casa não perdeu os últimos 2 H2H
    if (casa_ult == "V" or casa_ult == "E") and fora_ult == "D":
        if derrotas_h2h_casa == 0:
            # Porcentagem baseada no volume de vitórias total para medir dominância
            pct = "85%" if s.get("h2h_vitorias_t1", 0) >= 2 else "70%"
            sugestoes.append(f"1X 🔥 ({pct})")

    # --- REGRA 2X (Dupla Chance Fora) ---
    # Requisitos: Fora V ou E / Casa D / Fora não perdeu os últimos 2 H2H
    if (fora_ult == "V" or fora_ult == "E") and casa_ult == "D":
        if derrotas_h2h_fora == 0:
            # Porcentagem baseada no volume de vitórias total do visitante
            pct = "85%" if s.get("h2h_vitorias_t2", 0) >= 2 else "70%"
            sugestoes.append(f"2X 🔥 ({pct})")

    return sugestoes
