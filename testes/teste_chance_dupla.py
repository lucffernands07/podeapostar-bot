def verificar_chance_dupla(s):
    sugestoes = []
    
    # 1. MOMENTO ATUAL: Último jogo individual de cada time
    casa_ult = s.get("casa_ult_res", "") # V, E ou D
    fora_ult = s.get("fora_ult_res", "") # V, E ou D
    
    # 2. CONFRONTO DIRETO (H2H): Pegamos os dados do H2H
    # Para garantir a regra de "não perdeu os últimos 2", 
    # olhamos se o oponente tem vitórias registradas no bloco H2H.
    h2h_derrotas_casa = s.get("h2h_vitorias_t2", 0)
    h2h_derrotas_fora = s.get("h2h_vitorias_t1", 0)

    # --- LÓGICA 1X ---
    # Passo 1: Casa venceu a última E Fora perdeu a última
    if casa_ult == "V" and fora_ult == "D":
        # Passo 2: Nos últimos confrontos H2H, a Casa não pode ter perdido (vitórias do T2 = 0)
        # Nota: Como o robô raspa os últimos 5/6, se h2h_vitorias_t2 for 0, 
        # significa que não houve derrota nos últimos 5 (o que inclui os últimos 2).
        if h2h_derrotas_casa == 0:
            # Definição da Porcentagem baseada no volume de vitórias
            if s.get("h2h_vitorias_t1", 0) >= 2:
                pct = "85%"
            else:
                pct = "70%"
            sugestoes.append(f"1X 🔥 ({pct})")

    # --- LÓGICA 2X ---
    # Passo 1: Fora venceu a última E Casa perdeu a última
    if fora_ult == "V" and casa_ult == "D":
        # Passo 2: Nos últimos confrontos H2H, o Fora não pode ter perdido (vitórias do T1 = 0)
        if h2h_derrotas_fora == 0:
            if s.get("h2h_vitorias_t2", 0) >= 2:
                pct = "85%"
            else:
                pct = "70%"
            sugestoes.append(f"2X 🔥 ({pct})")

    return sugestoes
    
