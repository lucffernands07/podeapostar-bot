def verificar_chance_dupla(s):
    sugestoes = []
    
    # 1. MOMENTO ATUAL: Último jogo individual de cada time
    casa_ult = s.get("casa_ult_res", "") # V, E ou D
    fora_ult = s.get("fora_ult_res", "") # V, E ou D
    
    # 2. CONFRONTO DIRETO (H2H): Dados coletados do histórico direto
    # h2h_vitorias_t2 são vitórias do visitante contra a casa (derrotas da casa)
    # h2h_vitorias_t1 são vitórias da casa contra o visitante (derrotas do fora)
    h2h_derrotas_casa = s.get("h2h_vitorias_t2", 0)
    h2h_derrotas_fora = s.get("h2h_vitorias_t1", 0)

    # --- LÓGICA 1X ---
    # Passo 1: Casa Venceu OU Empatou a última E Fora perdeu a última
    if (casa_ult == "V" or casa_ult == "E") and fora_ult == "D":
        
        # Passo 2: H2H - Casa não pode ter perdido os últimos confrontos diretos
        if h2h_derrotas_casa == 0:
            # Porcentagem: 85% se tiver histórico de vitórias no H2H, 70% se for equilibrado
            if s.get("h2h_vitorias_t1", 0) >= 2:
                pct = "85%"
            else:
                pct = "70%"
            sugestoes.append(f"1X 🔥 ({pct})")

    # --- LÓGICA 2X ---
    # Passo 1: Fora Venceu OU Empatou a última E Casa perdeu a última
    if (fora_ult == "V" or fora_ult == "E") and casa_ult == "D":
        
        # Passo 2: H2H - Fora não pode ter perdido os últimos confrontos diretos
        if h2h_derrotas_fora == 0:
            # Porcentagem: 85% se tiver histórico de vitórias no H2H, 70% se for equilibrado
            if s.get("h2h_vitorias_t2", 0) >= 2:
                pct = "85%"
            else:
                pct = "70%"
            sugestoes.append(f"2X 🔥 ({pct})")

    return sugestoes
    
