def verificar_btts(s):
    """
    Avalia os últimos 5 jogos do Mandante (em casa) e do Visitante (fora):
    
    1. AMBAS MARCAM SIM:
       - Exige mínimo de 4/5 BTTS para ambos os times.
       - Retorna ["Ambas Marcam: Sim (100%)"] se ambos tiverem 5/5 BTTS.
       - Retorna ["Ambas Marcam: Sim (80%)"] se tiverem 4/5 BTTS.

    2. AMBAS MARCAM NÃO:
       - Exige máximo de 3/5 BTTS para ambos os times.
       - Retorna ["Ambas Marcam: Não (100%)"] se ambos tiverem <= 1/5 BTTS.
       - Retorna ["Ambas Marcam: Não (80%)"] se ambos tiverem <= 3/5 BTTS.
    """
    try:
        # Pega os contadores calculados na nova raspagem H2H (Casa/Fora)
        btts_casa = s.get("casa_btts", 0)
        btts_fora = s.get("fora_btts", 0)

        # -----------------------------------------------------------------
        # 🟢 REGRA 1: AMBAS MARCAM SIM (Mínimo 4/5 para ambos)
        # -----------------------------------------------------------------
        if btts_casa >= 4 and btts_fora >= 4:
            if btts_casa == 5 and btts_fora == 5:
                return ["Ambas Marcam: Sim (100%)"]
            return ["Ambas Marcam: Sim (80%)"]

        # -----------------------------------------------------------------
        # 🔴 REGRA 2: AMBAS MARCAM NÃO (Máximo 3/5 para ambos)
        # -----------------------------------------------------------------
        if btts_casa <= 3 and btts_fora <= 3:
            if btts_casa <= 1 and btts_fora <= 1:
                return ["Ambas Marcam: Não (100%)"]
            return ["Ambas Marcam: Não (80%)"]

        # Fora dos padrões de segurança
        return []

    except Exception as e:
        print(f"      ⚠️ Erro ao processar mercado Ambas Marcam: {e}")
        return []
        
